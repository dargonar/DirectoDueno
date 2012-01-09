# -*- coding: utf-8 -*-
"""
    Payment module
    ~~~~~~~~
"""
import logging
from datetime import datetime, date, timedelta
from xml.dom import minidom

from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.ext import deferred

from models import RealEstate, Payment, Invoice, UPConfig
from webapp2 import uri_for as url_for, RequestHandler
from dm import ipn_download
from taskqueue import Mapper

from utils import get_or_404, need_auth, BackendHandler

def send_mail(template, re, invoice=None):
  
  params={'action'  : template, 
          'rekey'   : str(re.key())}
  
  if invoice:
    params['invoice'] = str(invoice.key())
    
  taskqueue.add(url='/tsk/email_task', params=params)

def create_transaction_number(the_date, re):
  key = re.key()
  if key.id():
    return '%sI%d' % ( the_date.strftime('%Y%m'), int(key.id()) )
    
  return '%sN%d' % ( the_date.strftime('%Y%m'), int(re.key().name()) )

# Handler para la vuelta de dinero mail
class Cancel(BackendHandler):
  @need_auth(checkpay=False)
  def get(self, **kwargs):
    invoice = self.mine_or_404( kwargs['invoice'] )
    
    self.set_info('Se cancelo el pago para la factura #%s' % invoice.trx_id )
    self.redirect_to('backend/account/status')

class Done(BackendHandler):
  @need_auth(checkpay=False)
  def get(self, **kwargs):
    invoice = self.mine_or_404( kwargs['invoice'] )
    invoice.state = Invoice._PAID
    invoice.save()
    
    self.set_ok('El pago fue realizado con exito para la factura #%s' % invoice.trx_id)
    self.redirect_to('backend/account/status')

class Pending(BackendHandler):
  @need_auth(checkpay=False)
  def get(self, **kwargs):
    invoice = self.mine_or_404( kwargs['invoice'] )
    invoice.state = Invoice._INPROCESS
    invoice.save()

    self.set_ok(u'La factura #%s quedara en estado pendiente hasta que se acredite el pago.<br/>Si desea agilizar la acreditación envienos una copia del ticket de pago a pagos@directodueno.com.' % invoice.trx_id)
    self.redirect_to('backend/account/status')

class InvoicerMapper(Mapper):
  KIND    = RealEstate
  
  def map(self, re):
    
    plan = re.plan
    
    if re.status == RealEstate._TRIAL:
      #logging.error('-----------------entro en trial')
      # Uso el 80% del free_days del Plan?
      delta = datetime.utcnow() - re.created_at
      if delta.days >= int(re.plan.free_days*0.80):
        re.status = RealEstate._TRIAL_END
        send_mail('trial_will_expire', re)
        return ([re], []) # update/delete
      
    elif re.status == RealEstate._TRIAL_END:
      #logging.error('---------------entro en trial end')
      # Llegamos a los free_days del Plan y todavia no pago?
      delta = datetime.utcnow() - re.created_at
      if delta.days >= re.plan.free_days:
        re.status = RealEstate._NO_PAYMENT
        send_mail('trial_ended', re)
        return ([re], []) # update/delete
    
    elif re.status == RealEstate._ENABLED and not re.plan.is_free:

      #logging.error('-----------------------entro en ENABLED')
      
      # Today
      today = datetime.utcnow().date()
      
      next_month = re.last_invoice.month + 1
      next_year  = re.last_invoice.year
      
      if next_month == 13:
        next_month = 1
        next_year  = next_year + 1
      
      next_date = date(next_year, next_month, re.last_invoice.day)

      #logging.error('--------------next date ' + str(next_date) )
      #logging.error('--------------today ' + str(today) )

      invoice = None
      if today > next_date:
        invoice = Invoice()
        invoice.realestate = re
        invoice.trx_id     = create_transaction_number(next_date, re)
        invoice.amount     = re.plan.amount
        invoice.state      = Invoice._NOT_PAID
        invoice.date       = next_date
        invoice.put()
        
        re.last_invoice = next_date
        
      # Contamos las facturas impagas, si son mas que dos, ponemos en disabled
      # Si son menos que dos y le acabo de facturar, le envio la factura
      not_paid_invoices = len(Invoice().all(keys_only=True).filter('realestate', re.key()).filter('state', Invoice._NOT_PAID).fetch(10))
      #logging.error('----------- Lleva %d sin pagar' % not_paid_invoices)
      
      if not_paid_invoices > 2:
        re.status = RealEstate._NO_PAYMENT
        send_mail('no_payment', re)
        # TODO: mandar a deshablitiar?
        return ([re], [])
      
      elif invoice:
        send_mail('new_invoice', re, invoice)
        return ([re], [])
    
    return ([], []) # update/delete
    
class RunInvoicer(BackendHandler):
  def get(self, **kwargs):
    # Mandamos a correr la tarea de mapeo
    tmp = InvoicerMapper()
    deferred.defer(tmp.run)
    self.response.write('invoice mapper corriendo')

    
class PaymentAssingMapper(Mapper):
  KIND    = Payment
  FILTERS = [('assigned',0)]

  def map(self, payment):
    
    # Traemos la factura que este pago cancela el pago (payment)
    invoice = Invoice.all().filter('trx_id', payment.trx_id).get()
    if not invoice:
      logging.error('No encontre factura para el pago %s' % str(payment.key()))
      return ([],[])
    
    # Obtenemos el realestate en funcion del trx_id
    id_or_name = payment.trx_id[7:] #YYYYMM[NI]ddddddd
    
    re = None
    if payment.trx_id[6] == 'I':
      re = RealEstate.get_by_id(int(id_or_name))
    else:
      re = RealEstate.get_by_key_name(id_or_name)
    
    if re is None:
      logging.error('No encontre el realestate para %s' % payment.trx_id)
      return ([],[])
    
    invoice.realestate = re
    
    # Ponemos la factura en estado pagada
    invoice.state   = Invoice._PAID
    invoice.payment = payment
    invoice.save()
    
    # Acabamos de asignar un pago, deberiamos automaticamente 
    # poner en ENABLED a la inmo si es que no estaba en ese estado
    # Si esta volviendo a ENABLE desde NO_PAYMENT debemos comunicarle que 'las props estan publicadas nuevamente'
    
    oldst = re.status

    # payment_received
    if re.status == RealEstate._ENABLED:
      send_mail('payment_received', re)
    else:
      re.status = RealEstate._ENABLED
      re.save()

      if oldst == RealEstate._NO_PAYMENT:
        send_mail('enabled_again', re, invoice)
    
    payment.assigned = 1      
    return ([payment], []) # update/delete

# Handler para guardar el IPN
class UpdateIPN(RequestHandler):
  def post(self, **kwargs):
    self.request.charset = 'utf-8'
    tmp     = self.request.POST.get('date')
    account = self.request.POST.get('account')
    
    upcfg = UPConfig.get_or_insert('main-config')
    
    if account == 'emi':
      upcfg.last_ipn_emi = date(int(tmp[0:4]), int(tmp[4:6]), int(tmp[6:8]))
    else:
      upcfg.last_ipn = date(int(tmp[0:4]), int(tmp[4:6]), int(tmp[6:8]))
      
    upcfg.save()
    
    self.response.write('ok')

# XML Helper
def get_xml_value(parent, name):
  firstChild = parent.getElementsByTagName(name)[0].firstChild
  return firstChild.nodeValue if firstChild else ''

class Download(RequestHandler):
  def get(self, **kwargs):
    self.request.charset  = 'utf-8'
    
    account = kwargs['account']
    
    # Nos fijamos la ultima vez que lo pedimos, pedimos hasta hoy si estamos dentro de un mes max
    # Sino bajaremos en dos dias (probabilidad muy baja)
    upcfg = UPConfig.get_or_insert('main-config', last_ipn=datetime.now().date(), last_ipn_emi=datetime.now().date() )

    _from = upcfg.last_ipn
    if account == 'emi':
      _from = upcfg.last_ipn_emi
      
    _to = datetime.utcnow().date()

    if (_to - _from).days > 28:
      _to = _from + timedelta(days=28)
    
    # Bajamos el xml con la api de IPN
    dom = minidom.parseString(ipn_download(account, _from, _to))
    
    # Verificamos que este todo bien el xml de vuelta
    state = int(get_xml_value(dom, 'State'))
    if state != 1:
      logging.error('Error al traer xml: %d [%s]' % (state,account) )
      self.response.write('ok')
      return

    #logging.error('----------traje joya')
      
    # Parseamos y generamos los Payment
    to_save = []
    for pay in dom.getElementsByTagName('Pay'):
      
      p = Payment()
      p.trx_id  = pay.attributes['trx_id']
      
      # Rompemos la fecha (la esperamos en formato YYYYMMDD)
      tmp = get_xml_value(pay,'Trx_Date')
      p.date = date(int(tmp[0:4]),int(tmp[4:6]),int(tmp[6:8]))
      
      # El monto lo ponemos en int por 10
      p.amount = int(float(get_xml_value(pay,'Trx_Payment'))*10)
      p.assinged = 0
      
      to_save.append(p)
    
    # Cuantos pagos recibimos?
    logging.info('Se recibieron %d pagos [%s]' % ( len(to_save), account ) )
      
    # Salvamos todos los payments juntos y la ultima vez que corrimos en una transaccion
    def txn():
      if(len(to_save)):
        db.put(to_save)
        
        tmp = PaymentAssingMapper()
        deferred.defer(tmp.run, _transactional=True)
      
      taskqueue.add(url='/tsk/update_ipn/%s' % account, params={'date': _to.strftime('%Y%m%d'), 'account':account}, transactional=True)
    
    db.run_in_transaction(txn)
    
    # Mandamos a correr la tarea de mapeo de pagos si bajamos alguno nuevo
    self.response.write('ok')
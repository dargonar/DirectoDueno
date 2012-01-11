# -*- coding: utf-8 -*-
import logging
from google.appengine.ext import db
from google.appengine.api import mail
from datetime import datetime, timedelta

from webapp2 import abort, get_app, uri_for as url_for

from models import Property, Consulta, Invoice

from utils import get_bitly_url, MyBaseHandler, get_property_slug

class SendTask(MyBaseHandler):
  
  # def get(self, **kwargs):
    # self.request.charset = 'utf-8'
    
    # # TODO: Security hazard (think)
    # params = self.request.GET.mixed()
    # action = self.request.GET.get('action')
    # getattr(self, action)(params)
    # # params: { rekey, invoice=None }
    # return
  
  def post(self, **kwargs):
    self.request.charset = 'utf-8'
    
    # TODO: Security hazard (think)
    params = self.request.POST.mixed()
    action = self.request.POST.get('action')
    getattr(self, action)(params)
    # params: { rekey, invoice=None }
    return

  def directodueno_campaign(self, params):
    mail_to = params['email']
    context = { 'server_url':                 'http://www.directodueno.com'
              , 'support_url' :               'http://www.directodueno.com/admin/login'}
    context['mail_to'] = mail_to
    # Armo el body en plain text.
    body = self.render_template('email/campaign_start_v1.txt', **context)  
    # Armo el body en HTML.
    html = self.render_template('email/campaign_start_v1.html', **context)  
    
    # Envío el correo.
    mail.send_mail(sender="www.directodueno.com <info@directodueno.com>", 
                 to       = mail_to,
                 subject  = u"DirectoDueño: donde vendés y alquilás sin intermediarios.",
                 body     = body,
                 html     = html)
    # --------------------------------------------------------------------------------
    
  def common_context(self):
    context = { 'server_url':                 'http://'+self.request.headers.get('host', 'no host')
              , 'support_url' :               'http://'+self.request.headers.get('host', 'no host')}
    return context
    
  def send_email(self, template, mail_to, subject, **context):
    
    data = self.config['directodueno']['mail'][template]  
    
    # Armo el body en plain text.
    body = self.render_template('email/'+data['template']+'.txt', **context)  
    # Armo el body en HTML.
    html = self.render_template('email/'+data['template']+'.html', **context)  
    
    # Envío el correo.
    mail.send_mail(sender="www.directodueno.com <%s>" % data['sender'], 
                 to       = mail_to,
                 subject  = u'%s - DirectoDueño' % subject,
                 body     = body,
                 html     = html)
    # --------------------------------------------------------------------------------
      
  def trial_will_expire(self, params):
    re = db.get(params['rekey'])
    expires_at = re.created_at + timedelta(days=re.plan.free_days)
    
    context_ex = self.common_context()
    context_ex = dict({'expire_date':expires_at, 'expire_span':(expires_at-datetime.utcnow()).days}, **context_ex)
    
    self.send_email('trial_will_expire', re.email, u'Su período de prueba en DirectoDueño está a punto de finalizar', **context_ex)
  
  def trial_ended(self, params):
    re = db.get(params['rekey'])
    context_ex = self.common_context()
    
    self.send_email('trial_ended', re.email, u'Su período de prueba en DirectoDueño ha finalizado', **context_ex)

  def no_payment(self, params):
    re = db.get(params['rekey'])
    invoices_count  = len(Invoice().all(keys_only=True).filter('realestate', re.key()).filter('state', Invoice._NOT_PAID).fetch(10))
    plural          = 's' if invoices_count>1 else ''
    
    context_ex = self.common_context()
    context_ex = dict({'invoices_count':invoices_count, 'plural':plural}, **context_ex)
    
    self.send_email('no_payment', re.email, u'Aviso de factura%s impaga%s' % (plural, plural), **context_ex)
  
  def enabled_again(self, params):
    re        = db.get(params['rekey'])
    invoice   = db.get(params['invoice'])
    
    context_ex = self.common_context()
    context_ex = dict({'invoice':invoice}, **context_ex)
    
    self.send_email('enabled_again', re.email, u'Recepción de pago de factura', **context_ex)

  def payment_received(self, params):
    re        = db.get(params['rekey'])
    invoice   = db.get(params['invoice'])
    
    context_ex = self.common_context()
    context_ex = dict({'invoice':invoice}, **context_ex)
    
    self.send_email('payment_received', re.email, u'Recepción de pago de factura', **context_ex)
    
  def new_invoice(self, params):
    re        = db.get(params['rekey'])
    invoice   = db.get(params['invoice'])
    
    context_ex = self.common_context()
    context_ex = dict({'invoice':invoice}, **context_ex)
    
    self.send_email('new_invoice', re.email, u'Nueva factura', **context_ex)
    
  def requestinfo_user(self, params):
    key                   = params['propery_key']
    property              = db.get(key) 
    realestate_key        = params['realestate_key'] 
    realestate            = db.get(realestate_key) 
    
    prop_operation_id     = params['prop_operation_id']
    
    contact_from_map = True
    if 'template_realestate' in params:
      contact_from_map = False
    
    #property_link  = '%s/propiedades.html#%s/%s' % (realestate.website, key, prop_operation_id)
    property_link  = url_for('frontend/ficha', slug=get_property_slug(property), key=key, oper= prop_operation_id, _full=True) 
    

    if contact_from_map:
      str_query                 = params['query_string'] 
      property_link             = get_bitly_url(str_query)
    
    
    # Armo context, lo uso en varios lugares, jaja!
    context = { 'server_url':                 'http://'+self.request.headers.get('host', 'no host')
               ,'realestate_name':            realestate.name
               ,'realestate_website':         realestate.website
               ,'property_link':              property_link
               ,'sender_name':                self.request.POST.get('sender_name')
               ,'sender_email':               self.request.POST.get('sender_email')
               ,'sender_comment':             self.request.POST.get('sender_comment')
               ,'prop_operation_id':          prop_operation_id
              , 'support_url' :               'http://'+self.request.headers.get('host', 'no host')}
    
    # Mando Correo a Usuario.
    # Armo el body en plain text.
    body = self.render_template('email/'+self.config['directodueno']['mail']['requestinfo_user']['template']+'.txt', **context)  
    # Armo el body en HTML.
    html = self.render_template('email/'+self.config['directodueno']['mail']['requestinfo_user']['template']+'.html', **context)  
    
    # Envío el correo.
    mail.send_mail(sender="www.directodueno.com <%s>" % self.config['directodueno']['mail']['requestinfo_user']['sender'], 
                 to       = context['sender_email'],
                 subject  = u"Consulta por un inmueble - DirectoDueño",
                 body     = body,
                 html     = html)
    # --------------------------------------------------------------------------------
      
    self.response.write('ok')
  
  def requestinfo_agent(self, params):  
    key                   = params['propery_key']
    property              = db.get(key) 
    realestate_key        = params['realestate_key'] 
    realestate            = db.get(realestate_key) 
    
    prop_operation_id     = params['prop_operation_id']
    
    contact_from_map = True
    if 'template_realestate' in params:
      contact_from_map = False
    
    # realestate_property_link  = '%s/propiedades.html#%s/%s' % (realestate.website, key, prop_operation_id)
    # realestate_property_link  = url_for('realestate/ficha', realestate=str(realestate.key()), key=key, oper=prop_operation_id,  _full=True) 
    realestate_property_link    = url_for('frontend/ficha', slug=get_property_slug(property), key=key, oper= prop_operation_id, _full=True) 
    
    # if contact_from_map:
      # if realestate.website is None or realestate.website.strip()=='': # Deben tener ptopiedades.html y rever tema #if realestate.managed_domain==1 :
        # str_query                 = params['query_string'] 
        # realestate_property_link  = get_bitly_url(str_query)
    
    # Armo context, lo uso en varios lugares, jaja!
    context = { 'server_url':                 'http://'+self.request.headers.get('host', 'no host')
               ,'realestate_name':            realestate.name
               ,'realestate_website':         realestate.website
               ,'realestate_property_link':   realestate_property_link
               ,'sender_name':                self.request.POST.get('sender_name')
               ,'sender_email':               self.request.POST.get('sender_email')
               ,'sender_comment':             self.request.POST.get('sender_comment')
               ,'sender_telephone':           self.request.POST.get('sender_telephone', None)
               ,'prop_operation_id':          prop_operation_id
              , 'support_url' :               'http://'+self.request.headers.get('host', 'no host')}
    
    # Mando Correo a agente.
    # Armo el body en plain text.
    body = self.render_template('email/'+self.config['directodueno']['mail']['requestinfo_agent']['template']+'.txt', **context)  
    # Armo el body en HTML.
    html = self.render_template('email/'+self.config['directodueno']['mail']['requestinfo_agent']['template']+'.html', **context)  
    
    # Envío el correo.
    mail.send_mail(sender="www.directodueno.com <%s>" % self.config['directodueno']['mail']['requestinfo_agent']['sender'], 
                 to       = realestate.email,
                 bcc      = self.config['directodueno']['mail']['reply_consultas']['mail'],
                 subject  = u'Hicieron una consulta por un inmueble - DirectoDueño',
                 body     = body,
                 html     = html)
    
    self.save_consulta(property, realestate, contact_from_map, **context)
    
    self.response.write('ok')
    
    
  
  def contact_user(self, params):
    realestate_key        = params['realestate_key']
    realestate            = db.get(realestate_key) 
    
    # Armo context, lo uso en varios lugares, jaja!
    context = { 'server_url':                 'http://'+self.request.headers.get('host', 'no host')
               ,'realestate_name':            realestate.name
               ,'realestate_website':         realestate.website
               ,'sender_name':                self.request.POST.get('sender_name')
               ,'sender_email':               self.request.POST.get('sender_email')
               ,'sender_comment':             self.request.POST.get('sender_comment')
               , 'support_url' :               'http://'+self.request.headers.get('host', 'no host')}
    
    # Mando Correo a Usuario.
    # Armo el body en plain text.
    body = self.render_template('email/'+self.config['directodueno']['mail']['contact_user']['template']+'.txt', **context)  
    # Armo el body en HTML.
    html = self.render_template('email/'+self.config['directodueno']['mail']['contact_user']['template']+'.html', **context)  
    
    # Envío el correo.
    mail.send_mail(sender="www.directodueno.com <%s>" % self.config['directodueno']['mail']['contact_user']['sender'], 
                 to       = context['sender_email'],
                 subject  = u"Consulta - DirectoDueño",
                 body     = body,
                 html     = html)
    # --------------------------------------------------------------------------------
      
    self.response.write('ok')
    
  
  def contact_agent(self, params):
    realestate_key        = params['realestate_key']
    realestate            = db.get(realestate_key) 
    
    # Armo context, lo uso en varios lugares, jaja!
    context = { 'server_url':                 'http://'+self.request.headers.get('host', 'no host')
               ,'realestate_name':            realestate.name
               ,'realestate_website':         realestate.website
               ,'sender_name':                self.request.POST.get('sender_name')
               ,'sender_email':               self.request.POST.get('sender_email')
               ,'sender_comment':             self.request.POST.get('sender_comment')
               ,'sender_telephone':           self.request.POST.get('sender_telephone')
               ,'support_url' :               'http://'+self.request.headers.get('host', 'no host')}
    
    # Mando Correo a Usuario.
    # Armo el body en plain text.
    body = self.render_template('email/'+self.config['directodueno']['mail']['contact_agent']['template']+'.txt', **context)  
    # Armo el body en HTML.
    html = self.render_template('email/'+self.config['directodueno']['mail']['contact_agent']['template']+'.html', **context)  
    
    # Envío el correo.
    mail.send_mail(sender="www.directodueno.com <%s>" % self.config['directodueno']['mail']['contact_agent']['sender'], 
                 to       = realestate.email,
                 bcc      = self.config['directodueno']['mail']['reply_consultas']['mail'],
                 subject  = u"Hicieron una consulta - DirectoDueño",
                 body     = body,
                 html     = html)
    
    self.save_consulta(None, realestate, False, **context)
    
    self.response.write('ok')
    
  
  def save_consulta(self, property, realestate, contact_from_ultraprop, **context):
    #logging.debug('save_consulta:: llamada')          
    try:
      consulta                            = Consulta()
      consulta.realestate_name            = context['realestate_name']
      consulta.realestate                 = realestate
      consulta.property                   = property
      
      consulta.realestate_property_link   = ''
      if 'realestate_property_link' in context:
        consulta.realestate_property_link = context['realestate_property_link']
      
      consulta.property_link              = ''
      if 'property_link' in context:
        consulta.property_link            = context['property_link']
        
      consulta.sender_name                = context['sender_name']
      consulta.sender_email               = context['sender_email']
      consulta.sender_comment             = context['sender_comment']
      consulta.sender_telephone           = ''
      if 'sender_telephone' in context:
        consulta.sender_telephone         = context['sender_telephone']
      
      prop_operation_id                   = int(context['prop_operation_id']) if 'prop_operation_id' in context else 0
      consulta.prop_operation_desc = ''
      if prop_operation_id == Property._OPER_SELL:
        consulta.prop_operation_desc = 'Venta'
      if prop_operation_id == Property._OPER_RENT:
        consulta.prop_operation_desc = 'Alquiler'
      
      consulta.is_from_ultraprop          = 1 if contact_from_ultraprop else 0
      consulta.save()
    except Exception, e:
      logging.error('email.py::save_consulta() exception.')
      logging.exception(e)
    return 'ok'
# -*- coding: utf-8 -*-
import logging
import time
from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.api import mail

from webapp2 import abort, get_app, cached_property # uri_for as url_for

from search_helper import config_array, MAX_QUERY_RESULTS
from models import Property, ImageFile

from utils import get_or_404, FrontendHandler, get_bitly_url
from backend_forms import PropertyContactForm

class PopUp(FrontendHandler):
  def get(self, **kwargs):
    
    key                   = kwargs['key']
    bubble_css            = kwargs['bubble_css']
    price_data_operation  = int(kwargs['oper'])
    property              = get_or_404(key)
    
    images = ImageFile.all().filter('property =', db.Key(key)).order('position')
    context = {'images':images, 'property': property, 'Property':Property, 'bubble_css':bubble_css, 'price_data_operation':price_data_operation}
    
    return self.render_response('frontend/templates/_bubble.html', **context)  
    
class Ficha(FrontendHandler):
  def get(self, **kwargs):
    
    key                   = kwargs['key']
    price_data_operation  = kwargs['oper']
    
    property              = get_or_404(key) 
    
    property.visits=property.visits+1
    property.save(build_index=False)
    
    price                 = property.price_sell 
    cur                   = property.price_sell_currency 
    
    if int(price_data_operation) ==  Property._OPER_RENT: 
      price  = property.price_rent  
      cur    = property.price_rent_currency 

    context = { 'property': property
              , 'Property':Property
              , 'price':price
              , 'cur':cur
              , 'config_array':config_array
              , 'price_data_operation':price_data_operation}
    
    
    context_ex = dict({'form':self.form}, **context)
    context_ex = dict({'images': ImageFile.all().filter('property =', db.Key(key)).order('position') }, **context_ex)
    
    ficha = self.render_template('frontend/templates/_ficha.html', **context_ex)  
    tab   = self.render_template('frontend/templates/_prop_tab.html', **context)
    
    return self.render_json_response({'ficha': ficha, 'tab': tab})
  
  @cached_property
  def form(self):
    return PropertyContactForm()
  
  def full_page(self, **kwargs):
    
    key                   = kwargs['key']
    price_data_operation  = kwargs['oper']
    
    property              = get_or_404(key) 
    
    price                 = property.price_sell 
    cur                   = property.price_sell_currency 
    
    if int(price_data_operation) ==  Property._OPER_RENT: 
      price  = property.price_rent  
      cur    = property.price_rent_currency 

    context = { 'property': property
              , 'Property':Property
              , 'price':price
              , 'cur':cur
              , 'config_array':config_array
              , 'price_data_operation':price_data_operation}
    
    
    context_ex = dict({'form':self.form}, **context)
    context_ex = dict({'images': ImageFile.all().filter('property =', db.Key(key)).order('position') }, **context_ex)
    
    
    return self.render_response('frontend/ficha.html', **context_ex)  
  
class Compare(FrontendHandler):
  def get(self, **kwargs):
    
    keys = kwargs['keys']
    oper = int(kwargs['oper'])
    if keys is None or len(keys)<1:
      abort(404)
      
    properties              = get_or_404(kwargs['keys'][:-1].split(',')) 
    
    data = {  #'price':                    {'value':9999999999.9,  'key':'', 'comp':'<'} ,
              'area_indoor':            {'value':0.0,           'key':'', 'comp':'major_than'}
              , 'area_outdoor':         {'value':0.0,           'key':'', 'comp':'major_than'}
              , 'area_total':           {'value':0.0,           'key':'', 'comp':'major_than'}
              , 'rooms':                {'value':0,             'key':'', 'comp':'major_than'}
              , 'bedrooms':             {'value':0,             'key':'', 'comp':'major_than'}
              , 'bathrooms':            {'value':0,             'key':'', 'comp':'major_than'}
              , 'year_built':           {'value':9999999999,    'key':'', 'comp':'minor_than'}
              , 'prop_state_id':        {'value':9999999999,    'key':'', 'comp':'minor_than'}
            }
    if int(oper)==Property._OPER_SELL:
      price_field       = 'price_sell'
      data[price_field] =   {'value':9999999999.9,  'key':'', 'comp':'minor_than'}
    else:
      price_field       = 'price_rent'
      data[price_field] =   {'value':9999999999.9,  'key':'', 'comp':'minor_than'}
   
    images = {}
    for prop in properties:
      images[str(prop.key())] = ImageFile.all().filter('property =', prop.key()).order('position')
      prop.area_total = prop.area_indoor+prop.area_outdoor
      for attr in data.keys():
        prop_attr_value = getattr(prop, attr)
        if getattr(self, data[attr]['comp'])(prop_attr_value, data[attr]['value']):
          #data[attr]['key'] = str(prop.key())
          data[attr]['value'] = prop_attr_value
          
    data['price']           = data[price_field]
    comp_key                = str(time.time()).replace('.', '')
    compare                 = self.render_template('frontend/compare.html'
                                    , properties=properties
                                    , images = images
                                    , data=data
                                    , operation=oper
                                    , price_field=price_field
                                    , config_array=config_array, extra_fields=sorted(config_array['binary_values_properties'], key=config_array['binary_values_properties'].get, reverse=False)
                                    , comp_key=comp_key
                                    , Property=Property)  
    tab                     = self.render_template('frontend/templates/_compare_tab.html', comp_key=comp_key)
    
    return self.render_json_response({'compare': compare, 'tab': tab})
  
  def major_than(self, prop_value, current_value):
    return prop_value>current_value 
  def minor_than(self, prop_value, current_value):
    return prop_value<current_value and prop_value>0
    
class SendMail(FrontendHandler):
  def get(self, **kwargs):
    self.request.charset  = 'utf-8'
    
    key                   = kwargs['key']
    
    if not self.form.validate():
      # responsetxt = [reduce(lambda x, y: str(x)+' '+str(y), t) for t in self.form.errors.values()]
      responsetxt = 'Verifique los datos ingresados:' + '<br/>'.join(reduce(lambda x, y: str(x)+' '+str(y), t) for t in self.form.errors.values())
      self.response.status_int = 500
      self.response.write(responsetxt)
      return
    
    context = { 'propery_key':                key
               ,'realestate_key':             str(db.get(key).realestate.key())
               ,'query_string':               self.request.query_string + '&version=1'       
               ,'sender_name':                self.form.name.data
               ,'sender_email':               self.form.email.data
               ,'sender_comment':             self.form.message.data
               ,'prop_operation_id':          self.request.GET.get('prop_operation_id', default='1')}               
                
    def txn():
      taskqueue.add(url=self.url_for('backend/email_task'), params=dict({'action':'requestinfo_user'}, **context), transactional=True)
      taskqueue.add(url=self.url_for('backend/email_task'), params=dict({'action':'requestinfo_agent'}, **context), transactional=True)
    
    db.run_in_transaction(txn)
    
    self.response.write('Tu consulta fue enviada satisfactoriamente. Te hemos enviado una copia de la consulta a tu correo.')  
    
  @cached_property
  def form(self):
    return PropertyContactForm(self.request.GET)
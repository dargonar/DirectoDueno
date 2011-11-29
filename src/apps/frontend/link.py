# -*- coding: utf-8 -*-
import logging
import urllib


from webapp2 import cached_property, Response
from webapp2_extras.json import json, decode

from google.appengine.api import urlfetch, mail

from search_helper import config_array, MAX_QUERY_RESULTS
from forms import EmailLinkForm
from utils import FrontendHandler, get_bitly_url, expand_bitly_url, get_dict_from_querystring_dict
from utils import get_link_url
from models import Property

# Dummy Handler, por si chequea bit.ly.
class SearchShare(FrontendHandler):
  def get(self, **kwargs):
    return self.redirect_to('frontend/map')

# ============================================================ #
# Share busqueda a través de bitly.  ======================== #

class LoadSearchLink(FrontendHandler):
  def get(self, **kwargs):
    bitly_hash = kwargs.get('bitly_hash', '')
    if len(bitly_hash)<1:
      return redirect('frontend/map')
    
    query_dict = expand_bitly_url(bitly_hash)

    dict = get_dict_from_querystring_dict(query_dict)
    
    return self.render_response('frontend/index.html'
                          , config_arrayJSON=json.dumps(config_array)
                          , config_array=config_array
                          , max_results=MAX_QUERY_RESULTS
                          , preset=dict
                          , presetJSON=json.dumps(dict)
                          , _OPER_SELL=Property._OPER_SELL
                          , _OPER_RENT=Property._OPER_RENT)

class EmailShortenedLink(FrontendHandler):
  def post(self, **kwargs):
    self.request.charset = 'utf-8'
    if self.form.validate():
    
      # ---------------------------------------------------------------- #    
      # Mando Correo para compartir link.     -------------------------- #
      context = {'link':                urllib.unquote(self.form.link.data), 
                 'email_to':            self.form.email.data
               , 'support_url' :        'http://'+self.request.headers.get('host', 'no host') 
               , 'server_url':          'http://'+self.request.headers.get('host', 'no host')}
      # Armo el body en plain text.
      body = self.render_template('email/'+self.config['directodueno']['mail']['share_link']['template']+'.txt', **context)  
      # Armo el body en HTML.
      html = self.render_template('email/'+self.config['directodueno']['mail']['share_link']['template']+'.html', **context)  
      
      # Envío el correo.
      mail.send_mail(sender="www.directodueno.com <%s>" % self.config['directodueno']['mail']['share_link']['sender'], 
                   to=context['email_to'],
                   subject="DirectoDueño - Propiedades",
                   body=body,
                   html=html
                   )
      # ---------------------------------------------------------------- #    
      
      self.response.write('Correo enviado satisfactoriamente.')
      return 
      
    # responsetxt = [reduce(lambda x, y: str(x)+' '+str(y), t) for t in self.form.errors.values()]
    responsetxt = 'Verifique los datos ingresados:' + '<br/>'.join(reduce(lambda x, y: str(x)+' '+str(y), t) for t in self.form.errors.values())
    self.response.status_int = 500
    self.response.write(responsetxt)
  
  @cached_property
  def form(self):
    return EmailLinkForm(self.request.POST)
    
class ShortenLink(FrontendHandler):
  def get(self, **kwargs):
    
    str_query     = self.request.query_string 
    str_query     += '&version=1' 
    
    link_url      = get_bitly_url(str_query)
    
    # Armo URL con 
    return self.render_json_response({ 'bitly':link_url })


# ============================================================ #
# Share busqueda a través de Link local Model Class.  ======== #

class ShortenLocalLink(FrontendHandler):
  def get(self, **kwargs):
    
    str_query     = self.request.query_string 
    str_query     += '&version=2' 
    
    link_url      = get_link_url(str_query)
    
    # Armo URL con 
    return self.render_json_response({ 'bitly':link_url })

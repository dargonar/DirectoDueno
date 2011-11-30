# -*- coding: utf-8 -*-
import logging
import urllib
import cgi

from google.appengine.ext import db
from google.appengine.api import taskqueue
from taskqueue import Mapper
from webapp2 import abort, cached_property, RequestHandler, Response, HTTPException, uri_for as url_for, get_app
from webapp2_extras import jinja2, sessions, json

from myfilters import do_currencyfy, do_statusfy, do_pricefy, do_addressify, do_descriptify, do_headlinify, do_slugify, do_operationfy, do_totalareafy, do_expensasfy, do_add_days, do_ownerify

from models import Link, Property, RealEstate

def get_property_slug(property):
  return do_slugify(do_headlinify(property)+'-'+do_addressify(property))

# ================================================================================ #
# Funciones para manejo de Links: guardar y recuperar busqueda en mapa =========== #
# ================================================================================ #
def get_bitly_url(str_query):
  import urllib2
  url     = url_for('frontend/link/share', _full=True) + '?' + str_query
  if get_app().debug:
    url   = "http://puertogeo.appspot.com" + url_for('frontend/link/share') + '?' + str_query
  
  shortener_params = { "login"    : "diventiservices",
                       "apiKey"   : "R_3a5d98588cb05423c22de21292cd98d6",
                       "longurl"  : url, 
                       "format"   : "json"
                       }
                       
  form_data = urllib.urlencode(shortener_params)             
  
  post_url='http://api.bitly.com/v3/shorten?'+form_data
  
  result = urllib2.urlopen(post_url).read()
  
  bitlydata = json.decode(result)

  bitly_hash = ""
  if 'url' in bitlydata['data']:
    bitly_hash  = bitlydata['data']['hash']
  
  return url_for('frontend/link/map', _full=True, bitly_hash=bitly_hash) 

def expand_bitly_url(bitly_hash):
  import urllib2
  
  url = 'http://bit.ly/' + bitly_hash
  expander_params =   { "login"    : "diventiservices",
                       "apiKey"   : "R_3a5d98588cb05423c22de21292cd98d6",
                       "shortUrl"  : url, 
                       "format"   : "json"
                       }

                       
  form_data       = urllib.urlencode(expander_params)             
  
  post_url        = 'http://api.bitly.com/v3/expand?'+form_data
  
  # result = urlfetch.fetch(url=post_url, method=urlfetch.GET)
  result          = urllib2.urlopen(post_url).read()
  
  decoded_result  = json.decode(result)
  
  if 'expand' not in decoded_result['data'] or 'long_url' not in decoded_result['data']['expand'][0]:
    return None
  return cgi.parse_qs(decoded_result['data']['expand'][0]['long_url'].split('?')[1])
  
  
def get_dict_from_querystring_dict(query_dict):
  south         = query_dict['south'][0]
  north         = query_dict['north'][0]
  west          = query_dict['west'][0]
  east          = query_dict['east'][0]
  center_lat    = (float(north) + float(south))/2
  center_lon    = (float(east) + float(west))/2
  
  dict = {}
  for key in query_dict.keys():
    value = query_dict[key][0]
    if value is not None and len(value):
      dict[key] = value
  
  dict['center_lat'] = center_lat
  dict['center_lon'] = center_lon
  
  return dict

# ================================================= #
# Nuevos métodos sin uso de Bit.ly    ============= #  
def get_link_url(str_query, is_user_chared_link = True, slug='', description=''):
  mLink = None
  if is_user_chared_link:
    mLink = Link.new_for_user()
  else:
    mLink = Link.new_for_admin()
  mLink.description   = description
  mLink.slug          = slug
  mLink.query_string  = str_query
  mLink.put()
   
  key_name_or_id      = str(mLink.key().id())
  if description is None or len(description)<1:
    slug = 'compartido-%s' % key_name_or_id
  return url_for('frontend/map/slug/key', _full=True, slug=slug, key_name_or_id=key_name_or_id)
  
def expand_link_url(key_name_or_id):
  mLink = Link.get_by_id(int(key_name_or_id))
  return expand_link_url_ex(mLink)

def expand_link_url_ex(link):
  return cgi.parse_qs(link.query_string)
# FIN Funciones para manejo de Links....     ===================================== #
# ================================================================================ #


def get_or_404(key):
    try:
        obj = db.get(key)
        if obj:
            return obj
    except db.BadKeyError, e:
        # Falling through to raise the NotFound.
        pass

    abort(404)

class need_auth(object):
  def __init__(self, roles=None, code=0, url='backend/auth/login', checkpay=True):
    self.roles    = roles
    self.url      = url
    self.code     = code
    self.checkpay = checkpay

  def __call__(self, f):
    def validate_user(handler, *args, **kwargs):
      if handler.is_logged and (not self.roles or sum(map(lambda r: 1 if r in self.roles else 0, handler.roles)) ):
        
        # Trapeamos que no esta pagando
        if self.checkpay and handler.is_no_payment:
          return handler.redirect_to('backend/account/status')

        return f(handler, *args, **kwargs)
      
      if self.code:
        handler.abort(self.code)
      else:
        return handler.redirect_to(self.url)
      
    return validate_user

class FlashBuildMixin(object):
  def set_error(self, msg):
    self.session.add_flash(self.build_error(msg))
    
  def set_ok(self, msg):
    self.session.add_flash(self.build_ok(msg))
    
  def set_info(self, msg):
    self.session.add_flash(self.build_info(msg))
    
  def set_warning(self, msg):
    self.session.add_flash(self.build_warning(msg))
  
  def build_error(self, msg):
    return { 'type':'error', 'message':msg }
    
  def build_ok(self, msg):
    return { 'type':'success', 'message':msg }
  
  def build_info(self, msg):
    return { 'type':'info', 'message':msg }
    
  def build_warning(self, msg):
    return { 'type':'warning', 'message':msg }
    

class BackendMixin(object):
  def mine_or_404(self, key):
    obj = get_or_404(key)
    if not self.has_role('ultraadmin') and str(obj.realestate.key()) != self.get_realestate_key():
      abort(404)
    return obj
  
  def do_login(self, user):
    self.session['account.logged']                  = True
    self.session['account.enabled']                 = user.enabled
    self.session['account.fullname']                = '%s, %s' % (user.last_name, user.first_name)
    self.session['account.key']                     = str(user.key())
    self.set_realestate_key(str(user.realestate.key()))
    self.session['account.realestate.name']         = user.realestate.name
    self.session['account.realestate.status']       = user.realestate.status
    self.session['account.roles']                   = map(lambda s: s.strip(), user.rol.split(','))
    
    if self.is_ultraadmin:
      self.session['account.realestate.status'] = RealEstate._ENABLED
      
  @property
  def is_enabled(self):
    return self.is_logged and 'account.enabled' in self.session and self.session['account.enabled'] != 0
  
  @property
  def is_no_payment(self):
    return 'account.realestate.status' in self.session and self.session['account.realestate.status'] == 4
  
  def get_user_key(self):
    return self.session['account.key']
    
  def get_realestate_key(self):
    return self.session['account.realestate.key']
  
  def set_realestate_key(self, key):
    self.session['account.realestate.key'] = key
  
  def get_user_fullname(self):
    return self.session['account.fullname']

  def has_role(self, role):
    return role in self.session['account.roles'] if 'account.roles' in self.session else False

  @property
  def is_ultraadmin(self):
    return self.has_role('ultraadmin')
  
  @property
  def is_admin(self):
    return self.has_role('admin')

  @property
  def is_logged(self):
    return self.session['account.logged'] if 'account.logged' in self.session else False
  
  @property
  def roles(self):
    return self.session['account.roles']

class Jinja2Mixin(object):
  
  @cached_property
  def jinja2(self):
      j2 = jinja2.get_jinja2(app=self.app)
      
      self.setup_jinja_enviroment(j2.environment)
      
      # Returns a Jinja2 renderer cached in the app registry.
      return j2

  def setup_jinja_enviroment(self, env):

    env.filters['currencyfy']         = do_currencyfy
    env.filters['statusfy']           = do_statusfy
    env.filters['pricefy']            = do_pricefy
    env.filters['addressify']         = do_addressify
    env.filters['descriptify']        = do_descriptify
    env.filters['headlinify']         = do_headlinify
    env.filters['slugify']            = do_slugify
    env.filters['operationfy']        = do_operationfy
    env.filters['totalareafy']        = do_totalareafy
    env.filters['expensasfy']         = do_expensasfy
    env.filters['add_days']           = do_add_days
    env.filters['ownerify']           = do_ownerify
    env.globals['url_for']            = self.uri_for
    env.globals['app_version_id']     = self.app.config['directodueno']['app_version_id']
    env.globals['app_version']        = self.app.config['directodueno']['app_version']
    env.globals['is_debug']           = self.app.debug
    
    
    if hasattr(self,'is_logged'):
      env.globals['is_logged'] = self.is_logged
    
    if hasattr(self,'is_no_payment'):
      env.globals['is_no_payment'] = self.is_no_payment
      
    if hasattr(self,'has_role'):
      env.globals['has_role']  = self.has_role

    env.globals['session']     = self.session

    if hasattr(self.session, 'get_flashes'):
      flashes = self.session.get_flashes()
      env.globals['flash'] = flashes[0][0] if len(flashes) and len(flashes[0]) else None
      
  def render_response(self, _template, **context):
      # Renders a template and writes the result to the response.
      rv = self.jinja2.render_template(_template, **context)
      self.response.write(rv)
  
  def render_template(self, _template, **context):
      # Renders a template and writes the result to the response.
      rv = self.jinja2.render_template(_template, **context)
      return rv
      
class MyBaseHandler(RequestHandler, Jinja2Mixin, FlashBuildMixin):
  def dispatch(self):
      # Get a session store for this request.
      self.session_store = sessions.get_store(request=self.request)

      try:
          # Dispatch the request.
          RequestHandler.dispatch(self)
      finally:
          # Save all sessions.
          self.session_store.save_sessions(self.response)

  @cached_property
  def session(self):
      # Returns a session using the default cookie key.
      return self.session_store.get_session()
  
  def render_json_response(self, *args, **kwargs):
    self.response.content_type = 'application/json'
    self.response.write(json.encode(*args, **kwargs))
    
  def handle_exception(self, exception=None, debug=False):
    logging.exception(exception)
    
    text = 'Se ha producido un error en el servidor,<br/>intenta volver al inicio'
    code = 500
    
    if isinstance(exception,HTTPException):
      if exception.code == 404:
        text = u'La página solicitada no ha sido encontrada,<br/>intenta volver al inicio'
      
      code = exception.code
    
    self.render_response('error.html', code=code, text=text )
    self.response.status = str(code)+' '

  @cached_property
  def config(self):
    return get_app().config
      
class BackendHandler(MyBaseHandler, BackendMixin):
  pass

class FrontendHandler(MyBaseHandler):
  pass

class RealestateHandler(MyBaseHandler):
  def get_realestate_key_ex(self, realestate_key_or_id):
    try:
      id = str(int(realestate_key_or_id))
      return db.Key.from_path('RealEstate', id)
    except:
      return db.Key(realestate_key_or_id)
      
class NetworkPropertyMapper(Mapper):
  KIND        = Property
  FILTERS     = []
  
  def __init__(self, owner, friend, do_add=True, for_admin=True, for_website=False): 
    
    self.owner            = owner
    self.friend           = friend
    self.friend_website   = RealEstate.get_realestate_sharing_key(friend)
    self.do_add           = do_add
    self.for_admin        = for_admin
    self.for_website      = for_website
    self.FILTERS          = [ ('realestate', db.Key(owner)) ]
    
    # logging.error(u'NetworkPropertyMapper::__init__() owner:%s friend:%s'%(self.owner, self.friend));
    
    super(NetworkPropertyMapper, self).__init__()
    return
    
  def map(self, prop):

    prop_val  = prop.location_geocells
    # logging.error(u'NetworkPropertyMapper::map() owner:%s friend:%s'%(self.owner, self.friend));
    if self.do_add:
      if self.for_admin and self.friend not in prop_val:
        prop_val.append(self.friend)
      if self.for_website and self.friend_website not in prop_val:
        prop_val.append(self.friend_website)
      return ([prop],[])
    
    if not self.do_add:
      if self.for_admin and self.friend in prop_val:
        prop_val.remove(self.friend)
      if self.for_website and self.friend_website in prop_val:
        prop_val.remove(self.friend_website)
      return ([prop],[])
      
    return ([],[])
    
  # def finish(self):
      # """Called when the mapper has finished, to allow for any final work to be done."""
      # pass

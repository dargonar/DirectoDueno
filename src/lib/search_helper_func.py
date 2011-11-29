# -*- coding: utf-8 -*-
import logging
import unicodedata

from google.appengine.ext import db
from geo import geotypes
from webapp2 import cached_property
from webob.multidict import MultiDict

from models import Property, PropertyIndex
from search_helper import config_array, alphabet, MAX_QUERY_RESULTS
from backend_forms import PropertyFilterForm

def _simple_error(message, code=400):
  return {
    'status': 'error',
    'error': { 'message': message },
    'results': []
  }

def create_query_from_dict(values, Model, keys_only=True):
  
  base_query = Model.all(keys_only=keys_only)
  request_keys = values.keys()
  # ============================================================= #
  # PRICE ======================================================= #
  oper            = int(values.get('prop_operation_id', 1))
  currency        = str(values.get('currency', Property._CURRENCY_ARS)).upper()
  currency_rate = 1.0
  if currency == Property._CURRENCY_USD:
    currency_rate = Property._CURRENCY_RATE 
  price_field   = 'price_sell_computed' if oper==Property._OPER_SELL else 'price_rent_computed'
  
  if 'price_apply' in request_keys:
    if 'price_min' in request_keys:
      min_price = float(values.get('price_min'))*currency_rate
      if min_price < 0.1:
        min_price = 0;
      #logging.error('METO %s >= %.0f' % (price_field,float(min_price)) )
      base_query.filter(price_field+' >=', min_price)
    
    if 'price_max' in request_keys:
      max_price = float(values.get('price_max'))*currency_rate
      max_config = int(config_array['multiple_values_properties']['prop_operation_id']['ranges'][str(oper)]['max'])
      # 500001 hacked en utils.js
      if (((max_config!=int(max_price)) and oper==Property._OPER_RENT) or ((500001.0!=max_price) and oper==Property._OPER_SELL) ):
        #logging.error('METO %s >= %.0f' % (price_field,max_price) )
        base_query.filter(price_field+' <=', max_price)
  # ============================================================= #
  
  # ============================================================= #
  # Property types ============================================== #
  prop_type_ids = sorted([alphabet[int(str(x).replace('prop_type_id[','').replace(']',''))] for x in request_keys if 'prop_type_id' in x ])
  #logging.info('  prop_type_ids :'+str(prop_type_ids ))
  if len(prop_type_ids) > 0:
    prop_types_config_array = config_array['cells']['prop_type_id']['generated_attributes']
    allowed_values = []
    prop_type_cell_format = ''
    # tomo un solo valor de los ids elegidos.
    alphabet_char = prop_type_ids[0]
    for key in prop_types_config_array.keys():
      allowed_values = prop_types_config_array[key]['array']
      if alphabet_char in allowed_values:
        prop_type_cell_format = prop_types_config_array[key]['format']
        break
      else:
        allowed_values = []
    
    if len(allowed_values)>0:
      cell = ''
      for char in allowed_values:
        cell += char if char in prop_type_ids else '0'
      formatted_cell = prop_type_cell_format % cell
      #logging.error('[PROP TYPES CELL] location_geocells = ' + formatted_cell)
      base_query.filter( 'location_geocells = ', formatted_cell)
  # ============================================================= #
  
  # ============================================================= #
  # DISCRETE RANGES ============================================= #
  discrete_range_config_array = config_array['discrete_range_config']
  for key, item in discrete_range_config_array.items():
    attribute = None 
    value = None
    if key in request_keys:
      value = int(values.get(key))
      if int(value) <= 0:
        continue
      attribute = item['related_property']
      if item['is_indexed_property']==False:
        if value >= item['min_value']:
          value = item['min_value']
      the_value = '%s%s' % (attribute, str(value))
      #logging.error('[DISCRETE RANGES] ' + the_value)
      base_query.filter( 'location_geocells = ', the_value)
  # ============================================================= #  
  
  # ============================================================= #
  # multiple_values_properties ================================== #
  for key in config_array['multiple_values_properties'].keys():
    if key in request_keys:
      value = int(values.get(key))
      if(int(value)>0):
        attribute = config_array['multiple_values_properties'][key]['related_property']
        the_value = '%s%s' % (attribute, str(value))
        #logging.error('[MVP] ' + the_value)
        base_query.filter( 'location_geocells = ', the_value)
  # ============================================================= #  

  
  # ============================================================= #
  # binary_values_properties ==================================== #
  binary_values_properties_array = config_array['binary_values_properties']
  for key in binary_values_properties_array.keys():
    if key in request_keys:
      the_value = binary_values_properties_array[key]['related_property']
      #logging.error('[BINARY PROPERTIES] ' + the_value)
      base_query.filter( 'location_geocells = ', the_value)
  # ============================================================= #  
  
  # ============================================================= #
  # Filtro por key de Inmobiliaria=============================== #
  if values.has_key('realestate_key'):
      #logging.error('realestate= ' + values['realestate_key'])
      base_query.filter('realestate = ', db.Key(values['realestate_key']))

  # ============================================================= #
  # Orden                    ==================================== #
  sort = values.get('sort', '-'+price_field)
  sort = sort.replace('sort_price', price_field)
  #logging.error('ORDERBY ' + sort)
  base_query.order(sort)
  
  return base_query, {'operation':oper, 'price_field':price_field, 'currency':currency}

class PropertyPaginatorMixin(object):
  state_source = 'request'
  page_size    = 20
  
  def get2(self, **kwargs):
    
    if 'page' in kwargs:
      self.state_source = 'session'
      
    page = int(kwargs.get('page','1'))
    kwargs['properties'] , kwargs['page'] = self.get_items(page=page)
    
    return self.show_list(**kwargs)
  
  def post2(self, **kwargs):
    if not self.form.validate():
      return self.show_list(**kwargs)

    return self.get2(**kwargs)

  #  ---- VIRTUAL FUNCTIONS ----
  def render(self, **kwargs):
    return
    
  def add_extra_filter(self, base_query):
    return
  #  ---- VIRTUAL FUNCTIONS ----
  
  def get_items(self, page=1):
    if page == 1:
      self.session['cursor'] = [None]
    
    values = self.form.data
      
    if values['prop_type'] != 0:
      values['prop_type_id[%d]' % values['prop_type'] ] = 'on'
    
    if values['prop_operation_id'] != 0:
      if values['price_max'] is None:
        values['price_max'] = 500000000
      
      if values['price_min'] is None:
        values['price_min'] = 0

      values['price_apply'] = 'yes'
    
    base_query,_ = create_query_from_dict(values, Property, False)

    if values['location_text'] != '':
      tmp = unicodedata.normalize('NFKD', values['location_text']).encode('ascii', 'ignore').lower()
      for s in tmp.replace(' ',',').split(','):
        if s != '':
          base_query.filter('location_geocells =', '_' + s)

    # Llamamos por si se nececsita agregar mas filtros
    self.add_extra_filter(base_query)
    
    # Tomo las propiedades para la pagina 
    properties, page = self.get_properties_for_page(page, base_query)

    # Si estoy en la ultima pagina y se borra todo si vuelvo a esa pagina mostraria 
    # que no hay datos, deberia ir a la pagina anterior si se puede (page>1) o sino 
    # dejarlo asi (borre todo y habia una sola pagina )
    if len(properties) == 0 and page > 1:
      # Elimino el cursor de esa pagina por que no existe mas
      self.session['cursor'] = self.session['cursor'][:-1]
      page                   = page - 1
      properties, page       = self.get_properties_for_page(page, base_query)
    
    # Saco el cursor y veo si lo tengo que guardar (si es que estoy al final)
    # y si nos dio por lo menos page_size de taman/o
    new_cursor = base_query.cursor()
    if page+1 > len(self.session['cursor']):
      ss = self.session['cursor']
      ss.append( new_cursor )
      self.session['cursor'] = ss

    # Retornamos las propiedades y la pagina correjida
    return properties, page    

  def get_properties_for_page(self, page, base_query):
    
    # Si me piden una pagina que esta mas alla de mis cursores, uso la ultima y redefino page
    if page > len(self.session['cursor']):
      page = len(self.session['cursor'])
    
    # Tomo el cursor para la pagina
    cursor = self.session['cursor'][page-1]
    
    return base_query.with_cursor(cursor).fetch(self.page_size), page
    
  def show_list(self, **kwargs):
    kwargs['form']      = self.form
    kwargs['Property']  = Property
    kwargs['page_size'] = self.page_size
    return self.render(**kwargs)
  
  @cached_property
  def form(self):
    from models import RealEstate, RealEstateFriendship
    
    if self.state_source == 'request':
      self.session['request.data'] = self.request.POST.mixed()
    
    form                            = PropertyFilterForm(MultiDict(self.session['request.data']))
    
    if 'account.realestate.key' in self.session:
      my_key  = self.session['account.realestate.key']
      rs      = db.get(my_key)
      friends  = RealEstateFriendship.all().filter('realestates = ', my_key).filter('state = ', RealEstateFriendship._ACCEPTED).fetch(1000)
      form.realestate_network.choices = [(my_key, rs.name), ('ALL','<<Mi RED ULTAPROP>>')]+[(str(rs_friend.get_the_other_realestate(my_key, key_only=True)), '--'+rs_friend.get_the_other_realestate(my_key, key_only=False).name) for rs_friend in friends]
      form.realestate_network.default = my_key
    else:
      form.realestate_network.choices = [('ALL','<<Mi RED ULTAPROP>>')]
    return form
    
class Searcher(object):
  def __init__(self, request):
    self.request=request
  
  def doSearch(self, cursor_key, **kwargs):
    query_type = self.request["query_type"]
    
    if not query_type in ['proximity', 'bounds']:
      return _simple_error('El parámetro de búsqueda debe ser "proximity" o "bounds".', code=400)
      
    if query_type == 'proximity':
      try:
        center = geotypes.Point(float(self.request['lat']),
                                float(self.request['lon']))
      except ValueError:
        return _simple_error('lat and lon parameters must be valid latitude and longitude values.', code=400)
        
    elif query_type == 'bounds':
      try:
        bounds = geotypes.Box(float(self.request['north']),
                              float(self.request['east']),
                              float(self.request['south']),
                              float(self.request['west']))
      except ValueError:
        return _simple_error('north, south, east, and west parameters must be valid latitude/longitude values.', code=400)
    
    max_distance = 80000 # 80 km ~ 50 mi
    if self.request.has_key('max_distance'):
      max_distance = float(self.request['max_distance'])
    
    #---extirpado--
    base_query, price_data = create_query_from_dict(self.request, PropertyIndex)
    #---extirpado--
    
    max_results = MAX_QUERY_RESULTS
    if self.request.has_key('max_results'):
      max_results = int(self.request['max_results'])
    
    results, the_box, new_cursor_key = Property.bounding_box_fetch(
        base_query, bounds, max_results=max_results, cost_function=None , cursor_key=cursor_key
        )
    
    total_count   = 'cientos'
    viewing_count = len(results)
    
    return {'properties':results
            , 'total_count':total_count
            , 'viewing':viewing_count
            , 'the_box':'<br/>'+the_box+'<br/><br/>cursor_key:'+str(cursor_key)
            , 'cursor_key': new_cursor_key
            , 'price_data': price_data
            }
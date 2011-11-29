# -*- coding: utf-8 -*-
import logging
import cgi

from webapp2_extras.json import json
from google.appengine.ext import db

from search_helper import config_array, MAX_QUERY_RESULTS
from search_helper_func import Searcher
from utils import FrontendHandler, expand_link_url_ex, get_dict_from_querystring_dict
from models import Property, Link


class Index(FrontendHandler):
  def get(self, **kwargs):
    
    if not self.session.has_key('frontend.querystring'):
      show_extended_filter = self.request.GET.get('filtro_extendido',default=0)
      dict = {}
      for key in self.request.GET.keys():
        value = self.request.GET.get(key)
        if value is not None: # and len(str(value))>0:
          dict[key] = value
      dict['prop_operation_id']     = str(Property._OPER_SELL)
      dict['show_extended_filter']  = show_extended_filter
      if self.session.has_key('map.filter.realestate'):
        dict['map.filter.realestate'] = self.session.pop('map.filter.realestate')
    else:
      dict = self.session.pop('frontend.querystring') #self.session.clear()
      
    return self.render_response('frontend/index.html'
                          , config_arrayJSON=json.dumps(config_array)
                          , config_array=config_array
                          , max_results=MAX_QUERY_RESULTS
                          , preset=dict
                          , presetJSON=json.dumps(dict)
                          , _OPER_SELL=Property._OPER_SELL
                          , _OPER_RENT=Property._OPER_RENT)

  def post(self, **kwargs):
    dict = {}
    for key in self.request.POST.keys():
      value = self.request.POST.get(key)
      if value is not None and len(value)>0:
        dict[key] = value
    self.session['frontend.querystring'] = dict
    
    return self.redirect_to('frontend/map')

  def realesate_filtered(self, **kwargs):
    self.session['map.filter.realestate'] = kwargs['realestate']
    return self.redirect_to('frontend/map')
    
  # ================================================================================================ #  
  # Handlea los pedidos con formato "_/mapa/<slug>/<key_name_or_id> donde slug.get_format() = "casa-ph-departamento-en-venta-en-la-plata",
  #   escupiendo en el HTML GET el listado de propiedades y el json con las coords.
  # ToDo: implementar esto para todos los GETs de MAPA.
  def slugged_link(self, **kwargs):
    
    key_name_or_id =  kwargs['key_name_or_id']
    if len(key_name_or_id)<1:
      return self.redirect_to('frontend/map')
    
    mLink       = Link.get_by_id(int(key_name_or_id))
    query_dict  = expand_link_url_ex(mLink)
    
    dict = get_dict_from_querystring_dict(query_dict)
    
    # ================================= BEGIN FROM SEARCH ========================================== #
    _searcher = Searcher(dict)
    result = _searcher.doSearch(cursor_key=None, **kwargs)
    #return self.response.write(result)
    if 'status' in result:
      return self.redirect_to('frontend/map')
      
    properties  = db.get(result['properties'])
    
    price_data              = result['price_data']
    price_data_operation    = price_data['operation']
    price_data_price_field  = price_data['price_field']
    price_data_currency     = price_data['currency']
    
    
    html    = self.render_template('frontend/templates/_properties.html', properties=properties, Property=Property, 
                price_data_operation=price_data_operation
                , price_data_price_field=price_data_price_field
                , price_data_currency=price_data_currency
                , base_cursor_index = 0)

    coords = [({
                'lat': prop.location.lat,
                'lng': prop.location.lon,
                'key': str(prop.key()),
                'headline': prop.headline}
                )
              for prop in properties if prop is not None]
 
    markers_coords = json.dumps({
          'coords': coords,
          'status':'success',
          'display_total_count': result['total_count'],
          'display_viewing_count': result['viewing'],
          'the_box' : '',
          'cursor': str(result['cursor_key'])
          })
    # ================================= END FROM SEARCH ========================================== #
    return self.render_response('frontend/index.html'
                          , config_arrayJSON    = json.dumps(config_array)
                          , config_array        = config_array
                          , max_results         = MAX_QUERY_RESULTS
                          , preset              = dict
                          , presetJSON          = json.dumps(dict)
                          , _OPER_SELL          = Property._OPER_SELL
                          , _OPER_RENT          = Property._OPER_RENT
                          , markers_coords      = markers_coords
                          , html_property_list  = html
                          , title_description   = mLink.description)
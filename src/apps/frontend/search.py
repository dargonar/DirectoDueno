# -*- coding: utf-8 -*-
import logging
from google.appengine.ext import db

from webapp2 import Response
from webapp2_extras import json

from geo import geotypes

from models import Property
from utils import FrontendHandler

from search_helper_func import Searcher, MAX_QUERY_RESULTS

class Search(FrontendHandler):
  def get(self, **kwargs):
  
    #self.response.write(Response('hola todos'))
    #return
    
    this_cursor       = self.request.GET.get('cursor')
    this_cursor_index = self.request.GET.get('cursor_index', default='0')
    if this_cursor is not None and len(str(this_cursor))<1:
      this_cursor=None
    
    _searcher = Searcher(self.request.GET)

    # Si el resultado es un 'simple_error' retornamos directamente
    result = _searcher.doSearch(cursor_key=this_cursor, **kwargs)
    if 'status' in result:
      logging.error('TIRO ERROR TIRO ERORR');
      return self.render_json_response(result)
      
    properties  = db.get(result['properties'])
    
    price_data              = result['price_data']
    price_data_operation    = price_data['operation']
    price_data_price_field  = price_data['price_field']
    price_data_currency     = price_data['currency']
    
    
    html    = self.render_template('frontend/templates/_properties.html', properties=properties, Property=Property, 
                price_data_operation=price_data_operation
                , price_data_price_field=price_data_price_field
                , price_data_currency=price_data_currency
                , base_cursor_index = int(this_cursor_index)*MAX_QUERY_RESULTS)

    coords = [({
                'lat': prop.location.lat,
                'lng': prop.location.lon,
                'key': str(prop.key()),
                'headline': prop.headline}
                )
              for prop in properties if prop is not None]
 
    return self.render_json_response({
          'html': html,
          'coords': coords,
          'status':'success',
          'display_total_count': result['total_count'],
          'display_viewing_count': result['viewing'],
          'the_box' : str(result['the_box'])+';sent_cursor'+str(this_cursor),
          'cursor': str(result['cursor_key'])
          })
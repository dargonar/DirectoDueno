# -*- coding: utf-8 -*-
"""
    Consultas
    ~~~~~~~~
"""
from __future__ import with_statement

import logging
import re

from google.appengine.ext import db

from utils import get_or_404, need_auth, BackendHandler
from models import RealEstate, Consulta, Property

    
class Index(BackendHandler):
  page_size    = 20
  
  @need_auth()
  def get(self, **kwargs):
    return self.render(**kwargs)
  
  def page(self, **kwargs):
    return self.render(**kwargs)
    
  def render(self, **kwargs):
    realestate                    = get_or_404(self.get_realestate_key())
    kwargs['mnutop']              = 'consultas'   
    kwargs['Property']            = Property
    kwargs['page_size']           = self.page_size
    
    page = int(kwargs.get('page','1'))
    kwargs['consultas'] , kwargs['page'] = self.get_items(page=page, realestate=realestate)
    kwargs['page']  = page

    return self.render_response('backend/consultas.html', **kwargs)
  
  def get_items(self, page=1, realestate=None):
    if page == 1:
      self.session['consultas_cursor'] = [None]
  
    base_query  = Consulta.all().filter(' realestate = ', realestate.key()).order('-created_at')
    
    consultas, page = self.get_consultas_for_page(page, base_query)
  
    if len(consultas) == 0 and page > 1:
      # Elimino el cursor de esa pagina por que no existe mas
      self.session['consultas_cursor']  = self.session['consultas_cursor'][:-1]
      page                              = page - 1
      consultas, page                   = self.get_consultas_for_page(page, base_query)
    
    new_cursor = base_query.cursor()
    if page+1 > len(self.session['consultas_cursor']):
      ss = self.session['consultas_cursor']
      ss.append( new_cursor )
      self.session['consultas_cursor'] = ss

    # Retornamos las consultas y la pagina correjida
    return consultas, page    
    
  def get_consultas_for_page(self, page, base_query):
    
    # Si me piden una pagina que esta mas alla de mis cursores, uso la ultima y redefino page
    if page > len(self.session['consultas_cursor']):
      page = len(self.session['consultas_cursor'])
    
    # Tomo el cursor para la pagina
    cursor = self.session['consultas_cursor'][page-1]
    
    return base_query.with_cursor(cursor).fetch(self.page_size), page
# -*- coding: utf-8 -*-
"""
    property handlers
    ~~~~~~~~
"""
from __future__ import with_statement

import logging
import unicodedata

from google.appengine.ext import db
from google.appengine.api import taskqueue

from webapp2 import cached_property, Response, RequestHandler

from backend_forms import PropertyForm, PropertyFilterForm
from models import Property, PropertyIndex, ImageFile, RealEstate
from search_helper_func import PropertyPaginatorMixin, create_query_from_dict

from utils import need_auth, BackendHandler 

class UpdateIndex(RequestHandler):
  # Solo se puede llamar desde appengine por eso no lo aseguramos
  # La configuracion esta en el app.yaml _ah/defered
  def post(self, **kwargs):
    key      = self.request.POST['key']
    action   = self.request.POST['action']
    property = db.get(key)
    oldpi    = PropertyIndex.all().filter('property =', db.Key(key)).get()
    
    # Necesita actualizar el indice
    if action == 'need_update':
      if oldpi:
        property.update_property_index(oldpi)
        oldpi.save()
      else:
        action = 'need_rebuild'
    
    if action == 'need_rebuild' or action == 'need_remove':
      if oldpi: oldpi.delete()
      if action == 'need_rebuild':
        pi = PropertyIndex(key_name = '%s,%f,%f' % (str(property.key()), property.location.lat, property.location.lon))
        property.update_property_index(pi)
        pi.put()
    
    self.response.write('ok')

class Restore(BackendHandler):
  
  @need_auth(code=404)
  def get(self, **kwargs):
    property = self.mine_or_404(kwargs['key'])
    property.status = Property._NOT_PUBLISHED
    property.save(build_index=False)
    
    self.response.write('ok')

class Remove(BackendHandler):
  
  @need_auth(code=404)
  def post(self, **kwargs):
   
    page      = int(self.request.POST['page'])
    newstatus = int(self.request.POST['newstatus'])
    
    keys = []
    for key in self.request.POST:
      if key != 'page' and key != 'newstatus':
        keys.append(key)
    
    properties = []
    for property in Property.get(keys):
      property.status  = newstatus
      property.save(build_index=False)
      
      # Verifico que sean mias las propiedades que voy a borrar del indice
      if str(property.realestate.key()) != self.get_realestate_key():
        self.abort(500)
      
      properties.append(property)
    
    # Salvamos y mandamos a remover del indice
    def savetxn():
      for key in keys:
        taskqueue.add(url=self.url_for('property/update_index'), params={'key': key,'action':'need_remove'}, transactional=True)
    
    db.run_in_transaction(savetxn)
    
    self.set_ok('Las propiedades fueron %s correctamente' % ('recuperadas' if newstatus == Property._NOT_PUBLISHED else 'borradas') )
    return self.redirect_to('property/listpage', page=page)
    
class Publish(BackendHandler):
  
  @need_auth(code=404)
  def get(self, **kwargs):
    
    property = self.mine_or_404(kwargs['key'])
    property.status = Property._PUBLISHED if int(kwargs['yes']) else Property._NOT_PUBLISHED
    property.save(build_index=False)
    
    # Updateamos y mandamos a rebuild el indice si es necesario
    def savetxn():
      property.save(build_index=False)
      taskqueue.add(url=self.url_for('property/update_index'), params={'key': str(property.key()),'action':'need_rebuild' if property.status == Property._PUBLISHED else 'need_remove'}, transactional=True)
    
    db.run_in_transaction(savetxn)
    return self.render_response('backend/includes/prop_list.html', property=property, Property=Property)
    
class Images(BackendHandler):
  
  @need_auth()
  def get(self, **kwargs):

    property = self.mine_or_404(kwargs['key'])
    images = ImageFile.all().filter('property =', property.key()).order('position')
    
    params = { 'current_tab' : 'pictures',
               'title'       : 'Fotos de la propiedad',
               'key'         :  kwargs['key'],
               'mnutop'      : 'propiedades',
               'images'      :  images}

    return self.render_response('backend/includes/pictures.html', **params)
    
class List(BackendHandler, PropertyPaginatorMixin):
  
  @need_auth()
  def get(self, **kwargs):
    return self.get2(**kwargs)
  
  @need_auth()
  def post(self, **kwargs):
    self.request.charset  = 'utf-8'
    return self.post2(**kwargs)

  def add_extra_filter(self, base_query):
    if not self.has_role('ultraadmin'):
      base_query.filter('realestate =', db.Key( self.get_realestate_key() ) )
      
    base_query.filter('status =', self.form.status.data)
      
      
  def render(self, **kwargs):
    kwargs['mnutop'] = 'propiedades'
    return self.render_response('backend/property_list.html', **kwargs)
    
class NewEdit(BackendHandler):
  
  @need_auth()
  def get(self, **kwargs):
    if 'key' in kwargs:
      kwargs['title'] = 'Editando Propiedad'
      kwargs['form']  = PropertyForm(obj=self.mine_or_404(kwargs['key']))
    else:
      if len(Property.all().filter('realestate = ',db.Key(self.get_realestate_key())).fetch(10))>=1:
        self.set_error(u'Comuníquese con DirectoDueño si desea publicar más de una propiedad; por correo (ayuda@directodueno.com) o a través del <a href="%s">panel de ayuda</a>.' % self.uri_for('backend/help'))
        return self.redirect_to('property/list')
      kwargs['title'] = 'Nueva Propiedad'
      kwargs['form']  = self.form
    
    return self.show_property_form(**kwargs)
  
  @need_auth(code=404)
  def post(self, **kwargs):
    self.request.charset  = 'utf-8'
    
    editing = 'key' in self.request.POST and len(self.request.POST['key'])
    
    if not editing:
      if len(Property.all().filter('realestate = ',db.Key(self.get_realestate_key())).fetch(10))>=1:
        self.set_error(u'Comuníquese con DirectoDueño si desea publicar más de una propiedad.')
        return self.redirect_to('property/list')
        
    if not self.form.validate():
      kwargs['title'] = 'Editando Propiedad' if editing else 'Nueva Propiedad'
      kwargs['form']  = self.form
      kwargs['key']   = self.request.POST['key'] if editing else None
      kwargs['flash'] = {'message':'Verifique los datos ingresados', 'type':'error'}
      return self.show_property_form(**kwargs)
    
    # Actualizo o creo el model
    property = self.mine_or_404(self.request.POST['key']) if editing else Property.new(db.Key(self.get_realestate_key()))
    self.form.update_object(property)
    
    # Updateamos y mandamos a rebuild el indice si es necesario
    # Solo lo hacemos si se require y la propiedad esta publicada
    # Si se modifica una propiedad BORRADA o DESACTIVADA no se toca el indice por que no existe
    
    def savetxn():
      result = property.save(build_index=True) if editing else property.put()
      if result != 'nones' and property.status == Property._PUBLISHED:
        taskqueue.add(url=self.url_for('property/update_index'), params={'key': str(property.key()),'action':result}, transactional=True)
    
    db.run_in_transaction(savetxn)
    
    if self.request.POST['goto'] == 'go':
      return self.redirect_to('property/images', key=str(property.key()))

    self.set_ok('La propiedad fue %s ' % ('modificada con exito.' if editing else u'creada con exito, sera visible en el mapa dentro de la próxima hora.') )    
    return self.redirect_to('property/listpage', page=1)

  def show_property_form(self, **kwargs):
      kwargs['current_tab'] = 'type'
      kwargs['mnutop']      = 'propiedades'  
      return self.render_response('backend/includes/form.html', **kwargs)
    
  @cached_property
  def form(self):
    return PropertyForm(self.request.POST)
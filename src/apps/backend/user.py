# -*- coding: utf-8 -*-
"""
    Auth & RealState
    ~~~~~~~~
"""
import logging

from google.appengine.ext import db
from webapp2 import cached_property

from backend_forms import UserForm, UserChangePasswordForm
from utils import get_or_404, need_auth, BackendHandler

class Edit(BackendHandler):
  #Edit/New
  @need_auth()
  def get(self, **kwargs):
    user                        = get_or_404(self.get_user_key())
    kwargs['form']              = UserForm(obj=user)
    return self.render(user, **kwargs) 
  
  #Create/Save User.
  @need_auth()
  def post(self, **kwargs):
    self.request.charset  = 'utf-8'
    
    user                        = get_or_404(self.get_user_key())
    u_validated = self.form.validate()
    if not u_validated:
      kwargs['form']         = self.form
      if self.form.errors:
        kwargs['flash']      = self.build_error('Verifique los datos ingresados:')
      return self.render(user, **kwargs) 

    user          = self.form.update_object(user)
    user.save()
    
    # Actualizo los cambios en la sesión.
    self.do_login(user)
    
    self.set_ok('Usuario guardado satisfactoriamente.')
    return self.redirect_to('backend/user/edit')
  
  @need_auth()
  def password(self, **kwargs):
    user                        = get_or_404(self.get_user_key())
    u_validated = self.change_password_form.validate()
    if not u_validated:
      kwargs['form']              = UserForm(obj=user)
      kwargs['password_form']     = self.change_password_form
      self.set_error('Verifique los datos ingresados:')
      return self.render(user, **kwargs) 
    
    user          = self.change_password_form.update_object(user)
    user.save()
    
    self.set_ok('Contraseña guardada satisfactoriamente.')
    return self.redirect_to('backend/user/edit')
  
  def render(self, user, **kwargs):
    kwargs['user']              = user
    kwargs['key']               = self.get_user_key()
    if not kwargs.has_key('password_form'):
      kwargs['password_form']     = UserChangePasswordForm()
    kwargs['mnutop']            = 'usuarios'
      
    return self.render_response('backend/user.html', **kwargs)
    
  @cached_property
  def form(self):
    return UserForm(self.request.POST)
  
  @cached_property
  def change_password_form(self):
    return UserChangePasswordForm(self.request.POST)
    
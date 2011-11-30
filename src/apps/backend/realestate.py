# -*- coding: utf-8 -*-
"""
    Auth & RealState
    ~~~~~~~~
"""
from __future__ import with_statement

import logging
import re

from google.appengine.api import files
from google.appengine.ext import db
from google.appengine.api import images 
from google.appengine.api.images import get_serving_url

from backend_forms import RealEstateForm, validate_domain_id
from utils import get_or_404, need_auth, BackendHandler
from webapp2 import cached_property
from models import RealEstate


class Edit(BackendHandler):
  #Edit/New
  @need_auth()
  def get(self, **kwargs):
    
    realestate                    = get_or_404(self.get_realestate_key())
    kwargs['form']                = RealEstateForm(obj=realestate)
    kwargs['key']                 = self.get_realestate_key()
    kwargs['mnutop']              = 'inmobiliaria'
    kwargs['realestate_logo']     = realestate.logo_url
    
    return self.render_response('backend/realestate.html', **kwargs)
  
  #Create/Save RealEstate & User.
  @need_auth()
  def post(self, **kwargs):
    self.request.charset = 'utf-8'
    
    realestate = get_or_404(self.get_realestate_key())
    
    #HACK: Hack? le pongo un miembro para que la validacion del slug sepa cual es la key actual de la RealEste
    #de otra forma va a decir que ya esta siendo utilizada
    self.form.thekey = self.get_realestate_key()
    
    rs_validated = self.form.validate()
    if not rs_validated:
      kwargs['form']                = self.form
      kwargs['key']                 = self.get_realestate_key()
      kwargs['realestate_logo']     = realestate.logo_url
      if self.form.errors:
        kwargs['flash']         = self.build_error(u'Verifique los datos ingresados:')
        # + '<br/>'.join(reduce(lambda x, y: str(x)+' '+str(y), t) for t in self.form.errors.values()))
      return self.render_response('backend/realestate.html', **kwargs)
    
    
    realestate = self.form.update_object(realestate)

    realestate.save()
    
    # Actualizo los cambios en la sesión.
    self.do_login(db.get(self.get_user_key()))
    
    # Set Flash
    self.set_ok('Inmobiliaria guardada satisfactoriamente.')
    if self.request.POST['goto'] == 'website':
      return self.redirect_to('backend/realestate_website/edit')
    return self.redirect_to('backend/realestate/edit')
    
  @cached_property
  def form(self):
    return RealEstateForm(self.request.POST)
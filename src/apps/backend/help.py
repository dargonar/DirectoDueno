# -*- coding: utf-8 -*-
"""
    Help
    ~~~~~~~~
"""
import logging
from google.appengine.api import mail
from webapp2 import cached_property

from utils import get_or_404, need_auth, BackendHandler
from backend_forms import HelpDeskForm
from models import HelpDesk

class Index(BackendHandler):
  @need_auth(code=500)
  def get(self, **kwargs):
    user                    = get_or_404(self.get_user_key())
    
    kwargs['mnutop']              = 'help'
    kwargs['form']                = HelpDeskForm(obj=HelpDesk.new_for_current(user))
    return self.render_response('backend/help.html', **kwargs)
  
  @cached_property
  def form(self):
    return HelpDeskForm(self.request.POST)
    
  @need_auth()
  def post(self, **kwargs):
    self.request.charset = 'utf-8'
    
    realestate = get_or_404(self.get_realestate_key())
    
    rs_validated = self.form.validate()
    if not rs_validated:
      kwargs['form']                = self.form
      kwargs['mnutop']              = 'help'
      if self.form.errors:
        kwargs['flash']         = self.build_error(u'Verifique los datos ingresados:')
        # + '<br/>'.join(reduce(lambda x, y: str(x)+' '+str(y), t) for t in self.form.errors.values()))
      return self.render_response('backend/help.html', **kwargs)
    
    helpdesk = HelpDesk() 
    helpdesk.realestate       = realestate
    helpdesk.realestate_name  = realestate.name
    helpdesk = self.form.update_object(helpdesk)
    
    mail_to='info@directodueno.com'
    body='El usuario %s solicita ayuda. Key: %s. MSG" "%s"' % (realestate.email, str(realestate.key()), helpdesk)
    mail.send_mail(sender="www.directodueno.com <info@directodueno.com>", 
                 to       = mail_to,
                 subject  = "DirectoDueño: Un cliente necesita ayuda",
                 body     = body)
    
    helpdesk.save()
    
    # Set Flash
    self.set_ok(u'Su solicitud fue enviada satisfactoriamente.<br/> A la brevedad un agente de DirectoDueño se comunicará con Ud.')
    return self.redirect_to('backend/help')
# -*- coding: utf-8 -*-
"""
    account handlers
    ~~~~~~~~
"""
import logging
from datetime import datetime

from google.appengine.ext import db

from models import Invoice, RealEstate
from utils import need_auth, BackendHandler 

class Status(BackendHandler):
  
  @need_auth(checkpay=False)
  def get(self, **kwargs):
    re          = db.get(self.get_realestate_key())
    invoices    = []
    
    invoices.extend( Invoice.all().filter('realestate', re.key()).filter('state', Invoice._INPROCESS).order('date') )
    invoices.extend( Invoice.all().filter('realestate', re.key()).filter('state', Invoice._NOT_PAID).filter('date <= ', datetime.now()).order('date') )
    
    total_debt  = reduce(lambda x,i: x + (i.amount if i.state == Invoice._NOT_PAID else 0), invoices, 0)

    
    params = {
      're'        :re,
      'invoices'  :invoices,
      'total_debt':total_debt,
      'mnutop'    :'cuenta',
      'plan'      :re.plan,
      'Invoice'   :Invoice,
    }
      
    return self.render_response('backend/account.html', **params)
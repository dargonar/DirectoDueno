# -*- coding: utf-8 -*-
import logging
from utils import FrontendHandler

class Handler(FrontendHandler):
  def get(self, **kwargs):
    return self.render_response('frontend/promo-lanzamiento.html')



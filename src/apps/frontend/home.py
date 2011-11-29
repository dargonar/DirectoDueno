# -*- coding: utf-8 -*-
import logging

from webapp2_extras.json import json
from search_helper import config_array
from utils import FrontendHandler
from models import Property, Link, RealEstate

class Index(FrontendHandler):
  def get(self, **kwargs):
    preset        = {'prop_operation_id':str(Property._OPER_SELL)}
    direct_links  = Link.all().filter('type = ', 'home').fetch(25)
    return self.render_response('frontend/home.html'
                , config_array    = config_array
                , preset          = preset
                , presetJSON      = json.dumps(preset)
                , _OPER_SELL      = Property._OPER_SELL
                , _OPER_RENT      = Property._OPER_RENT
                , direct_links    = direct_links)

class Red(FrontendHandler):
  def get(self, **kwargs):
    realestates   = RealEstate.all().order('name')
    return self.render_response('frontend/red.html'
                , realestates     = realestates)

class Terms(FrontendHandler):
  def get(self, **kwargs):
    return self.render_response('frontend/terms.html')

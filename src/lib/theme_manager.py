# -*- coding: utf-8 -*-
import logging

default_theme = 'theme_grey'
themes        = {   'theme_green_blue':      {'props_at_home': 5}
                  , 'theme_blue':         {'props_at_home': 5}
                  , 'theme_grey':         {'props_at_home': 5}
                  , 'theme_red_black':    {'props_at_home': 4}
                  , 'theme_red_white':    {'props_at_home': 4}}
                  
def get_props_at_home(theme):
  return themes[theme]['props_at_home']

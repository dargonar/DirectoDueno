# -*- coding: utf-8 -*-
import logging
from webapp2 import uri_for as url_for
from datetime import datetime, timedelta

from models import Property, RealEstate, User, RealEstateFriendship
from re import *
from backend_forms import status_choices
from search_helper import config_array, alphabet

_slugify_strip_re = compile(r'[^\w\s-]')
_slugify_hyphenate_re = compile(r'[-\s]+')

def do_add_days(date, days):
  return date + timedelta(days=days)

def do_slugify(value):
  """
  Normalizes string, converts to lowercase, removes non-alpha characters,
  and converts spaces to hyphens.
  
  From Django's "django/template/defaultfilters.py".
  """
  import unicodedata
  
  if not isinstance(value, unicode):
      value = unicode(value)
  value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
  value = unicode(_slugify_strip_re.sub('', value).strip().lower())
  return _slugify_hyphenate_re.sub('-', value)
    
def do_headlinify(prop):
    
    descs = config_array['multiple_values_properties']['prop_operation_id']['descriptions']
    
    # Ponemos el headline
    ops = []
    for i in range(0,len(descs)):
      if i & prop.prop_operation_id:
        ops.append(descs[i])
        
    return u'%s en %s' % ( config_array['cells']['prop_type_id']['short_descriptions'][alphabet.index(prop.prop_type_id)]
                                  , '/'.join(ops))
  
def do_descriptify(prop, cols, small=False, total_area_included=False):
  items = { 'rooms'        : { 'desc': 'ambiente'   ,'small':'amb.'       ,'plural': True  },
            'bedrooms'     : { 'desc': 'dormitorio' ,'small':'dorm.'      ,'plural': True  },
            'bathrooms'    : { 'desc': u'baño'      ,'small':u'bano.'     ,'plural': True  },
            'area_indoor'  : { 'desc': u'm² cub.'   ,'small':u'm² cub.'   ,'plural': False },
            'area_outdoor' : { 'desc': u'm² descub.','small':u'm² descub.','plural': False }, }
            
  parts = []
  for col in cols:
    # Tenemos esta columna?
    if col not in items:
      continue

    item = items[col]      
    
    # Tomamos el valor, como son todos integers si es 0(=sin dato) no lo mostramos
    val = int(getattr(prop, col))
    if not val:
      continue
    
    # Ponemos la descripción y pluralizamos si hay que hacerlo y si no es small (el small no se pluraliza)
    desc = item['desc']
    if not small:    
      if item['plural'] and val > 1:
        desc += 's'
    elif 'small' in item:
      desc = item['small']

    # Agregamos al arreglo
    parts.append( u'%d %s' % (val, desc) )
  
  stringy = ', '.join(parts)
  
  if not total_area_included:
    return stringy
  
  total_area = do_totalareafy(prop)
  
  if len(total_area)>0:
    return stringy+', '+total_area+' totales.'
  
  return stringy

def do_totalareafy(prop):
  if prop.area_indoor <= 0.0 and prop.area_outdoor <=0.0:
    return ''
  return u'%.1f m²' % (prop.area_outdoor+prop.area_indoor)
  
def do_addressify(prop):

  parts = []
  
  street = prop.street_name
  tmp = street.lower()
  if ' entre ' not in tmp and ' y ' not in tmp:
    if prop.street_number > 0:
      street += ' al ' + str(int(int(prop.street_number/100)*100))

  parts.append(street)
  
  if prop.neighborhood and prop.neighborhood.strip() != '':
    parts.append( prop.neighborhood.strip() )

  parts.append(prop.hack_city)
  return ', '.join(parts)


def do_statusfy(val):
  for choice in status_choices:
    if choice[0] == val:
      return choice[1]
  
  return ''
  
def do_time_distance_in_words(from_date, since_date = None, target_tz=None, include_seconds=False):
  '''
  Returns the age as a string
  '''
  if since_date is None:
    since_date = datetime.now(target_tz)

  distance_in_time = since_date - from_date
  distance_in_seconds = int(round(abs(distance_in_time.days * 86400 + distance_in_time.seconds)))
  distance_in_minutes = int(round(distance_in_seconds/60))

  if distance_in_minutes <= 1:
    if include_seconds:
      for remainder in [5, 10, 20]:
        if distance_in_seconds < remainder:
          return "menos de %s seconds" % remainder
      if distance_in_seconds < 40:
        return "medio minuto"
      elif distance_in_seconds < 60:
        return "menos de un minuto"
      else:
        return "1 minuto"
    else:
      if distance_in_minutes == 0:
        return "menos de un minuto"
      else:
        return "1 minuto"
  elif distance_in_minutes < 45:
    return "%s minutos" % distance_in_minutes
  elif distance_in_minutes < 90:
    return "cerca de 1 hora"
  elif distance_in_minutes < 1440:
    return "cerca de %d hora" % (round(distance_in_minutes / 60.0))
  elif distance_in_minutes < 2880:
    return "1 d&iacute;a"
  elif distance_in_minutes < 43220:
    return "%d dias" % (round(distance_in_minutes / 1440))
  elif distance_in_minutes < 86400:
    return "cerca de 1 mes"
  elif distance_in_minutes < 525600:
    return "%d meses" % (round(distance_in_minutes / 43200))
  elif distance_in_minutes < 1051200:
    return "cerca de 1 a&ntilde;o"
  else:
    return "mas de %d a&ntilde;os" % (round(distance_in_minutes / 525600))

def do_currencyfy(number, small=False, **args):
  temp = "%.1f" % number
  # if small:
    # temp = "%d" % int(number)
  temp = temp.replace('.', ',')
  profile = compile(r"(\d)(\d\d\d[.,])")
  while 1:
      temp, count = subn(profile,r"\1.\2",temp)
      if not count: break
  if small:
    if ',' in temp:
      return temp[:-2]
  return temp
  
def do_operationfy(operation_id):
  if operation_id == Property._OPER_SELL:
    return 'Venta'
  return 'Alquiler'
  
def do_pricefy(property, operation_type = None, small=False, extended_format=False, **args):
  number = property.price_rent
  cur = property.price_rent_currency
  #if (operation_type is None and property.price_sell_computed>0.0) or int(operation_type) == Property._OPER_SELL:
  if property.prop_operation_id == Property._OPER_SELL:
    number = property.price_sell
    cur = property.price_sell_currency
  if extended_format:
    return '<span class="value price"><small>%s</small> %s</span>' % (cur, do_currencyfy(number))
  return '<small>'+cur+'</small>'+do_currencyfy(number, small=small)
  
def do_expensasfy(property, operation_type = None, small=False, small_if_none=False, **args):
  number = property.price_expensas
  cur = property.price_rent_currency
  if (not property.price_expensas) or int(operation_type) != Property._OPER_RENT:
    if small_if_none:
      return '<span class="mth">Sin datos / No tiene</span>'
    else:
      return 'Sin datos / No tiene'
  return '<small>'+cur+'</small>'+do_currencyfy(number, small=small) + (' <span class="mth">/mes</span>' if not small else '')
  
def do_ownerify(realestate, min=False):
  user = User.all().filter(' realestate = ', realestate).get()
  if min:
    return '%s (%s)' % (user.full_name, user.email)
  return 'De <i>%s</i> <br/>%s' % (user.full_name, user.email)
   
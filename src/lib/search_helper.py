# -*- coding: utf-8 -*-
import logging

# ============================================================ #
# PRIVATE ==================================================== #
alphabet                              = '0123456789abcdef'
MAX_QUERY_RESULTS                     = 100

config_array = {
  # 'cells' contiene la configuración de los atributos de tipo 'geocell' de una Propiedad para generar StringList de conbinaciones binarias 
  # a partir de un 'alphabet'.
  'cells':{
    'prop_type_id': {
      'descriptions':         [u'--indistinto--', u'Casa', u'Departamento', u'PH', u'Oficina', u'Local Comercial o Fondo de Comercio', u'Galpon o Deposito o Edificio Ind.', u'Consultorio', u'Casa en Country o Barrio Cerrado',  u'Quinta', u'Lote o Terreno', u'Cochera', u'Campo o Chacra']
      , 'short_descriptions': [u'--indistinto--', u'Casa', u'Depto.', u'PH', u'Oficina', u'Local', u'Galpon', u'Consultorio', u'Country', u'Quinta', u'Lote', u'Cochera', u'Campo']
      , 'has_divider':        [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1]
      , 'in_home':            [0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
      , 'generated_attributes':{
        #  'array': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b'], 'format':  'ty%s'
         'prop_type_id_xresidential_cells':    {'array': ['0', '1', '2', '3'],      'format':  'ty%s00000000'}
         , 'prop_type_xbiz_cells':             {'array': ['0', '4', '5', '6', '7'], 'format':  'ty000%s0000'}
         , 'prop_type_id_xcountryside_cells':  {'array': ['0', '8', '9', 'a'],      'format':  'ty0000000%s0'}
         , 'prop_type_id_xothers_cells':       {'array': ['0', 'b'],                'format':  'ty0000000000%s'}
         , 'prop_type_id_xlote':               {'array': ['0', 'c'],                'format':  'ty0000000000%s'}
      } 
    }
  }
  # 'discrete_range_config' contiene la configuración de los atributos de tipo rango de una Propiedad que se discretizan.
  , 'discrete_range_config' : {
      'area_indoor':  { 
                  'rangos':[0, 40, 50, 60, 70, 100, 200, 300, 9999999999]
                  , 'related_property': 'ai' #'area_indoor_id'
                  , 'is_indexed_property' : True
                  , 'descriptions':[u'--indistinto--', u'0 a 40 m2', u'40 a 50 m2', u'50 a 60 m2', u'60 a 70 m2', u'70 a 100 m2', u'100 a 200 m2', u'200 a 300 m2', u'300 m2 o más']
        }
      , 'area_outdoor': {
                  'rangos':[0, 10, 20, 50, 100, 9999999999]
                  , 'related_property': 'ao' #'area_outdoor_id'
                  , 'is_indexed_property' : True
                  , 'descriptions':[u'--indistinto--', u'0 a 10 m2', u'10 a 20 m2', u'20 a 50 m2', u'50 a 100 m2', u'100 m2 o más']
        }
      , 'year_built':   {
                  'rangos':[ 0, 1, 5, 10, 20, 50, 9999999999]
                  , 'related_property': 'yb' #'year_built_id'
                  , 'is_indexed_property' : True
                  , 'descriptions' : [u'--indistinto--', u'A estrenar', u'menor a 5 años', u'entre 5 y 10 años', u'entre 10 y 20 años', u'entre 20 y 50 años', u'más de 50 años' ]
        }
      , 'rooms':{
                  'rangos':[ 0, 1, 2, 3, 4, 5, 6, 9999999999]
                  , 'descriptions' : [u'--indistinto--', u'1 ambiente', u'2 ambientes', u'3 ambientes', u'4 ambientes', u'5 ambientes', u'6 ambientes o más']
                  , 'min_value': 6
                  , 'related_property': 'ro' #'rooms_id'
                  , 'is_indexed_property' : False
        } 
      , 'bathrooms':{
                  'rangos':[ 0, 1, 2, 3, 9999999999]
                  , 'descriptions' : [u'--indistinto--', u'1 baño', u'2 baños', u'3 baños o más']
                  , 'min_value': 3
                  , 'related_property': 'ba' #'bathrooms_id'
                  , 'is_indexed_property' : False
        }
      , 'bedrooms': {
                  'rangos':[ 0, 1, 2, 3, 4, 5, 9999999999]
                  , 'descriptions' : [u'--indistinto--', u'1 habitación', u'2 habitaciones', u'3 habitaciones', u'4 habitaciones', u'5 habitaciones o más']
                  , 'min_value': 5
                  , 'related_property': 'be' #'bedrooms_id'
                  , 'is_indexed_property' : False
      }
      , 'prop_state_id': {
                  'rangos': [ 0, 1, 2, 3, 4, 5, 6, 7, 8]
                  , 'related_property':'st'
                  , 'is_indexed_property' : True
                  , 'descriptions': [u'--indistinto--', u'Nuevo', u'Excelente', u'Muy bueno', u'Bueno', u'Regular', u'Reciclado', u'A reciclar'] 
      }
      
    }
  , 'multiple_values_properties':{
    # 'prop_state_id':             {'descriptions': [u'Indistinto', u'Nuevo', u'A reciclar', u'Reciclado', u'Regular', u'Bueno', u'Muy bueno', u'Excelente'] 
                                  # , 'related_property':'st'}
     'prop_operation_state_id': {'descriptions': [u'--indistinto--', u'Disponible', u'Reservada', u'Vendida', u'Alquilada']
                                  , 'related_property':'os'}
    , 'prop_owner_id':           {'descriptions': [u'--indistinto--', u'Inmobiliaria', u'Dueño directo']
                                  , 'related_property':'ow'}
    , 'prop_operation_id':       {'descriptions': [u'--indistinto--', u'Venta', u'Alquiler']
                                    , 'related_property':'op'
                                    , 'ranges':{'1':{'step':'1', 'min':'0', 'max':'16'}, '2':{'step':'250', 'min':'0', 'max':'10000'}}
                                  }
  }
  , 'binary_values_properties':{
       'agua_corriente':    {'description': 'Agua corriente', 'title': u'Agua corriente', 'is_filter': 0, 'related_property':''}
      , 'furnished':        {'description': 'Amoblado', 'title': 'Amoblado', 'is_filter': 1, 'related_property':'ag'}
      , 'live_work':        {'description': 'Apto Prof.', 'title': 'Apto Profesional', 'is_filter': 1, 'related_property':'al'}
      , 'elevator':         {'description': 'Ascensor', 'title': 'Ascensor', 'is_filter': 1, 'related_property':'ad'}
      , 'balcony':          {'description': u'Balcón', 'title': u'Balcón', 'is_filter': 1, 'related_property':'ab'}
      , 'cloacas':          {'description': 'Cloacas', 'title': u'Cloacas', 'is_filter': 0, 'related_property':''}
      ,'appurtenance':      {'description': 'Dependencia', 'title': 'Dependencia', 'is_filter': 1 , 'related_property':'aa'}
      , 'fireplace':        {'description': 'Estufa Hogar', 'title': 'Estufa Hogar', 'is_filter': 1, 'related_property':'af'}
      , 'garage':           {'description': 'Garage', 'title': 'Garage', 'is_filter': 1, 'related_property':'ah'}
      , 'gas_natural':      {'description': 'Gas natural', 'title': u'Gas natural', 'is_filter': 0, 'related_property':''}
      , 'gas_envasado':     {'description': 'Gas envasado', 'title': u'Gas envasado', 'is_filter': 0, 'related_property':''}
      , 'gym':              {'description': 'Gimnasio', 'title': 'Gimnasio', 'is_filter': 1, 'related_property':'ak'}
      , 'internet':         {'description': 'Internet', 'title': u'Internet', 'is_filter': 0, 'related_property':''}
      , 'monitoreo':        {'description': 'Monitoreo', 'title': u'Monitoreo', 'is_filter': 0, 'related_property':''}
      , 'washer_dryer':     {'description': 'Laundry', 'title': 'Laundry', 'is_filter': 1, 'related_property':'ap'}
      , 'luxury':           {'description': 'Lujo', 'title': 'Lujo', 'is_filter': 1, 'related_property':'am'}
      , 'grillroom':        {'description': 'Parrilla', 'title': 'Parrilla', 'is_filter': 1, 'related_property':'aj'}
      , 'garden':           {'description': 'Patio', 'title': 'Patio', 'is_filter': 1, 'related_property':'ai'}
      , 'pool':             {'description': 'Piscina', 'title': 'Piscina', 'is_filter': 1, 'related_property':'an'}
      , 'doorman':          {'description': 'Portero', 'title': 'Portero', 'is_filter': 1, 'related_property':'ac'}
      , 'sum':              {'description': 'SUM', 'title': u'Salón de usos múltiples', 'is_filter': 1, 'related_property':'aq'}
      , 'telefono':         {'description': u'Teléfono', 'title': u'Teléfono', 'is_filter': 0, 'related_property':''}
      , 'terrace':          {'description': 'Terraza', 'title': 'Terraza', 'is_filter': 1, 'related_property':'ao'}
      , 'tv_cable':         {'description': 'TV por cable', 'title': u'TV por cable', 'is_filter': 0, 'related_property':''}
      , 'vigilancia':       {'description': 'Vigilancia', 'title': u'Vigilancia', 'is_filter': 0, 'related_property':''}
      
  }
}

#Tabla de rates por defecto
default_currency_table = {
  'ARS' : {'USD':0.25},
  'USD' : {'ARS':4.00},
}  

# Esta funcion retorna un par con (alphabet[x], alphabet[0:y])
#   x = el indice del primer item mayor que value, si no se encuentra este item, retorna la longitud del array.
#   y = len(array).
def get_index_alphabet(value, array, is_binary=False):
  
  if is_binary:
    if value in array and value != '0':
      return (value, [value])
    
    this_alphabet = map(lambda x:str(x),array)
    return ( alphabet[array.index(value) if value in array else 0], this_alphabet)
  
  filtered = filter(lambda x:x>=value,array)
  return (alphabet[array.index( min(filtered))]
            , alphabet[0:len(array)] )
            
# Producto cartesiano de un array de listas.  
def product(*args):
  if not args:
      return iter(((),)) # yield tuple()
  return (items + (item,) 
          for items in product(*args[:-1]) for item in args[-1])

# Itera sobre las listas y llama a product .... 
def build_list(cells):
  todos = []
  for i,v in enumerate(cells):
    items = []
    for j in range(0, len(cells)):
      items.append( [cells[j][0]] if j == i else cells[j][1] )
    todos += product( *items )
  
  return set([reduce(lambda x, y: str(x)+str(y), t) for t in todos])

# Retorna las 'keys' de las 'keys' de config_array + extras.
# Estas son propiedades que se meten en el indice
def indexed_properties(extras=[]):
  return sum([config_array[j].keys() for j in config_array.keys()], extras)
  
def calculate_price(price, currency_origin, currency_dest, table=default_currency_table):
  if currency_origin == currency_dest:
    return price
  try:
    rate = table[currency_origin][currency_dest]
    return rate*price
  except:
    return -0.1
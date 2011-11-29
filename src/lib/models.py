# -*- coding: utf-8 -*-

from google.appengine.ext import db, blobstore
from geo.geomodel import GeoModel
import random 
import logging
import unicodedata

from datetime import date, datetime , timedelta

from search_helper import config_array, alphabet, MAX_QUERY_RESULTS
from search_helper import build_list, get_index_alphabet , calculate_price, indexed_properties

from geo import geocell

class UPConfig(db.Model):
  last_ipn     = db.DateProperty()
  last_ipn_emi = db.DateProperty()

class Plan(db.Model):
  _MONTHLY     = 1
  _ONE_TIME    = 2
  _EMI_MONTHLY = 3

  name                = db.StringProperty()
  description         = db.StringProperty()
  type                = db.IntegerProperty()
  amount              = db.IntegerProperty()
  free_days           = db.IntegerProperty()
  payd_days           = db.IntegerProperty()
  online              = db.IntegerProperty()
  
  def __repr__(self):
    return 'PLAN: ' + self.name
    
class RealEstate(db.Model):
  
  _REGISTERED   = 0
  _TRIAL        = 1
  _TRIAL_END    = 2
  _ENABLED      = 3
  _NO_PAYMENT   = 4 
  
  @classmethod
  def new(cls):
    rs = RealEstate(status=RealEstate._TRIAL, managed_domain=0)
    rs.tpl_title  = u'Hacemos más fácil, rápida y segura su operación inmobiliaria'
    rs.tpl_text   = u'Nuestra inmobiliaria se ha convertido en una empresa moderna y dinámica. Hoy cuenta con los más modernos sistemas de comercialización, con los recursos humanos y con la tecnología necesarios para realizar con éxito sus negocios inmobiliarios.'
    rs.is_tester  = False
    return rs
  
  @classmethod
  def get_realestate_sharing_key(cls, string_key, realestate=None):
    prefix = 'fe_'
    if string_key is not None and string_key.strip()!='':
      return prefix+string_key
    return prefix+str(realestate.key())
  
  def get_web_theme(self):
    if self.web_theme is not None and self.web_theme.strip()!='':
      return self.web_theme
    return 'theme_grey'
    
  logo                = blobstore.BlobReferenceProperty() #--Borrar--
  logo_url            = db.StringProperty(indexed=False)
  name                = db.StringProperty()
  website             = db.StringProperty(indexed=False)
  email               = db.EmailProperty(indexed=False)
  tpl_title           = db.StringProperty(indexed=False)
  tpl_text            = db.TextProperty(indexed=False)
  
  title               = db.StringProperty()
  fax_number          = db.StringProperty(indexed=False)
  telephone_number    = db.StringProperty(indexed=False)
  telephone_number2   = db.StringProperty(indexed=False)
  open_at             = db.StringProperty(indexed=False)
  
  address             = db.StringProperty(indexed=False)
  zip_code            = db.StringProperty()
  updated_at          = db.DateTimeProperty(auto_now=True)
  created_at          = db.DateTimeProperty(auto_now_add=True)
  
  enable              = db.IntegerProperty() #--borrar--
  status              = db.IntegerProperty()
  managed_domain      = db.IntegerProperty()
  is_tester           = db.BooleanProperty()
  
  web_theme           = db.StringProperty(indexed=False)
  domain_id           = db.StringProperty()
  plan                = db.ReferenceProperty(Plan)
  last_email          = db.DateProperty()
  last_invoice        = db.DateProperty()
  last_login          = db.DateTimeProperty()
  
  def is_in_trial(self):
    return self.status==RealEstate._TRIAL
  @staticmethod
  def public_attributes():
    """Returns a set of simple attributes on Immovable Property entities."""
    return ['logo', 'name', 'website', 'email', 'title', 'fax_number', 'telephone_number', 'telephone_number2', 'address', 'zip_code', 'enable']
  
  def __repr__(self):
    return self.name

class Payment(db.Model):
  trx_id              = db.StringProperty()
  date                = db.DateProperty()
  amount              = db.IntegerProperty()
  assinged            = db.IntegerProperty()
  created_at          = db.DateTimeProperty(auto_now_add=True)

class Invoice(db.Model):
  _INVALID    = 0
  _NOT_PAID   = 1
  _INPROCESS  = 2
  _PAID       = 3
  _INBANK     = 4
  
  realestate          = db.ReferenceProperty(RealEstate)
  trx_id              = db.StringProperty()
  amount              = db.IntegerProperty()
  payment             = db.ReferenceProperty(Payment)
  state               = db.IntegerProperty()
  date                = db.DateProperty()
  created_at          = db.DateTimeProperty(auto_now_add=True)

  def str_state(self, css=True):
    if self.state == Invoice._INPROCESS:
      return ('inprocess' if css else 'En Proceso')
    
    if (datetime.now().date() - self.date).days > 15:
      return ('pending' if css else 'Vencida')
    
    return ('indate' if css else 'Pendiente')
    
class User(db.Model):
  
  @classmethod
  def new(cls):
    return User(enabled=0, restore_password=0)
  
  first_name          = db.StringProperty()
  last_name           = db.StringProperty()
  mobile_number       = db.StringProperty(indexed=False)
  telephone_number    = db.StringProperty(indexed=False)  
  email               = db.EmailProperty()
  rol                 = db.StringProperty(required=True, default='oper')
  password            = db.StringProperty()
  gender              = db.StringProperty(indexed=False)
  birthday            = db.DateProperty(auto_now_add=True, indexed=False)
  realestate          = db.ReferenceProperty(RealEstate)
  enabled             = db.IntegerProperty()
  restore_password    = db.IntegerProperty()
  updated_at          = db.DateTimeProperty(auto_now=True)
  created_at          = db.DateTimeProperty(auto_now_add=True)
  
  @property
  def full_name(self):
    return '%s %s' % (self.first_name if self.first_name else '' , self.last_name if self.last_name else '')
  
  def __repr__(self):
    return self.name

class Property(GeoModel):

  _PUBLISHED     = 1
  _NOT_PUBLISHED = 2
  _DELETED       = 3
  
  # realestates_friends     => al ser amigos
  # realestates_frontend    => al ampliar oferta  
  @staticmethod
  def new(realestate):
    return Property(realestate=realestate, status=Property._PUBLISHED ,image_count=0)
    
  status                  = db.IntegerProperty()
  def is_deleted(self):
    return self.status == Property._DELETED
  
  def is_published(self):
    return self.status == Property._PUBLISHED
  
  def is_not_published(self):
    return self.status == Property._NOT_PUBLISHED
  
  # Information Fields	
  headline                = db.StringProperty()
  main_description        = db.TextProperty()
  country                 = db.StringProperty(indexed=False)
  state                   = db.StringProperty(indexed=False)
  city                    = db.StringProperty(indexed=False)
  neighborhood            = db.StringProperty(indexed=False)
  street_name             = db.StringProperty(indexed=False)
  street_number           = db.IntegerProperty(indexed=False)
  
  zip_code                = db.StringProperty(indexed=False)
  	
  floor                   = db.StringProperty(indexed=False)
  building_floors	        = db.IntegerProperty(indexed=False)
  	
  images_count            = db.IntegerProperty()
  	
  neighborhood_name       = db.StringProperty(indexed=False)         
  user                    = db.ReferenceProperty(User)
  
  # ===================================================== # 
  # Search fields	                                        #
  # ===================================================== #
  
  # AREA FIELDS
  area_indoor             = db.IntegerProperty(indexed=False)
    # 1	 # 0-40
    # 2	 # 40-50
    # 3	 # 50-60
    # 4	 # 60-70
    # 5	 # 60-100
    # 6	 # 100-200
    # 7	 # 200-300
    # 8	 # 300 o más
  area_outdoor            = db.IntegerProperty(indexed=False)
    # 1	  # 0-10
    # 2	  # 10-20
    # 3	  # 20-50
    # 4	  # 50-100
    # 5	  # 100 o más
  
  # ROOMS FIELDS
  rooms     	            = db.IntegerProperty(indexed=False)   # 1 a 5 - P es >= 6
  bathrooms               = db.IntegerProperty(indexed=False)   # 1 a 3 - P es >= 4
  bedrooms                = db.IntegerProperty(indexed=False)   # 1 a 4 -	P es >= 5

  # PRICES FIELDS
  price_sell              = db.FloatProperty(indexed=False)
  price_rent              = db.FloatProperty(indexed=False)
  price_expensas          = db.FloatProperty(indexed=False, default=0.0)
  
  _CURRENCY_RATE          = 4
  _CURRENCY_ARS           = 'ARS'
  _CURRENCY_USD           = 'USD'
  price_sell_currency     = db.StringProperty(indexed=False)
  price_rent_currency     = db.StringProperty(indexed=False)
  
  price_sell_computed     = db.FloatProperty()
  price_rent_computed     = db.FloatProperty()
  
  # AMENITIES FIELDS GROUP 1
  appurtenance            = db.IntegerProperty(indexed=False)
  balcony                 = db.IntegerProperty(indexed=False)
  doorman                 = db.IntegerProperty(indexed=False)
  elevator                = db.IntegerProperty(indexed=False)
  fireplace               = db.IntegerProperty(indexed=False)
  furnished               = db.IntegerProperty(indexed=False)
  garage                  = db.IntegerProperty(indexed=False)
    
  # AMENITIES FIELDS GROUP 2
  garden                  = db.IntegerProperty(indexed=False)
  grillroom               = db.IntegerProperty(indexed=False)
  gym                     = db.IntegerProperty(indexed=False)
  live_work               = db.IntegerProperty(indexed=False)
  luxury                  = db.IntegerProperty(indexed=False)
  pool                    = db.IntegerProperty(indexed=False)
  terrace                 = db.IntegerProperty(indexed=False)
  
  
  # AMENITIES FIELDS GROUP 3 & YEAR BUILT
  washer_dryer            = db.IntegerProperty(indexed=False)
  sum	                    = db.IntegerProperty(indexed=False)
	
  # LAS DE EMO QUE NO ESTABAN
  agua_corriente          = db.IntegerProperty(indexed=False)
  gas_natural             = db.IntegerProperty(indexed=False)
  gas_envasado            = db.IntegerProperty(indexed=False)
  luz                     = db.IntegerProperty(indexed=False)
  cloacas                 = db.IntegerProperty(indexed=False)
  telefono                = db.IntegerProperty(indexed=False)
  tv_cable                = db.IntegerProperty(indexed=False)
  internet                = db.IntegerProperty(indexed=False)
  vigilancia              = db.IntegerProperty(indexed=False)
  monitoreo               = db.IntegerProperty(indexed=False)
  
  # ADDED BY MaRiAn
  patio                   = db.IntegerProperty(indexed=False)
  
  
  year_built	            = db.IntegerProperty(indexed=False)
    # 1	 # A estrenar
    # 2	 # menor a 5 años
    # 3	 # entre 5 y 10 años
    # 4	 # entre 10 y 20 años
    # 5	 # entre 20 y 50 años
    # 6	 # más de 50 años

  # DATETIMEs
  updated_at              = db.DateTimeProperty(auto_now=True)
  created_at              = db.DateTimeProperty(auto_now_add=True)
  
  # PUBLISHER	
  realestate              = db.ReferenceProperty(RealEstate)
  	
  # PROPERTY TYPES
  prop_type_id	                = db.StringProperty(indexed=False)
  #prop_type_id_cell                 = db.StringListProperty()  
  
  # PROPERTY STATE & OPERATION & OWNER
  prop_state_id	                = db.IntegerProperty(indexed=False)
        # Nuevo	        1
        # A reciclar	  2
        # Reciclado	    3
        # Regular	      4
        # Bueno	        5
        # Muy bueno	    6
        # Excelente	    7
  prop_operation_state_id	      = db.IntegerProperty(indexed=False)
        # Disponible	  1
        # Reservada	    2
        # Vendida	      3
        # Alquilada	    4
  prop_owner_id	                = db.IntegerProperty(indexed=False)
        # Inmobiliaria	1
        # Dueño directo	2
  _OPER_SELL=1
  _OPER_RENT=2
  prop_operation_id	            = db.IntegerProperty(indexed=False)
        # Venta	        1
        # Alquiler	    2
  
  main_image                    = blobstore.BlobReferenceProperty() #--Borrar--
  main_image_url                = db.StringProperty(indexed=False)
  # # ======================================================= #
  # # PROPIEDADES PARA DEFINIR RANGOS A PARTIR DE OTRAS PROPS #
  # area_indoor_id          = db.IntegerProperty() # 0-40
  
  # area_outdoor_id         = db.IntegerProperty() # 0-10
  
  # rooms_id                = db.IntegerProperty() # 6 o más
  # bathrooms_id            = db.IntegerProperty() # 3 o más
  # bedrooms_id             = db.IntegerProperty() # 5 o más
  
  # year_built_id           = db.IntegerProperty() # A estrenar
  # # ======================================================= #

  visits                        = db.IntegerProperty(indexed=False, default=0) 
  def has_images(self):
    if self.images_count is not None and self.images_count != 0:
      return 1
    return 0
  
  def calculate_inner_values(self):
    
    # Calculamos los precios en pesos
    self.price_rent_computed = calculate_price(self.price_rent, self.price_rent_currency, 'ARS')
    self.price_sell_computed = calculate_price(self.price_sell, self.price_sell_currency, 'ARS')
    
    # Armamos para la busqueda en backend
    address = []
    for item in ['country','state','city','neighborhood','street_name']:
      if getattr(self,item) is not None and getattr(self,item).strip() != '':
        try:
          s = unicodedata.normalize('NFKD', getattr(self,item)).encode('ascii', 'ignore').lower()
          # HACK 
          if s != u'ciudad autonoma de buenos aires':
            address += map(lambda x: '_'+x, s.split(' '))
        except Exception, e:
          pass
    self.location_geocells = self.check_options_ex()+address
    
  def need_update_index(self, oldme):
    
    # Ahora (no) tiene imagenes?
    if oldme.has_images() != self.has_images():
      return True
    
    # Cambio alguna de las propiedades que se indexan?
    for prop in indexed_properties(['location','price_sell_computed','price_rent_computed']):
      v1 = getattr(oldme,prop)
      v2 = getattr(self,prop)
      if cmp(v1,v2):
        return True
    
    return False

  def update_property_index(self, pi):
    pi.location = self.location

    max_res_geocell, primos = geocell.compute(self.location, geocell.MAX_GEOCELL_RESOLUTION, True)
    tmp = [max_res_geocell[:res] for res in range(1, geocell.MAX_GEOCELL_RESOLUTION + 1)]
   
    pi.location_geocells       = sorted(tmp+primos)+self.check_options_ex()
    pi.price_sell_computed     = self.price_sell_computed
    pi.price_rent_computed     = self.price_rent_computed
    pi.area_indoor             = self.area_indoor
    pi.bedrooms                = self.bedrooms
    pi.rooms                   = self.rooms
    pi.images_count            = self.has_images()
    pi.realestate              = self.realestate
    pi.property                = self.key()    
  
  
  def realestate_friend_keys(self):
    my_key = str(self.realestate.key())
    
    friends = RealEstateFriendship.all().filter('realestates = ', my_key).filter('state = ', RealEstateFriendship._ACCEPTED).fetch(1000)
    friend_realestates_keys = []
    friend_realestates_keys.append(my_key)
    friend_realestates_keys.append(RealEstate.get_realestate_sharing_key(my_key))
    
    for friend in friends:
      my_friend_key = friend.get_the_other_realestate(my_key, key_only=True)
      # Somos amigos, entonces ves mis props en admin
      friend_realestates_keys.append(my_friend_key)
      # Si estas mostrando mi oferta en tu web
      if friend.is_the_other_realestate_offering_my_props(my_key):
        friend_realestates_keys.append(RealEstate.get_realestate_sharing_key(my_friend_key))
  
    return friend_realestates_keys
    
  def save(self, build_index=True, friends=None):
    # Puede ser que venga de imagenes.
    if build_index:
      self.calculate_inner_values()
      self.append_friends(friends)
    # Magia para saber si necesitamos actualizar o rebuildear el index [o no hacer nada]
    # Solo para la edicion, quitar publicacion o borrar lo fuerzan directamente
    retvalue = 'nones'
    oldme = db.get(self.key())
    if self.need_update_index(oldme):
      retvalue = 'need_update'
      if self.location != oldme.location:
        retvalue = 'need_rebuild'
    
    super(Property, self).save()
    return retvalue
    
  #Cuando nuevo
  def put(self, friends):
    self.calculate_inner_values()
    self.append_friends(friends)
    super(Property, self).put()
    return 'need_rebuild'
  
  #Agrego realestates amigas a self.location_geocells y me agrgo a mi mismo jejej.
  def append_friends(self, friends):
    
    
    self.location_geocells.extend(friends)
    
  
  def getPropType(self):
    return config_array['cells']['prop_type_id']['short_descriptions'][alphabet.index(self.prop_type_id)]

  @property
  def hack_city(self):
    HACK = u'Ciudad Autónoma de Buenos Aires'
    return self.city if self.city != HACK else 'Capital Federal'

  def getPropAddress(self):
    if self.street_number<=0:
      return u'%s 0, %s, %s' % (self.street_name, self.neighborhood, self.hack_city )
    return u'%s %s, %s, %s' % (self.street_name, str(int(int(self.street_number/100)*100)), self.neighborhood, self.hack_city)
    
    
  def getPropFullAddress(self):
    from utils import do_addressify
    return do_addressify(self)
    #return u'%s, %s' % (self.getPropAddress(), self.country)
    
  def getPropOperation(self):
    return config_array['multiple_values_properties']['prop_operation_id']['descriptions'][self.prop_operation_id]
  
  def getPropState(self):
    value = self.prop_state_id
    
    if value <=0:
      return 'Sin datos'
    data  = config_array['discrete_range_config']['prop_state_id']
    if data['is_indexed_property']==True:
      array = data['rangos']
      value = array.index(min(filter(lambda x:x>=value,array)))
    else:
      if value>=data['min_value']:
        value = int(data['min_value'])
    
    return data['descriptions'][(value)]
    #return config_array['multiple_values_properties']['prop_state_id']['descriptions'][self.prop_state_id]
  
  def getAge(self):
    if self.year_built > 0:
      index = config_array['discrete_range_config']['year_built']['rangos'].index(int(self.year_built))
      return config_array['discrete_range_config']['year_built']['descriptions'][index]
    return 'Sin datos'
    
    data  = config_array['discrete_range_config']['year_built']
    value = self.year_built
    if data['is_indexed_property']==True:
      array = data['rangos']
      value = array.index(min(filter(lambda x:x>=value,array)))
    else:
      if value>=data['min_value']:
        value = int(data['min_value'])
    
    return data['descriptions'][(value)]
    
  def check_options(self):
    array = self.check_options_ex()
    self.update_location()
    self.location_geocells += array
    return 0

  def check_options_ex(self):
    options=[]
    
    generated_attributes_array = config_array['cells']['prop_type_id']['generated_attributes']
    for key in generated_attributes_array.keys():
      pair_array = []
      if(self.prop_type_id in generated_attributes_array[key]['array']):
        for value in generated_attributes_array[key]['array']:
          if value == 0:
            continue
          rango = [0, value]
          is_binary = True 
          pair = get_index_alphabet(self.prop_type_id, rango, is_binary)
          pair_array.append(pair)
        the_format = generated_attributes_array[key]['format']
        types = map(lambda x: the_format % str(x),build_list(pair_array))
        options=types
    
    for key in config_array['binary_values_properties']:
      value = getattr(self, key)
      if value == 1:
        the_property = config_array['binary_values_properties'][key]['related_property']
        options.append(the_property)
        
    discrete_range_config_array = config_array['discrete_range_config']
    for key in discrete_range_config_array.keys():
      data = discrete_range_config_array[key]
      value = getattr(self, key)
      the_property = data['related_property']
      if data['is_indexed_property']==True:
        array = data['rangos']
        value = array.index(min(filter(lambda x:x>=value,array)))
      else:
        if value>=data['min_value']:
          value = int(data['min_value'])
      the_value = '%s%s' % (the_property, str(value))
      options.append(the_value)
      
    multiple_values_properties_array = config_array['multiple_values_properties']
    for key in multiple_values_properties_array.keys():
      value = getattr(self, key)
      the_property = multiple_values_properties_array[key]['related_property']
      
      #-----------HACK PENSAR---------------
      if the_property == 'op':
        for i in range(0,len(multiple_values_properties_array[key]['descriptions'])):
          if i & value:
            the_value = '%s%s' % (the_property, str(i))
            options.append(the_value)
      #-----------HACK PENSAR---------------
      else:
        the_value = '%s%s' % (the_property, str(value))
        options.append(the_value)
    return options
    
  @staticmethod
  def public_attributes():
    """Returns a set of simple attributes on Immovable Property entities."""
    return ['headline', 'main_description', 'country', 'state', 'city', 'neighborhood', 'street_name', 'street_number', 'zip_code', 'floor',
          'building_floors', 'images_count', 'area_indoor', 'area_outdoor', 'rooms', 'bathrooms', 'bedrooms', 'appurtenance', 
          'balcony', 'doorman', 'elevator', 'fireplace', 'furnished', 'garage','garden','grillroom', 'gym', 'live_work', 
          'luxury','pool', 'terrace', 'washer_dryer', 'sum', 
          'agua_corriente', 'gas_natural', 'gas_envasado', 'luz', 'cloacas', 'telefono', 'tv_cable', 'internet', 'vigilancia', 'monitoreo','patio', 
          'year_built', 'prop_type_id', 'prop_state_id', 'prop_operation_state_id', 
          'prop_owner_id', 'prop_operation_id'
          ,'price_sell' ,'price_rent', 'price_sell_currency', 'price_rent_currency', 'price_sell_computed', 'price_rent_computed']
    #, 'user', 'realestate', 'updated_at', 'created_at'

  # @staticmethod
  # def public_attributes_ex():
    # return ['area_indoor_id', 'area_outdoor_id' , 'rooms_id', 'bathrooms_id', 'bedrooms_id', 'year_built_id']
          
  def _get_latitude(self):
    return self.location.lat if self.location else None

  def _set_latitude(self, lat):
    if not self.location:
      self.location = db.GeoPt()

    self.location.lat = lat

  latitude = property(_get_latitude, _set_latitude)

  def _get_longitude(self):
    return self.location.lon if self.location else None

  def _set_longitude(self, lon):
    if not self.location:
      self.location = db.GeoPt()

    self.location.lon = lon

  longitude = property(_get_longitude, _set_longitude)
  
  def __repr__(self):
    from myfilters import do_headlinify, do_addressify, do_descriptify
    return do_headlinify(self) + '|' + do_addressify(self) + '|' + do_descriptify(self, cols=['rooms','bedrooms','bathrooms','area_indoor', 'area_outdoor'], small=True)

class PropertyIndex(GeoModel):
  # location = db.GeoPtProperty()
  # location_geocells = db.StringListProperty()
  price_sell_computed     = db.FloatProperty()
  price_rent_computed     = db.FloatProperty()
  published_at            = db.DateTimeProperty(auto_now_add=True)
  price_changed_at        = db.DateTimeProperty(auto_now_add=True)
  area_indoor             = db.IntegerProperty()
  bedrooms                = db.IntegerProperty()
  rooms                   = db.IntegerProperty()
  realestate              = db.ReferenceProperty(RealEstate)
  property                = db.ReferenceProperty(Property)
  images_count            = db.IntegerProperty() # 1 tiene, 0 no tiene
  
class ImageFile(db.Model):
  file                = blobstore.BlobReferenceProperty()
  filename            = db.StringProperty()
  title               = db.StringProperty()
  position            = db.IntegerProperty()
  property            = db.ReferenceProperty(Property)
  realestate          = db.ReferenceProperty(RealEstate)
  created_at          = db.DateTimeProperty(auto_now_add=True)
  def __repr__(self):
    return self.filename
    
class Consulta(db.Model):
  realestate_name           = db.StringProperty()
  realestate                = db.ReferenceProperty(RealEstate)
  property                  = db.ReferenceProperty(Property)
  realestate_property_link  = db.StringProperty()
  property_link             = db.StringProperty()
  sender_name               = db.StringProperty()
  sender_email              = db.StringProperty()
  sender_comment            = db.TextProperty()
  sender_telephone          = db.StringProperty()
  prop_operation_desc       = db.StringProperty()
  is_from_ultraprop         = db.IntegerProperty()
  created_at                = db.DateTimeProperty(auto_now_add=True)

class Link(db.Model):
  @classmethod
  def new_for_user(cls):
    return Link(type='user')
  @classmethod
  def new_for_admin(cls):
    return Link(type='home')
  type                      = db.StringProperty(required=True, choices=set(['home', 'user']))
  description               = db.StringProperty()
  slug                      = db.StringProperty()
  query_string              = db.TextProperty()
  created_at                = db.DateTimeProperty(auto_now_add=True)

class HelpDesk(db.Model):
  @classmethod
  def new_for_current(cls, user):
    tel = (user.mobile_number if user.mobile_number and user.mobile_number.strip()!='' else user.telephone_number)
    if not tel:
      tel = user.realestate.telephone_number
    return HelpDesk(realestate_name=user.realestate.name
                , realestate=user.realestate
                , sender_name= '%s %s' % (user.first_name if user.first_name else '', user.last_name if user.last_name else '') 
                , sender_email=user.email
                , sender_telephone=tel)
    
  realestate_name           = db.StringProperty()
  realestate                = db.ReferenceProperty(RealEstate)
  sender_name               = db.StringProperty()
  sender_email              = db.StringProperty()
  sender_telephone          = db.StringProperty()
  sender_subject            = db.StringProperty()
  sender_comment            = db.TextProperty()
  created_at                = db.DateTimeProperty(auto_now_add=True)
  
  def __repr__(self):
    return self.realestate_name + '|' + str(self.realestate.key()) + '|' + self.sender_name + '|' + self.sender_email + '|' + self.sender_telephone + '|' + self.sender_subject + '|' + self.sender_comment + '|' + self.created_at.strftime('%d/%m/%Y')

class RealEstateFriendship(db.Model):
  _REQUESTED        = 1
  _ACCEPTED         = 2
  _DENIED           = 3
  _DELETED          = 4
  
  @classmethod
  def not_accepted_states(cls):
    return [RealEstateFriendship._REQUESTED, RealEstateFriendship._DENIED, RealEstateFriendship._DELETED]
    
  @classmethod
  def new_for_request(cls, realestate_a, realestate_b):
    rs                  = RealEstateFriendship(key_name = '%s,%s' % (str(realestate_a.key()), str(realestate_b.key())), state=RealEstateFriendship._REQUESTED)
    rs.rs_a_shows_b     = False
    rs.rs_b_shows_a     = False
    rs.realestate_a     = realestate_a
    rs.realestate_b     = realestate_b
    return rs
  
  @classmethod
  def get_the_other(cls, obj_key, known_realestate, get_key=False):
    datu        = str(obj_key.name()).split(',')
    unknown_key = datu[0]
    if(datu[0]==known_realestate):
      unknown_key = datu[1]
    if get_key:
      return db.Key(unknown_key)
    return unknown_key
  
  @classmethod
  def is_sender_ex(cls, obj_key, known_realestate):
    datu        = str(obj_key.name()).split(',')
    return datu[0]==known_realestate
    
  def is_the_other_realestate_offering_my_props(self, my_realestate_key):
    if str(self.key()).split(',')[0]==my_realestate_key:
      return self.rs_b_shows_a
    return self.rs_a_shows_b
    
  def get_the_other_realestate(self, known_realestate, key_only=False):
    if key_only:
      return RealEstateFriendship.get_the_other(self.key(), str(known_realestate), get_key=False)
    return db.get(RealEstateFriendship.get_the_other(self.key(), str(known_realestate), get_key=True))
  
  def is_sender(self, realestate):
    return self.realestate_a.key() == realestate.key()
  
  def accept(self):
    self.state = RealEstateFriendship._ACCEPTED
    self.save()
    return
    
  def reject(self):
    self.state = RealEstateFriendship._DENIED
    self.save()
    return 
  
  def alive(self):
    self.state = RealEstateFriendship._REQUESTED
    self.save()
    return 
    
  realestate_a              = db.ReferenceProperty(RealEstate, collection_name ='realestate_a')
  realestate_b              = db.ReferenceProperty(RealEstate, collection_name ='realestate_b')
  realestate_deleter        = db.ReferenceProperty(RealEstate, collection_name ='realestate_deleter') 
  created_at                = db.DateTimeProperty(auto_now_add=True)
  state                     = db.IntegerProperty()
  rs_a_shows_b              = db.BooleanProperty()
  rs_b_shows_a              = db.BooleanProperty()
  realestates               = db.StringListProperty()
  
  # def save(self):
    # super(RealEstateFriendship, self).save()
    # return self
    
  #Cuando nuevo
  def put(self):
    self.realestates.append(str(self.realestate_a.key()))
    self.realestates.append(str(self.realestate_b.key()))
    super(RealEstateFriendship, self).put()
    return self
    
  
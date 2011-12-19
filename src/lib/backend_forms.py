# -*- coding: utf-8 -*-
"""
    backend forms
    ~~~~~~~~
"""
import re
import logging

from wtforms import Form, BooleanField, SelectField, TextField, FloatField , PasswordField, FileField, DateField
from wtforms import HiddenField, TextAreaField, IntegerField, validators, ValidationError
from wtforms.widgets import TextInput
from wtforms.ext.appengine.fields import GeoPtPropertyField
from wtforms.validators import regexp
from google.appengine.ext import db

from models import Property, RealEstate, User

#value helpers
from search_helper import config_array
short_descs   = config_array['cells']['prop_type_id']['short_descriptions'][1:]
features      = config_array['discrete_range_config']
more_features = config_array['binary_values_properties']
multiple      = config_array['multiple_values_properties']

order_opts = [('sort_price','Precio (ascendente)'),
              ('-sort_price','Precio (descendente)'),]

status_choices = [(Property._PUBLISHED,'Publicadas'),(Property._NOT_PUBLISHED,'No Publicadas'), (Property._DELETED,'Eliminadas')]

class MyTextInput(TextInput):
    def __init__(self, error_class=u'error'):
        super(MyTextInput, self).__init__()
        self.error_class = error_class

    def __call__(self, field, **kwargs):
        if field.errors:
            c = kwargs.pop('class', '') or kwargs.pop('class_', '')
            kwargs['class'] = u'%s %s' % (self.error_class, c)
        return super(MyTextInput, self).__call__(field, **kwargs)
        

def is_number(s):
  try:
    float(s)
    return True
  except:
    return False

def is_int(s):
  try:
    int(s)
    return True
  except:
    return False
    
def to_float(val):
  try:
    return float(val)
  except:
    return 0.0

def to_int(val):
  try:
    return int(val)
  except:
    return 0
  
def my_float_validator(field, condition):
  if condition:
    if not field.data or isinstance(field.data, basestring) and not field.data.strip():
      raise ValidationError('Debe ingresar un precio')
    if not is_number(field.data):
      raise ValidationError('El precio es invalido')

def my_float_validator_simple(field):
  if field.data.strip() != '' and not is_number(field.data):
    raise ValidationError('El precio es invalido')
      
def my_int_validator(field):
  if field.data.strip() != '' and not is_int(field.data):
    raise ValidationError('El numero es invalido')

def validate_domain_id(domain_id, mykey=None):
    if domain_id.strip()=='':
      return {'result':'used','msg':u'El nombre no puede ser vacío'}
    
    if domain_id.strip()in['mapa', 'admin', 'red-ultraprop', '']:
      return {'result':'used','msg':u'Este nombre está restringido'}
      
    # Primero validamos que sea tipo regex
    SLUG_REGEX = re.compile('^[-\w]+$')
    if not re.match(SLUG_REGEX, domain_id):
      return {'result':'noslug','msg':'El nombre solo puede contener letras, numeros y guiones'}
    
    tmp = RealEstate.all(keys_only=True).filter('domain_id', domain_id).get()
    if tmp and (mykey is None or str(tmp) != mykey):
      return {'result':'used','msg':'El nombre ya esta siendo utilizado'}
    
    return {'result':'free','msg':'El nombre se encuentra disponible'}

#Form to filter properties
class PropertyFilterForm(Form):
  def __repr__(self):
    return 'PropertyFilterForm'
  
  location_text      = TextField('Buscar en', default='')
  prop_type          = SelectField('Tipo de propiedad', coerce=int, choices=[(0, '--indistinto--')]+[(i+1, short_descs[i]) for i in range(0,len(short_descs)) ], default=0)
  prop_operation_id  = SelectField(u'Tipo de Operación' , coerce=int, choices=[(i, multiple['prop_operation_id']['descriptions'][i]) for i in range(0, len(multiple['prop_operation_id']['descriptions']))],default=0)
  currency           = SelectField('Moneda',choices=[('ARS', '$ - Pesos'), ('USD', 'USD - Dolares')],default='ARS')
  price_min          = IntegerField(u'Precio', [validators.optional()], widget=MyTextInput())
  price_max          = IntegerField(u'Precio', [validators.optional()], widget=MyTextInput())
  area_indoor        = SelectField('Superficie' , coerce=int, choices=[( i, features['area_indoor']['descriptions'][i]) for i in range(0, len(features['area_indoor']['rangos']))],default=0)
  rooms              = SelectField('Ambientes', coerce=int, choices=[( i, features['rooms']['descriptions'][i]) for i in range(0, len(features['rooms']['rangos'])-1)],default=0)  
  bedrooms           = SelectField('Dormitorios', coerce=int, choices=[( i, features['bedrooms']['descriptions'][i]) for i in range(0, len(features['bedrooms']['rangos'])-1)],default=0)  
  sort               = SelectField(choices=[(order_opts[i][0],order_opts[i][1]) for i in range(0,len(order_opts))], default='-sort_price')
  status             = SelectField(u'Estado de publicación', coerce=int, choices=status_choices, default=Property._PUBLISHED)
  #haslocation        = BooleanField(u'Listar Todas')
  
  
  
#Form to edit/create a new property
class PropertyForm(Form):
  def __repr__(self):
    return 'PropertyForm'
    
  def update_object(self, prop):
    prop.prop_type_id         = self.prop_type_id.data
    prop.prop_operation_id    = self.prop_operation_id.data
    prop.price_sell_currency  = self.price_sell_currency.data
    prop.price_sell           = to_float(self.price_sell.data)
    prop.price_rent_currency  = self.price_rent_currency.data
    prop.price_rent           = to_float(self.price_rent.data)
    prop.price_expensas       = to_float(self.price_expensas.data)
    prop.rooms                = to_int(self.rooms.data)
    prop.bedrooms             = to_int(self.bedrooms.data)
    prop.bathrooms            = to_int(self.bathrooms.data)
    prop.building_floors      = to_int(self.building_floors.data)
    prop.year_built           = self.year_built.data
    prop.area_indoor          = to_int(self.area_indoor.data)
    prop.area_outdoor         = to_int(self.area_outdoor.data)
    prop.prop_state_id        = self.prop_state_id.data
    prop.appurtenance         = to_int(self.appurtenance.data)
    prop.balcony              = to_int(self.balcony.data)
    prop.doorman              = to_int(self.doorman.data)
    prop.elevator             = to_int(self.elevator.data)
    prop.fireplace            = to_int(self.fireplace.data)
    prop.furnished            = to_int(self.furnished.data)
    prop.garage               = to_int(self.garage.data)
    prop.garden               = to_int(self.garden.data)
    prop.grillroom            = to_int(self.grillroom.data)
    prop.gym                  = to_int(self.gym.data)
    prop.live_work            = to_int(self.live_work.data)
    prop.luxury               = to_int(self.luxury.data)
    prop.pool                 = to_int(self.pool.data)
    prop.terrace              = to_int(self.terrace.data)
    prop.washer_dryer         = to_int(self.washer_dryer.data)
    prop.sum                  = to_int(self.sum.data)
    prop.main_description     = self.main_description.data
    prop.country              = self.country.data
    prop.state                = self.state.data
    prop.city                 = self.city.data
    prop.neighborhood         = self.neighborhood.data
    prop.street_name          = self.street_name.data
    prop.street_number        = to_int(self.street_number.data)
    prop.floor_number         = self.floor_number.data
    prop.location             = self.location.data
    prop.agua_corriente       = to_int(self.agua_corriente.data)
    prop.gas_natural          = to_int(self.gas_natural.data)
    prop.gas_envasado         = to_int(self.gas_envasado.data)
    prop.luz                  = to_int(self.luz.data)
    prop.cloacas              = to_int(self.cloacas.data)
    prop.telefono             = to_int(self.telefono.data)
    prop.tv_cable             = to_int(self.tv_cable.data)
    prop.internet             = to_int(self.internet.data)
    prop.vigilancia           = to_int(self.vigilancia.data)
    prop.monitoreo            = to_int(self.monitoreo.data)
    
    #TODO: Sacar de donde va
    prop.prop_operation_state_id = to_int(self.prop_operation_state_id.data)
    prop.prop_owner_id           = 1

    prop.cardinal_direction     = self.cardinal_direction.data
    return prop
    
  def __init__(self, formdata=None, obj=None, **kwargs):
    super(PropertyForm, self).__init__(formdata=formdata, obj=obj, **kwargs)
    self.sell_yes.data = self.prop_operation_id.data != None and self.prop_operation_id.data & Property._OPER_SELL != 0 
    self.rent_yes.data = self.prop_operation_id.data != None and self.prop_operation_id.data & Property._OPER_RENT != 0
    
    # HACKU: de marku para que no aparezca 0 cuando es 'sin dato' en los enteros
    int_fileds = ['area_indoor', 'area_outdoor', 'rooms', 'bedrooms', 'bathrooms', 'building_floors', 'street_number']
    for int_filed in int_fileds:
      p = getattr(self, int_filed)
      if str(getattr(p,'data')) == '0':
        setattr(p,'data', '')

  # --- type.html
  prop_type_id        = SelectField(choices=[ (str(hex(i+1)[2:]), short_descs[i]) for i in range(0,len(short_descs)) ])
  prop_operation_id   = IntegerField('',[validators.required(message=u'Debe elegir al menos un tipo de operación')], default=0)
  
  price_sell_currency = SelectField(choices=[('ARS', '$'), ('USD', 'USD')])
  price_sell          = TextField()
  sell_yes            = BooleanField('Venta', id='op_' + str(Property._OPER_SELL))
  
  price_rent_currency = SelectField(choices=[('ARS', '$'), ('USD', 'USD')])
  price_rent          = TextField()
  rent_yes            = BooleanField('Alquiler', id='op_' + str(Property._OPER_RENT))
  price_expensas      = TextField()
    
  def validate_price_expensas(form, field):
    my_float_validator_simple(field)
    
  def validate_price_rent(form, field):
    my_float_validator(field, form.prop_operation_id.data & Property._OPER_RENT != 0)

  def validate_price_sell(form, field):
    my_float_validator(field, form.prop_operation_id.data & Property._OPER_SELL != 0)

  def validate_area_indoor(form, field):
    my_int_validator(field)
    
  def validate_area_outdoor(form, field):
    my_int_validator(field)

  def validate_rooms(form, field):
    my_int_validator(field)
  
  def validate_bedrooms(form, field):
    my_int_validator(field)
  
  def validate_bathrooms(form, field):
    my_int_validator(field)

  def validate_building_floors(form, field):
    my_int_validator(field)
  
  def validate_street_number(form, field):
    my_int_validator(field)
    
  # ---- features.html
  rooms           = TextField('Ambientes')
  bedrooms        = TextField('Dormitorios')
  bathrooms       = TextField('Toilettes')
  building_floors = TextField('Plantas/Pisos')
  
  year_built      = SelectField(u'Antigüedad'   , coerce=int, choices=[(0,'Sin Datos')]+[( features['year_built']['rangos'][i], features['year_built']['descriptions'][i]) for i in range(1, len(features['year_built']['rangos']))])
  area_indoor     = TextField('Superficie Cubierta', description=u'm²')
  area_outdoor    = TextField('Superficie Descubierta', description=u'm²')
  prop_state_id   = SelectField(u'Estado General' , coerce=int, choices=[(0,'Sin Datos')]+[( features['prop_state_id']['rangos'][i], features['prop_state_id']['descriptions'][i]) for i in range(1, len(features['prop_state_id']['rangos'])-1)])
  
  #cardinal_direction      =  SelectField(u'Orientación', choices=[(1, 'Norte'), (2, 'Noreste'), (3, 'Este'), (4, 'Sureste'), (5, 'Sur'), (6, 'Suroeste'), (7, 'Oeste'), (8, 'Noroeste')])
  cardinal_direction      =  SelectField(u'Orientación', choices=[('', 'No disponible'), ('Norte', 'Norte'), ('Noreste', 'Noreste'), ('Este', 'Este'), ('Sureste', 'Sureste'), ('Sur', 'Sur'), ('Suroeste', 'Suroeste'), ('Oeste', 'Oeste'), ('Noroeste', 'Noroeste')])
  
  prop_operation_state_id =  SelectField(u'Etiqueta' , coerce=int, choices=[(Property._OPER_STATE_NADA, '-ninguna-'),
      (Property._OPER_STATE_RESERVADO, 'Reservado'),
      (Property._OPER_STATE_SUSPENDIDO, 'Suspendido'),
      (Property._OPER_STATE_VENDIDO, 'Vendido'),
      (Property._OPER_STATE_ALQUILADO, 'Alquilado'),
      (Property._OPER_STATE_OPORTUNIDAD, 'Oportunidad'),
      (Property._OPER_STATE_DE_POZO, 'De pozo'),
      (Property._OPER_STATE_APTO_CREDITO, u'Apto Crédito'),
      (Property._OPER_STATE_IMPECABLE, 'Impecable'),
      (Property._OPER_STATE_INVERSION, u'Inversión')])
      
  
  # --- more_features.html
  appurtenance    = BooleanField('Dependencia')
  balcony         = BooleanField(u'Balcón')
  doorman         = BooleanField('Portero')
  elevator        = BooleanField('Ascensor')
  fireplace       = BooleanField('Estufa Hogar')
  furnished       = BooleanField('Amoblado')
  garage          = BooleanField('Garage')
  garden          = BooleanField('Parque')
  grillroom       = BooleanField('Parrilla')
  gym             = BooleanField('Gimnasio')
  live_work       = BooleanField('Apto Profesional')
  luxury          = BooleanField('Lujo')
  pool            = BooleanField('Piscina')
  terrace         = BooleanField('Terraza')
  washer_dryer    = BooleanField(u'Lavandería')
  sum             = BooleanField('SUM')
  
  main_description= TextAreaField(u'Descripción de la propiedad', [validators.optional(), validators.length(max=5120, message=u'La descripción debe ser como maximo %(max)s caracteres')])

  # --- location.html
  country         = TextField(u'País')
  state           = TextField(u'Región/Provincia')
  city            = TextField('Localidad')
  neighborhood    = TextField('Barrio')
  street_name     = TextField('Calle')
  street_number   = TextField('Altura', widget=MyTextInput())
  floor_number    = TextField('Piso/Dpto.', widget=MyTextInput())
  location        = GeoPtPropertyField()

  # --- services.html
  agua_corriente  = BooleanField('Agua corriente')
  gas_natural     = BooleanField('Gas natural')
  gas_envasado    = BooleanField('Gas envasado')
  luz             = BooleanField('Luz')
  cloacas         = BooleanField('Cloacas')
  telefono        = BooleanField(u'Teléfono')

  tv_cable        = BooleanField(u'Televisión por Cable')
  internet        = BooleanField('Internet')
  vigilancia      = BooleanField('Vigilancia privada')
  monitoreo       = BooleanField(u'Monitoreo electrónico')

class RealEstateForm(Form):
  def __repr__(self):
    return 'RealEstateForm'
  
  logo                = FileField('')
  name                = TextField('',[validators.Required(message=u'Debe ingresar un nombre de Inmobiliaria.')])
  email               = TextField('',[validators.email(message=u'Debe ingresar un correo válido.')
                                      , validators.Required(message=u'Debe ingresar un correo electrónico.')], default='')
  telephone_number    = TextField('')
  telephone_number2   = TextField('')
  open_at             = TextField('')
  
  def update_object(self, rs):
    rs.name               = self.name.data
    rs.email              = self.email.data
    rs.telephone_number   = self.telephone_number.data
    rs.telephone_number2  = self.telephone_number2.data
    rs.open_at            = self.open_at.data
    return rs
    

class RealEstateWebSiteForm(Form):
  def __repr__(self):
    return 'RealEstateWebSiteForm'
  
  website             = TextField('', default='')
  managed_domain      = BooleanField('')
  domain_id           = TextField('')
  tpl_title           = TextField('')
  tpl_text            = TextAreaField('')
  
  def validate_website(form, field):
    
    if field.data.strip() == '':
      return
    
    tld_part = ur'\.[a-z]{2,10}'
    if 'http://' in field.data:
      regex = ur'^[a-z]+://([^/:]+%s|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$' % tld_part
      mRegexp = regexp(regex, re.IGNORECASE, message=u'Dirección inválida.')
    else:
      regex = ur'([^/:]+%s|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$' % tld_part
      mRegexp = regexp(regex, re.IGNORECASE, message=u'Dirección inválida.')
    mRegexp.__call__(form, field)

  def validate_domain_id(form, field):
    res = validate_domain_id(field.data.strip(), form.thekey)
    if res['result'] == 'free':
      return
      
    raise ValidationError(res['msg'])
    
    
  def update_object(self, rs):
    rs.website                  = self.website.data
    if self.website.data.strip() != '' and 'http://' not in self.website.data:
      rs.website                  = 'http://'+self.website.data
    tmp_current_managed_domain  = rs.managed_domain
    rs.managed_domain           = to_int(self.managed_domain.data)
    rs.domain_id                = self.domain_id.data
    rs.tpl_title                = self.tpl_title.data
    rs.tpl_text                 = self.tpl_text.data
    
    return rs, (tmp_current_managed_domain!=rs.managed_domain)
    
    
class UserForm(Form):
  def __repr__(self):
    return 'UserForm'
  
  first_name          = TextField('',[validators.Required(message=u'Debe ingresar un nombre.')])
  last_name           = TextField('',[validators.Required(message=u'Debe ingresar un apellido.')])
  telephone_number    = TextField('')
  mobile_number       = TextField('',[validators.Required(message=u'Debe ingresar un número de celular.')])
  email               = TextField('',[validators.email(message=u'Debe ingresar un correo válido.')], default='')
  rol                 = SelectField(u'Rol' , choices=set([('owner', u'Dueño'), ('admin', 'Administrador'), ("oper", 'Operador')]), default='owner')
  gender              = SelectField(u'Género' , choices=set([('male', u'Masculino'), ('female', 'Femenino')]))
  birthday            = DateField('')
  key                 = TextField('')
  
  def update_object(self, user):
    user.first_name         = self.first_name.data
    user.last_name          = self.last_name.data
    user.telephone_number   = self.telephone_number.data
    user.mobile_number      = self.mobile_number.data
    user.email              = self.email.data
    user.rol                = self.rol.data
    #user.password           = self.password.data
    user.gender             = self.gender.data
    return user
  
  def validate_email(form, field):
    # Chequeo que el correo sea válido.
    user         = User.all().filter('email =', field.data).get()
    
    if user:
      if str(user.key()) == str(form.key.data):
        return
      raise ValidationError(u'Este correo ya esta siendo utilizado.')

class KetchupForm(Form):
  def __repr__(self):
    return 'KetchupForm'
  
  ketchup             = TextField('')
  inketchup           = TextField('')
  
  def validate_ketchup(form, field):
    if field.data is None:
      raise ValidationError(u'Hello droid.')
    if len(field.data)>0:
      raise ValidationError(u'Hello droid.')
  def validate_inketchup(form, field):
    if field.data is None or len(field.data)<1:
      raise ValidationError(u'Hello droid.')
    
    try:
      ms = int(field.data)
      if ms!=2:
        raise ValidationError(u'Hello droid.')
    except:
      raise ValidationError(u'Hello droid.')
      
class UserChangePasswordForm(Form):
  def __repr__(self):
    return 'UserChangePasswordForm'
  password            = PasswordField(u'Contraseña', [
                            validators.Length(message=u'La contraseña debe tener al menos %(min)d caracteres.', min=6),
                            validators.Required(message=u'Debe ingresar una contraseña.'),
                            validators.EqualTo('confirm', message=u'Las contraseñas deben ser iguales.'),
                        ])
  confirm             = PasswordField(u'Repita contraseña')
  
  def update_object(self, user):
    user.password           = self.password.data
    return user
    
class SignUpForm(KetchupForm):
  def __repr__(self):
    return 'SignUpForm'

  def validate_accept_terms(form, field):
    if not field.data:
      raise ValidationError(u'Debe aceptar los términos y condiciones.')
      
  def validate_email(form, field):
    # Chequeo que el correo no este repetido
    user        = User.all().filter('email =', field.data).get()
    
    #TODO: NO HAY INDICE PARA ESTO POR ESO NO SE PUEDE VALIDAR
    #realestate  = RealEstate.all().filter('email =', field.data).get()
    
    if user:
      raise ValidationError(u'Este correo ya esta siendo utilizado.')
  
  # def validate_name(form, field):
    # # Chequeo que el nombre de la inmo no este repetido
    # name = RealEstate.all().filter('name', field.data.strip()).get()
    # if name:
      # raise ValidationError(u'Ese nombre ya esta siendo utilizado.')
  
  # TODO: NO HAY INDICE PARA ESTO POR ESO NO SE PUEDE VALIDAR!!!!
  # def validate_telephone_number(form, field):
    # # Chequeo que el teléfono de la inmo no este repetido
    # name = RealEstate.all().filter('telephone_number', field.data.strip()).get()
    # if name:
      # raise ValidationError(u'Ese teléfono ya esta siendo utilizado.')

  # name                = TextField('',[validators.Required(message=u'Debe ingresar un nombre de Inmobiliaria.')])
  email               = TextField('',[validators.email(message=u'Debe ingresar un correo válido.')], default='')
  # telephone_number    = TextField('',[validators.Required(message=u'Debe ingresar un número de teléfono.')])
  password            = PasswordField(u'Contraseña', [
                            validators.Length(message=u'La contraseña debe tener al menos %(min)d caracteres.', min=6),
                            validators.Required(message=u'Debe ingresar una contraseña.'),
                            validators.EqualTo('confirm', message=u'Las contraseñas deben ser iguales.')
                        ])
  confirm             = PasswordField(u'Repita contraseña')
  accept_terms        = BooleanField('')
      
class PropertyContactForm(KetchupForm):
  def __repr__(self):
    return 'PropertyContactForm'
    
  name                = TextField('',[validators.Required(message=u'Debe ingresar un nombre.')])
  email               = TextField('',[validators.email(message=u'Debe ingresar un correo válido.')
                                      , validators.Required(message=u'Debe ingresar un correo.')], default='')
  message             = TextAreaField('',[validators.Required(message=u'Debe ingresar un mensaje.')], default='')
  telephone           = TextField('')
  
class HelpDeskForm(Form):
  def __repr__(self):
    return 'HelpDeskForm'
  
  sender_name               = TextField('',[validators.Required(message=u'Debe ingresar un nombre.')])
  sender_email              = TextField('',[validators.email(message=u'Debe ingresar un correo válido.')
                                      , validators.Required(message=u'Debe ingresar un correo.')], default='')
  sender_telephone          = TextField('')
  sender_subject            = TextField('', [validators.Required(message=u'Debe ingresar un Asunto.')])
  sender_comment            = TextAreaField('',[validators.Required(message=u'Debe ingresar un Comentario.')], default='')
  
  def update_object(self, help_desk):
    help_desk.sender_name       = self.sender_name.data
    help_desk.sender_email      = self.sender_email.data
    help_desk.sender_telephone  = self.sender_telephone.data  
    help_desk.sender_subject  = self.sender_subject.data
    help_desk.sender_comment  = self.sender_comment.data
    
    return help_desk
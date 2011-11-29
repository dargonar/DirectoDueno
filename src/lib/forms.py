# -*- coding: utf-8 -*-
#from tipfy.ext.wtforms import Form, fields
from wtforms import Form, BooleanField, SelectField, TextField, FloatField 
from wtforms import HiddenField, TextAreaField, IntegerField, validators, ValidationError


class EmailLinkForm(Form):
  email   = TextField('',[validators.email(message=u'Debe ingresar un email válido.')], default='')
  link    = HiddenField('') #,[validators.url(message=u'La URL no es válida.')], default='')

# class ContactForm(Form):
    # name = fields.TextField('Name')
    # email = fields.TextField('Email')
    # message = fields.TextAreaField('Message')
    # image = fields.FileField('Image')
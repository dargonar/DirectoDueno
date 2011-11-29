# -*- coding: utf-8 -*-
"""
    images handlers
    ~~~~~~~~
"""
from __future__ import with_statement
import logging
import urllib
import time

from datetime import datetime
from google.appengine.api import images, files, taskqueue
from google.appengine.ext import db, blobstore
from google.appengine.api.images import get_serving_url

from models import ImageFile, Property
from utils import need_auth, BackendHandler

from webapp2 import RequestHandler, Response
from webapp2_extras.securecookie import SecureCookieSerializer

class Reorder(BackendHandler):
  @need_auth(code=500)
  def post(self, **kwargs):
    keys = self.request.POST['keys'].split(',')
    
    to_save = []
    for i,fi in enumerate(ImageFile.get(keys)):
      fi.position = i+1
      
      # Verifico que sean mias las fotines por 'silas' hacker
      if not self.has_role('ultraadmin') and str(fi.realestate.key()) != self.get_realestate_key():
        self.abort(500)

      to_save.append(fi)
    
    db.save(to_save)
    property = self.mine_or_404(str(to_save[0].property.key()))
    property.main_image_url = to_save[0].title
    property.save(build_index=False)
    
    self.response.write('ok')


# Este es un handler global para retornar imagenes
# No necesita validacion de ningun tipo
# class Show(RequestHandler):
  # def render_img(self, data):
    # self.response.headers['Cache-Control'] = "public"
    # self.response.expires = datetime(2028,3,28)
    # self.response.write(data)
 
  # def original(self, **kwargs):
    # self.response.headers['Content-Type'] = "image/png"
    # img = images.Image(blob_key=kwargs['key'])
    # img.rotate(0)
    # self.render_img(img.execute_transforms(output_encoding=images.PNG))
    
  # def get(self, **kwargs):
    # self.response.headers['Content-Type'] = "image/jpg"
    # img = images.Image(blob_key=kwargs['key'])
    # img.resize(width=int(kwargs['width']), height=int(kwargs['height']))
    # self.render_img(img.execute_transforms())

class Remove(BackendHandler):
  @need_auth(code=500)
  def get(self, **kwargs):
    self.remove([kwargs['key']])
    self.response.write('ok')
  
  @need_auth(code=500)
  def post(self, **kwargs):
    keys = []
    for key in self.request.POST:
      keys.append(key)
    
    self.remove(keys)
    return self.redirect_to('property/images', key=kwargs['key'])

  def remove(self, keys):
    fimgs     = ImageFile.get(keys)
    key       = fimgs[0].property.key()
    property  = self.mine_or_404(str(key))
    
    # Get all blobkeys
    blobkeys = []
    for fimg in fimgs:
      
      # Verifico que sean mias las fotines por 'silas' hacker
      if not self.has_role('ultraadmin') and str(fimg.realestate.key()) != self.get_realestate_key():
        self.abort(500)

      blobkeys.append(fimg.file.key())

    # Delete fileimages
    db.delete(fimgs)
    
    # Delete blobs
    blobstore.delete(blobkeys)

    #Update images_count
    if property.images_count:
      property.images_count = property.images_count - len(blobkeys)
      if property.images_count > 0:
        fi = ImageFile.all().filter('property =',property.key()).order('position').get()
        property.main_image_url = fi.title if fi else None
      else:
        property.main_image_url = None
    else:
      property.images_count = 0
      property.main_image_url   = None
      
    result = property.save(build_index=False)
    if result != 'nones':
      taskqueue.add(url=self.url_for('property/update_index'), params={'key': str(property.key()),'action':result})
    

class Upload(BackendHandler):
  # Alto hack: El flash manda un post con el archivo pero no pone las cookies.
  # Usando el plugin de swfupload 'cookies' mete todas las cookies para el sitio 
  # como parametros de post normales (en el request.form), de ahi la sacamos y armamos 
  # La session con la secure cookie
  
  # @need_auth(code=500)
  def post(self, **kwargs):
    
    # Todo esto es para recuperar la session en funcion de un parametro del post 
    # que nos manda el flash swfupload
    cookie_name  = self.app.config['webapp2_extras.sessions']['cookie_name']
    secret_key   = self.app.config['webapp2_extras.sessions']['secret_key']
    raw_data     = str(self.request.POST[cookie_name])
    
    if raw_data[0] == "\"" and raw_data[-1] == "\"":
      raw_data = raw_data[1:][:-1]
    
    # ALTO HACK: no se por que carajo no funcion el urllib.unquote
    raw_data     = raw_data.decode('string_escape')
    self.session = SecureCookieSerializer(secret_key).deserialize(cookie_name, raw_data)
    
    # Hacemos lo que hacia el decorator
    if not self.is_logged:
      self.abort(500)
    
    property = self.mine_or_404(kwargs['key'])
  
    fs = self.request.POST['file']
    # Create the file
    file_name = files.blobstore.create(mime_type='image/jpg', _blobinfo_uploaded_filename=fs.filename)

    # Open the file and write to it
    img = images.Image(fs.file.getvalue())
    img.resize(width=800, height=600)

    with files.open(file_name, 'a') as f:
      f.write(img.execute_transforms(output_encoding=images.JPEG, quality=70))

    # Finalize the file. Do this before attempting to read it.
    files.finalize(file_name)

    # Get the file's blob key
    blob_key = files.blobstore.get_blob_key(file_name)

    # ------ BEGIN HACK -------- #
    # GAE BUG => http://code.google.com/p/googleappengine/issues/detail?id=5142
    for i in range(1,10):
      if not blob_key:
        time.sleep(0.05)
        blob_key = files.blobstore.get_blob_key(file_name)
      else:
        break
    
    if not blob_key:
      logging.error("no pude obtener el blob_key, hay un leak en el blobstore!")
      abort(500)
    # ------ END HACK -------- #
      
    imgfile = ImageFile()
    imgfile.title     = get_serving_url(blob_key)
    imgfile.file      = blob_key
    imgfile.filename  = fs.filename
    imgfile.realestate= property.realestate.key()
    imgfile.property  = db.Key(encoded=kwargs['key'])
    imgfile.put()
    
    #Update property
    if property.images_count:
      property.images_count = property.images_count + 1
    else:
      property.images_count = 1
      property.main_image_url   = imgfile.title
    
    result = property.save(build_index=False)
    # HACK: No mandamos a regenerar el PropertyIndex
    #if result != 'nones':
    #  taskqueue.add(url=self.url_for('property/update_index'), params={'key': str(property.key()),'action':result})
    
    return self.render_response('backend/includes/img_box.html', image=imgfile)
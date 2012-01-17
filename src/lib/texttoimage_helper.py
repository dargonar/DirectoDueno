# -*- coding: utf-8 -*-
import logging

from StringIO import StringIO
import random


from webapp2 import abort
from google.appengine.api import images, files, taskqueue
from google.appengine.ext import db, blobstore
from google.appengine.api.images import get_serving_url

#from utils import get_or_404
#from models import RealEstate

#def render_realestate_email_by_obj(realestate):
def render_text_into_blob(text):
  #text = realestate.email if realestate.email else ''
  
  from pybmp.bmpfont_arial_12 import font_data
  from pybmp.bmp import BitMap, Color
  
  bmp = BitMap( 250, 22, Color.WHITE )
  bmp.setFont(font_data)
  bmp.setPenColor( Color.BLACK.darken() )
  bmp.drawText(text, 4, 4)
  #bmp.drawLine( 0, 0, 10, 10)
  
  f = StringIO()
  f.write(bmp.getBitmap())
  f.flush()
  
  file_name = files.blobstore.create(mime_type='image/bmp', _blobinfo_uploaded_filename=str(random.randint(0,100000)))
  img = images.Image(image_data=f.getvalue())
  
  # img = images.Image.open(f)
  img.resize(width=250, height=22)
  myfile = files.open(file_name, 'a')
  myfile.write(img.execute_transforms(output_encoding=images.JPEG, quality=100))
  myfile.close()
  
  files.finalize(file_name)
  
  blob_key = files.blobstore.get_blob_key(file_name)
  
  for i in range(1,10):
    if not blob_key:
      time.sleep(0.05)
      blob_key = files.blobstore.get_blob_key(file_name)
    else:
      break
  
  if not blob_key:
    logging.error("no pude obtener el blob_key, hay un leak en el blobstore!")
    abort(500)
  
  return blob_key
  
  # realestate.email_image      = blob_key
  # realestate.email_image_url  = get_serving_url(blob_key)
  
  # realestate.save()
  
  return 0

# def render_realestate_email(realestate_key):
  
  # try:
    # obj = db.get(key)
    # if obj:
      # return render_realestate_email_by_obj(obj)
  # except db.BadKeyError, e:
    # # Falling through to raise the NotFound.
    # pass
  # abort(404)

# -*- coding: utf-8 -*-
import os, os.path, shutil
import sys

YUI_COMPRESSOR = 'yuicompress/yuicompressor-2.4.6.jar'

def compress(in_files, out_file, in_type='js', verbose=False,
             temp_file='.temp'):
    temp = open(temp_file, 'w')
    for f in in_files:
        fh = open(f)
        data = fh.read() + '\n'
        fh.close()

        temp.write(data)

        print ' + %s' % f
    temp.close()

    options = ['-o "%s"' % out_file,
               '--type %s' % in_type]

    if verbose:
        options.append('-v')

    os.system('java -jar "%s" %s "%s"' % (YUI_COMPRESSOR,
                                          ' '.join(options),
                                          temp_file))

    org_size = os.path.getsize(temp_file)
    new_size = os.path.getsize(out_file)

    print '=> %s' % out_file
    print 'Original: %.2f kB' % (org_size / 1024.0)
    print 'Compressed: %.2f kB' % (new_size / 1024.0)
    print 'Reduction: %.1f%%' % (float(org_size - new_size) / org_size * 100)
    print ''

    os.remove(temp_file)
    
SCRIPTS = {
      'be':[
        'src/static/js/jquery.min.js',
        'src/static/js/jquery-ui-1.8.7.custom.min.js',
        'src/static/js/jquery.addplaceholder.js',
        'src/static/js/swfupload.js',
        'src/static/js/plugins/swfupload.cookies.js',
        'src/static/js/jquery.ketchup.js',
        'src/static/js/jquery.listnav.pack-2.1.js',
        'src/static/js/jquery.lightbox-0.5.js',
        'src/static/js/backend.js',
      ],
      
      'fe':[
        'src/static/js/jquery-1.4.4.min.js',
        'src/static/js/jquery-ui-1.8.7.custom.min.js',
        'src/static/js/jquery.scrollTo-1.4.2-min.js',
        'src/static/js/jquery.fadeSliderToggle.js',
        'src/static/js/jquery.multilists.plugin.js',
        'src/static/js/jquery.ad-gallery.js',
        'src/static/js/utils.js',
        'src/static/js/number-functions.js',
        'src/static/js/jquery.addplaceholder.js',
        'src/static/js/_infobox_packed.js',
        'src/static/js/ZeroClipboard.js',
        'src/static/js/jquery.tools.min.js',
        'src/static/js/jquery.ketchup.js',
        'src/static/js/jquery.lightbox-0.5.js',
        'src/static/js/frontend.js',
      ] 
      
}

SCRIPTS_OUT_DEBUG = {'be':'backend-debug.js','fe':'frontend-debug.js'}

STYLESHEETS = {
    'be':[
      'src/static/css/common.css',
      'src/static/css/backend.css',
      'src/static/css/fb-buttons.css',
      'src/static/css/jquery.lightbox-0.5.css',
    ],
    
    'fe':[
      'src/static/css/jquery-ui-1.8.7.custom.css',
      'src/static/css/frontend.css',
      'src/static/css/common.css',
      'src/static/css/jquery.ad-gallery.css',
      'src/static/css/fb-buttons.css',
      'src/static/css/jquery.lightbox-0.5.css',
    ]
}

def main():

  if len(sys.argv) < 3:
    print 'compress.py version (be|fe|re)'
    return

  version = sys.argv[1]
  app     = sys.argv[2]
  
  if app != 'be' and app != 'fe':
    print 'compress.py version (be|fe)'
    return
  
  names = {'fe':'frontend','be':'backend'}

  SCRIPTS_OUT       = '%s.min-%s.js' % (names[app], version)
  STYLESHEETS_OUT   = '%s.min-%s.css' % (names[app], version)

  print 'Compressing %s JavaScript...' % names[app]
  compress(SCRIPTS[app], SCRIPTS_OUT, 'js', False, SCRIPTS_OUT_DEBUG[app])

  print 'Compressing %s CSS...' % names[app]
  compress(STYLESHEETS[app], STYLESHEETS_OUT, 'css')
  

if __name__ == '__main__':
  main()
# -*- coding: utf-8 -*-
"""WSGI app setup."""
import os
import sys

# Add lib as primary libraries directory, with fallback to lib/dist
# and optionally to lib/dist.zip, loaded using zipimport.
if 'lib' not in sys.path:
    # Add /lib as primary libraries directory, with fallback to /distlib
    # and optionally to distlib loaded using zipimport.
    sys.path[0:0] = ['lib', 'distlib', 'distlib.zip']

import webapp2

from config import config
from urls import get_rules

def enable_jinja2_debugging():
    """Enables blacklisted modules that help Jinja2 debugging."""
    if not debug:
        return
    from google.appengine.tools.dev_appserver import HardenedModulesHook
    HardenedModulesHook._WHITE_LIST_C_MODULES += ['_ctypes', 'gestalt']

# Corriendo en debug?
debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

fullver = os.environ.get('CURRENT_VERSION_ID', '1')

config['directodueno']['app_version_id'] = fullver
config['directodueno']['app_version']    = fullver[0:fullver.rfind('.')]

# Instanciamos la aplicacion.
app = webapp2.WSGIApplication(routes=get_rules(config), debug=debug, config=config)
enable_jinja2_debugging()

def main():
    app.run()

if __name__ == '__main__':
    main()

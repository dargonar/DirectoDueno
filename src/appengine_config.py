def webapp_add_wsgi_middleware(app):
    import sys
    if 'lib' not in sys.path:
        sys.path[0:0] = ['lib', 'distlib', 'distlib.zip']

    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    return app
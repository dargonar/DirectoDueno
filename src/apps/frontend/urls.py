# -*- coding: utf-8 -*-
from webapp2 import Route, RedirectHandler
from webapp2_extras.routes import PathPrefixRoute

def get_rules():
    """Returns a list of URL rules for the Hello, World! application.

    
    :return:
        A list of class:`tipfy.Rule` instances.
    """
    rules = [
    
      #-------------------------------URL HACKS VAN ACA----------------------------------------
      Route('/tsk/fix_images',      name='fiximages',      handler='apps.backend.hacks.FixImages'),
      Route('/tsk/fix_re',          name='fixre',          handler='apps.backend.hacks.FixRealEstates'),
      Route('/tsk/remove_re/<key>', name='removere',       handler='apps.backend.hacks.RemoveRealEstate'),
      Route('/tsk/fix_prop',        name='fixprop',        handler='apps.backend.hacks.FixProperty'),
      
      # Campaña lanzamiento
      Route('/tsk/start_engine_campaign', name='start_engine_campaign', handler='apps.backend.hacks.StartEngineCampaign'),
      
      # Hacko para EMI
      Route('/ver/<archivo>',         name='ver_archivo',         handler='apps.backend.hacks.VerArchivo'),
      
      # HACKO Unsubscribe campagna la plata
      Route('/unsubscribe/<email>',   name='unsubscribe',         handler='apps.backend.hacks.Unsubscribe'),
      #----------------------------------------------------------------------------------------
      
      Route('/',                                                    name='frontend/home',             handler='apps.frontend.home.Index'),
      
      Route('/mapa',                                                name='frontend/map',              handler='apps.frontend.map.Index'),
      
      Route('/inmobiliarias-la-plata',                              name='frontend/red',              handler='apps.frontend.home.Red'),

      Route('/terms',                                               name='frontend/terms',            handler='apps.frontend.home.Terms'),      
      
      Route('/mapa/<slug>/<key_name_or_id>',                        name='frontend/map/slug/key',     handler='apps.frontend.map.Index:slugged_link'),
      Route('/mapa/<realestate>',                                   name='frontend/map/realestate',   handler='apps.frontend.map.Index:realesate_filtered'),
      
      #Route('/link/copy',                                           name='frontend/link/copy',        handler='apps.frontend.link.ShortenLink'),
      Route('/link/copy',                                           name='frontend/link/copy',        handler='apps.frontend.link.ShortenLocalLink'),
      Route('/link/copy/sendmail',                                  name='frontend/link/sendmail',    handler='apps.frontend.link.EmailShortenedLink'),
      Route('/link/share/',                                         name='frontend/link/share',       handler='apps.frontend.link.SearchShare'),
      Route('/link/map/<bitly_hash>',                               name='frontend/link/map',         handler='apps.frontend.link.LoadSearchLink'),
      
      Route('/service/search',                                      name='frontend/search',           handler='apps.frontend.search.Search'),
      
      Route('/compare/<keys>/<oper>',                               name='compare',                   handler='apps.frontend.property_info.Compare'),
      Route('/<slug>/ficha-<key>/<oper>',                           name='frontend/ficha',            handler='apps.frontend.property_info.Ficha:full_page'),
      Route('/service/popup/<key>/<bubble_css>/<oper>',             name='frontend/property_popup',   handler='apps.frontend.property_info.PopUp'),
      Route('/service/ficha/<key>/<oper>',                          name='frontend/property_ficha',   handler='apps.frontend.property_info.Ficha'),
      Route('/service/ficha/email/<key>/<oper>',                    name='frontend/ficha/sendemail',  handler='apps.frontend.property_info.SendMail'),
    ]
    
    return rules

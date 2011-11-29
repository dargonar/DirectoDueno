var map = null;
var geocoder = new google.maps.Geocoder();
var marker = null;
var myProjectionHelperOverlay = null;
var markersArray = [];
var iconsArray = [];

var m_initializing = false;

var filter_ranges;

function is_array(input){
  return typeof(input)=='object'&&(input instanceof Array);
}

var is1024w_or_less = false;
var isMSIE7         = false; 

function init_index()
{
  filter_ranges = config_array['discrete_range_config'];

  //////// ACCORDION //////////
  jQuery( "#accordion" ).accordion({ autoHeight: false });
  jQuery(".tab_content").hide();
  jQuery("#sidebar ul.tabs li:first").addClass("active").show();
  jQuery("#sidebar .tab_content:first").show();

  if ( $.browser.msie ) 
  {
    if(parseInt($.browser.version, 7) )
    {
      isMSIE7 = true;
    }
  }
  
  if(screen.width<=1024)
  {
    is1024w_or_less=true;
    jQuery('body').addClass('w1024or_less');
  }
  
  initUI();
  if(preset!=null)
  {  
    loadPreset();
  }
  else
  {
    initMap();
  }
}

function loadPreset(){
  
  if(default_lat==null | default_lon==null)
    initMap();
  else
    autoGeolocate();
  
  if(preset!=null && jQuery.inArray( 'opened_ficha_keys', preset))
  {
    var opened_ficha_keys = preset['opened_ficha_keys'];
    if (opened_ficha_keys && typeof (opened_ficha_keys) == 'string' && opened_ficha_keys.length > 0)
    {
      var opened_ficha_keysArray = opened_ficha_keys.split(',');
      jQuery.each(opened_ficha_keysArray, function(index, value){
        if (value && typeof(value) == 'string' && value.length > 0)
          onShowFicha(null, value);
      });
    }
  }
}

function onPropTypeChanged(sender){
  
  m_initializing = true;
  var elementGroup          = jQuery(sender).attr('group_item'); //'#prop_type_id_groups .sub_options'
  
  var contenedores_a_desactivar = jQuery('#prop_type_id_groups div.sub_options[group!="'+elementGroup+'"]');
  contenedores_a_desactivar.removeClass('selected');
  
  var contenedor_a_activar = jQuery('#prop_type_id_groups div.sub_options[group="'+elementGroup+'"]');
  if(!jQuery(contenedor_a_activar).hasClass('selected'))
    jQuery(contenedor_a_activar).addClass('selected');
  
  var elementos_a_uncheck = jQuery('input[id*="prop_type_id"][group_item!="'+elementGroup+'"]:checked');
  elementos_a_uncheck.each(
    function(index, value){ 
      setTransCheckboxState(jQuery(value).attr('id'), false);
    }
  );
  m_initializing=false;
} 

function initUI() {
  onWindowResize();
  //jQuery('[jqtransform|=true]').jqTransform(); //lo llamo desde el html.
	//Checkboxes
  jQuery('#filters_bar [id*="prop_type_id"]').change(function(){ onPropTypeChanged(this);onMainFilterChange(this);});
  jQuery('#prop_operation_id').change(
    function(){
      if (jQuery('#prop_operation_id').val()==OPER_RENT)
        setPriceSliderOptions('price_slider', default_slider_max2, default_slider_step2, default_slider_min2, default_slider_max2);
      else 
        setPriceSliderOptions('price_slider', default_slider_max1, default_slider_step1, default_slider_min1, default_slider_max1);
      
      formatRangePriceText('price_display'
                              , jQuery( "#price_slider" ).slider( "option", "min")
                              , jQuery( "#price_slider" ).slider( "option", "max")
                              , jQuery('#currency').val()
                              , jQuery( "#price_slider" ).slider( "option", "max") );
      onMainFilterChange(this);
    }
  );
  
  if(jQuery('#prop_operation_id').val()==OPER_SELL && default_max_value>default_slider_max)
  { 
    default_min_value = $.inArray(default_min_value.toString(), sellPrices); //sellPrices.indexOf(default_min_value.toString());
    default_max_value = $.inArray(default_max_value.toString(), sellPrices); //sellPrices.indexOf(default_max_value.toString());
  }
  
  jQuery("#price_slider").slider({
    orientation: 'horizontal', min: default_slider_min, max: default_slider_max, range: true, step: default_slider_step, values: [default_min_value, default_max_value], 
    slide: function(event, ui) { 
        formatRangePriceText('price_display'
                              , getPriceValue(ui.values[0])
                              , getPriceValue(ui.values[1])
                              , jQuery('#currency').val()
                              , jQuery( "#price_slider" ).slider( "option", "max") );
      },
    change: function(event, ui) {
      onMainFilterChange(ui);
    }
  });
  
  formatRangePriceText('price_display'
                              , getPriceValue(default_min_value)
                              , getPriceValue(default_max_value)
                              , jQuery('#currency').val()
                              , jQuery( "#price_slider" ).slider( "option", "max") );
        
  jQuery.each(filter_ranges, function(key, value) { 
    var data = value;
    var display_obj = key+ '_display';
    var apply_obj   = key+'_apply';
    var slider_obj  = key+'_slider';
    var descriptions = data['descriptions'];
    var default_value=0;
    if(preset!=null && jQuery.inArray( key, preset)>-1)
      default_value = preset[key];
    jQuery("#"+slider_obj).slider({
      orientation: 'horizontal', min: 0, max: descriptions.length-1, range: false, step: 1, value: default_value,
      slide: function(event, ui) {
        var text = descriptions[ui.value];
        jQuery("#"+display_obj).html(text);
      }
    });
    var text = descriptions[parseInt(default_value)];
    jQuery("#"+ display_obj).html(text);
    
  });
  
  jQuery('#sort').change(function(){
    onMainFilterChange(this);
  });
  
  jQuery('#currency').change(function(){ 
      currency=(jQuery('#currency').val()=='ars'?'$':'US$');
      var values=jQuery("#price_slider").slider('values');
      formatRangePriceText('price_display'
                            , getPriceValue(values[0])
                            , getPriceValue(values[1])
                            , jQuery('#currency').val()
                            ,jQuery( "#price_slider" ).slider( "option", "max") );
      doSearch();
    }
  );
  
  if(is1024w_or_less)
  {
    var copy = $('#main_filter_options_form #filters_bar li.none').clone();
    $('#main_filter_options_form #filters_bar li.none').remove();
    copy.css('float','right');
    copy.find('a.link').css('margin-top','0px');
    jQuery('#copylink').removeClass('w1024plus');
    jQuery('#copylink').addClass('w1024less');
    // jQuery('#copylink').css('left','0px');
    // jQuery('#copylink').css('width','423px');
    // jQuery('#copylink').css('position','absolute');
    $('#sidebar .tabs').append(copy);
  }
  
  if(show_extended_filter==1)
    toggleFilter();
}


function initMap(){
  autoGeolocate();
  if(navigator.geolocation) {
    //triggerGeolocationAdvice();
    navigator.geolocation.getCurrentPosition(html5LocatePositionSuccess, html5LocatePositionError);
  }
  return false;  
}

/* ======================================================================== */
/* Geolocation overlay */
var geolocation_advice_timer = null;
function triggerGeolocationAdvice(){
  geolocation_advice_timer = setInterval(
    function() {
      stopGeolocationAdvice();
      showGeolocationAdvice();
    }
  , 5000);
}
function onGeolocationOverlayClose()
{
  stopGeolocationAdvice();
  jQuery('#geolocation_overlay').remove();
  jQuery('#geolocation_advice').remove();
}
function showGeolocationAdvice(){
  if(isMSIE7)
  {
    $('#geolocation_advice').removeClass('top').addClass('bottom');
  }
  $('#geolocation_overlay').overlay({
    mask: 'black',
    closeOnClick: false,
    load: true,
    top:'0px',
    left:'0px'
  });
  $('#geolocation_advice').show();
}
function stopGeolocationAdvice(){
  if(geolocation_advice_timer!=null)
    clearInterval(geolocation_advice_timer);
}
/* ======================================================================== */

/* GEOLOCATION */
function autoGeolocate(){
  if(default_lat==null || default_lon==null)
  {
    // CABA
    // default_lat=-34.6130;
    // default_lon=-58.4700;
    
    // La Plata
    default_lat=-34.92139;
    default_lon=-57.954683;
  }
  var myLatlng = new google.maps.LatLng(default_lat, default_lon);
  locateMap(myLatlng);
  initMapSearch();
}

function html5LocatePositionError(positionerror){
  // Ver http://dev.w3.org/geo/api/spec-source.html
  onGeolocationOverlayClose();
}

function html5LocatePositionSuccess(position) {
  // Ver http://dev.w3.org/geo/api/spec-source.html
  onGeolocationOverlayClose();
  var point = new google.maps.LatLng(position.coords.latitude, position.coords.longitude);
  map.setCenter(point);
  doSearch();
}

function locateMap(myLatlng)
{
  var myOptions = {
    zoom: default_zoom_level,
    center: myLatlng,
    mapTypeId: google.maps.MapTypeId.ROADMAP,
    panControl: false

  };
  onWindowResize();
  map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);
  
  //GEOCODER
  //geocoder = new google.maps.Geocoder();
  
  /* inicializo variables del mapa */
  myProjectionHelperOverlay = new ProjectionHelperOverlay(map);
  iconsArray['default'] = new google.maps.MarkerImage('/img/icons/map/icong.png',
      new google.maps.Size(18, 36), new google.maps.Point(0, 0), new google.maps.Point(8, 36)); 
  iconsArray['selected'] = new google.maps.MarkerImage('/img/icons/map/iconb.png', 
      new google.maps.Size(18, 36), new google.maps.Point(0, 0), new google.maps.Point(8, 36)); 
  iconsArray['shadow'] = new google.maps.MarkerImage('/img/icons/map/shadow.png',
      new google.maps.Size(33, 28), new google.maps.Point(0, 0), new google.maps.Point(0, 28)); 

  //Boton localizador
  $('#btnSearch').click( function() {
    var address = document.getElementById("searchmap").value;

    put_marker = true;
    geocoder.geocode({'address': address,'region' : 'ar'}, function(results, status){ 
    
      var handled = false;
      $.each(results, function(i, item) {
        if( is_from_country(item, 'Argentina') )
        {
          handle_result(item.geometry);
          handled = true;
          return false;
        }
      });
      
      if (status != google.maps.GeocoderStatus.OK || handled == false) 
      {
        showErrorMessageBox("Imposible ubicar dirección");
        return;
      }
    });
  });  

      
  jQuery("#searchmap").autocomplete({
      //This bit uses the geocoder to fetch address values
      source: function(request, response) {
        geocoder.geocode( {'address': request.term, 'region' : 'ar'}, function(results, status) {
          response(jQuery.map(results, function(item) {
              //Solo direcciones de argentina
              if( !is_from_country(item,'Argentina') )
                return null;

              return {
                    label: item.formatted_address,
                    value: item.formatted_address,
                    result: item
              };
          }));
        });
      },
      //This bit is executed upon selection of an address
      select: function(event, ui) {
        handle_result( ui.item.result.geometry ); 
      }
    });
    
    return false;
}

function handle_result(geometry)
{
  var location = new google.maps.LatLng(geometry.location.lat(), geometry.location.lng());
  //map.setCenter(location);
  var myOptions = {
    zoom: 15,
    center: location
  };
  map.setOptions(myOptions);
  //marker.setPosition(location);
  jQuery("#searchmap").attr('title', jQuery("#searchmap").val());
  doSearch(); // Hack: dado que no me cuelgo mas del boumds-changed del mapa!
}
      
function initMapSearch(){
  var g_initial_map_event = google.maps.event.addListener(map, 'bounds_changed', 
    function() {
      google.maps.event.removeListener(g_initial_map_event);
      doSearch();
  });
}
/* Document Resize Event & Functions */
jQuery(window).resize(function() {
  onWindowResize();
  //console.log(' Event window.resize.');
});

function headerHeight(){
      var a = jQuery("#header").outerHeight();
      var b = jQuery("#filters_bar").outerHeight();
      var c = 0;
      if(jQuery("#main_tabs").length>0 && jQuery("#main_tabs").is(':visible'))
        c =jQuery("#main_tabs").outerHeight();
      return a + b + c;  
  }
  
var map_size_changed = false;
function onWindowResize(){
  var a = jQuery(window).height(), b = jQuery(window).width();
  
  var extraWidth = 0;
  if(isMSIE7)
    extraWidth = 0; //340;
  
  jQuery('#map_container').css('width', (b - 340) + "px"); 
  jQuery('#map_container').css('height', (a - headerHeight()) + "px"); 
  
  //jQuery('#map_canvas').css('width', (b - 340 - 340 - extraWidth) + "px"); 
  jQuery('#map_canvas').css('width', (b - 340 ) + "px"); 
  
  var footerHeight = 0;
  if(jQuery('#foot_map').is(':visible'))
    footerHeight = 30;
  jQuery('#map_canvas').css('height', (a - headerHeight() - footerHeight) + "px"); 
  
  // var sidebar_h = jQuery(window).height() - jQuery("#header").outerHeight() - jQuery("#filters_bar").outerHeight() - jQuery("#r_actions_bar").outerHeight();
  jQuery('#sidebar').css('height', jQuery('#content').outerHeight());
  
  map_size_changed=true;
  
}

/* UI Events*/
function onMainFilterChange(obj)
{
  if(m_initializing)
    return false;
  checkFiltersOptions();
  doSearch();
  return false;
}

/* SEARCH */

var g_searchResults = null;
var g_searchResults_index = [];

var g_currentSearchXHR = null; // For cancelling current XHRs.
var g_searchOptions = {}; // Last options passed to doSearch.
var g_searchCenterMarker = null;

var g_mapAutoScrollInterval = null;
var g_programmaticPanning = false; // Temporary moveend disable switch.

var MIN_PROXIMITY_SEARCH_GEOCODE_ACCURACY = 6;

var MAX_PROXIMITY_SEARCH_MILES = 50;

function getPrev(){
  doSearch(-1);
}

function getNext(){
  doSearch(+1);
}

var cursorPosition = 0;
var cursorsArray = null;

function doSearch() {
  
  jQuery('#error').hide();
  showLoading();
  
  // Reseteo Cursor.
  if (arguments.length != 1)
  {
    cursorPosition = 0;
    cursorsArray = new Array();
    $('#btnMoreProps_next').attr('disabled','disabled');
    $('#btnMoreProps_prev').attr('disabled','disabled');
  }
  
  if(markers_coords!=null)
  {
    //do something
    load_json_result(markers_coords,0, false);
    markers_coords=null;
    getSearchParameters(null, null);
    hideLoading();
    enableSearchOnPan();
    return false;
  }
  
  if (g_currentSearchXHR && 'abort' in g_currentSearchXHR) {
    // console.log("doSearch:: ABORTED");
    g_currentSearchXHR.abort();
  }
  
  clearSearchResults();
  
  /* ==================================== */
  /* Manejo de Cursores                   */
  var cursor = new Array();
  var cursorStep = 0;
  if (arguments.length == 1)
  {
    cursorStep = arguments[0];
    if(cursorStep<0)
    { 
      cursor=cursorsArray[cursorPosition][cursorStep];
      cursorPosition=cursorPosition+cursorStep;
      cursorsArray.pop();
    }
    else
    {
      cursor=cursorsArray[cursorPosition][cursorStep];
      cursorPosition=cursorPosition+1;
    }
    // console.log('   Voy a mandar CURSOR ['+cursor+']');
  }
  
  /* ==================================== */
  
  searchParameters = getSearchParameters(cursor, cursorPosition);
  
  // Perform proximity or bounds search.
  g_currentSearchXHR = jQuery.ajax({
    url: '/service/search',
    type: 'get',
    data: searchParameters,
    dataType: 'json',
    error: function(jqXHR, textStatus, errorThrown) {
      return false;
    },
    success: function(obj) {
      g_currentSearchXHR = null;
      
      jQuery('#loading_sidebar').hide();
      
      load_json_result(obj, cursorStep, true);
      
    }
  });
  enableSearchOnPan();
}

function getSearchParameters(cursor, cursorPosition)
{
  var oldSearchOptions = g_searchOptions;
  
  var price_values = jQuery('#price_slider').slider('values');
  // Parametros por default
  var price_min = price_values[0];
  var price_max = price_values[1];
  
  if(jQuery('#prop_operation_id').val()==OPER_SELL)
  { 
    price_min = sellPrices[price_values[0]];
    price_max = sellPrices[price_values[1]];
  }
  
  var searchParameters = {
        query_type : 'bounds' // 'proximity'
        , extended_options:1
        , price_apply : 1
        , price_min: price_min
        , price_max: price_max 
        , sort: jQuery('#sort').val()
      };
  
  /* Le seteo la key de la RealEstate si es distinta del Null. */
  if(realestate_key!=null)
  {
    searchParameters =  updateObject(searchParameters, { realestate_key:realestate_key});
  }
  
  /* Manejo de Cursores. */
  if(cursor!=null)
  {
    searchParameters =  updateObject(searchParameters, { cursor:cursor, cursor_index:cursorPosition});
  }
  
  // Serializo los parametros en pantalla principal.
  var main_options = jQuery('#main_filter_options_form').serializeArray();
  
  // Formateo los parametros serializados de pantalla principal.
  var main_options_array = [];
  jQuery.each(main_options, function(i, main_option){
    main_options_array[main_option.name.replace('main_','')] = main_option.value;
  });

  // Updeteo el objeto master.
  searchParameters = updateObject(searchParameters, main_options_array);
  
  if (searchParameters.query_type == 'bounds') {
    var current_bounds = map.getBounds();
    if(!current_bounds)
    {
      return false;
    }
    searchParameters = updateObject(searchParameters, {
      north: current_bounds.getNorthEast().lat(),
      east: current_bounds.getNorthEast().lng(),
      south: current_bounds.getSouthWest().lat(),
      west: current_bounds.getSouthWest().lng(),
      max_results: MAX_BOUNDS_SEARCH_RESULTS
    });
  }
  
  searchParameters = updateObject(searchParameters,getMoreFilterOptions());  
  
  g_searchOptions = searchParameters;
  return searchParameters;
}
function load_json_result(obj, cursorStep, load_html){
  if (obj && obj.status && obj.status == 'success') {
    // Esto es para debug, muestro LatLon'g en cartel de error y si puedo lo copio al clipboard!
    
    if(jQuery('#meta_debug').length>0)
      jQuery('#meta_debug').append("<p>"+obj.the_box+"</p>");
    var cursorObject = obj.cursor;
    // console.log('   Recibi como "next" CURSOR ['+cursorObject+']');
    if(cursorObject!=null && cursorObject.length>0 && cursorObject!='None')
    {
      if(cursorStep>=0)
      {
        cursorObject = ((cursorObject=='None')?null:cursorObject);
        cursorsArray[cursorPosition]=new Array();
        cursorsArray[cursorPosition][1]=cursorObject;
        if(cursorsArray.length>2)
          cursorsArray[cursorPosition][-1]=cursorsArray[cursorPosition-2][1];
        else
          cursorsArray[cursorPosition][-1]=null;
      }
      $('#btnMoreProps_next').attr('disabled', ((cursorObject==null)?'disabled':''));
      $('#btnMoreProps_next').attr('title',((cursorObject==null)?'':'Ver página '+ (cursorPosition+2)));
    }
    else
    {
      $('#btnMoreProps_next').attr('disabled', 'disabled');
      $('#btnMoreProps_next').attr('title','');
    }
    
    if(cursorsArray!=null && cursorsArray.length>1)
    {
      $('#btnMoreProps_prev').attr('disabled', '');
      $('#btnMoreProps_prev').attr('title', 'Ver página '+cursorPosition);
    }
    else
    {
      $('#btnMoreProps_prev').attr('disabled', 'disabled');
      $('#btnMoreProps_prev').attr('title', '');
    }
    
    if(load_html)
    {
      jQuery('#prop_container').html(obj.html);
    }
    
    $('#tab_viewing_page').html(cursorPosition+1); // en tab1.html
    $('#tab_viewing_count').html(obj.display_viewing_count); // en tab1.html
    // $('#display_total_count').html(obj.display_total_count); // en map.html
    //$('#display_viewing_count').html(obj.display_viewing_count); // en map.html
            
    m_last_result_object = obj; 
    for (var i = 0; i < obj.coords.length; i++) {
      var coord = obj.coords[i];
      marker = createResultMarker(coord);
    }
    
    jQuery('#loading_map').hide();
  } 
  else 
  {
    jQuery('#loading_map').hide();
    jQuery('#loading_sidebar').hide();
  }
}
/**
 * Enables or disables search-on-pan, which performs new queries upon panning
 * of the map.
 * @param {Boolean} enable Set to true to enable, false to disable.
 */
var g_mapPanListener = null;
var g_mapZoomListener = null;
// var g_mapDragStartListener = null;
// var g_mapBoundChangedListener = null;
// var g_mapDragStarted = false;
function enableSearchOnPan(enable) {
  if (typeof(enable) == 'undefined')
    enable = true;
  
  if (!enable) {
    if (g_mapPanListener)
      google.maps.event.removeListener(g_mapPanListener);
    if(g_mapZoomListener!=null)
      google.maps.event.removeListener(g_mapZoomListener);
    // if(g_mapDragStartListener!=null)
      // google.maps.event.removeListener(g_mapDragStartListener);  
    // if(g_mapBoundChangedListener!=null)
      // google.maps.event.removeListener(g_mapBoundChangedListener);    
      
    // Kill all listeners
    g_mapPanListener = null;
    g_mapZoomListener=null;
    // g_mapDragStartListener=null;
    // g_mapBoundChangedListener=null;
  } else if (!g_mapPanListener) {
    g_mapZoomListener= google.maps.event.addListener(map, 'zoom_changed',
        function() {
          doSearch();
        });
    g_mapPanListener = google.maps.event.addListener(map, 'dragend',
        function() {
          // g_mapDragStarted = false;
          doSearch();
        });
    // g_mapDragStartListener = google.maps.event.addListener(map, 'dragstart',
        // function() {
          // g_mapDragStarted = true;
        // });
    // g_mapBoundChangedListener = google.maps.event.addListener(map, 'bounds_changed',
        // function() {
          // if (!g_mapDragStarted)
            // doSearch();
        // });
  }
}

var bubble_ib = null; 
var minibubble_ib = null; 
function createResultMarker(coord) {
  var resultLatLng = new google.maps.LatLng(coord.lat, coord.lng);
  
  var marker = new google.maps.Marker({
      position: resultLatLng,
      map:map,
      icon : iconsArray['default'],
      /*title: coord.headline,*/
      key: coord.key,
      flat: false,
      shadow:iconsArray['shadow'] ,
      visible:true
    
  });
  
  markersArray[coord.key]=marker;
  
  //markersArray.push(marker);
  google.maps.event.addListener(marker, 'click', (function(marker) {
    return function() { return onShowPopup(marker, marker, marker.key); }; 
  })(marker));
  
  google.maps.event.addListener(marker, 'mouseover', (function(marker) {
    return function() {  
      onMouseOverMarker(marker); 
      return onListedPropertyIsHover(marker.key);
    }; 
  })(marker));
  
  google.maps.event.addListener(marker, 'mouseout', (function(marker) {
    return function() { 
      onMouseOutMarker(marker); 
      return onListedPropertyIsNotHover(marker.key);
    }; 
  })(marker));
        
  var prop = jQuery('#prop_box_'+marker.key);
  return marker;
}


var myLastSelectedMarker = null;
function onShowPopup(sender, marker, key){
  if(!g_mapPanListener)
  {
    showTabWindow(sender, key);
    return false;
  }
  
  showLoading();
  
  var scrollToListItem = false;
  if(marker==null)
  {
    marker = markersArray[key];
  }
  else
  {
    scrollToListItem = true;
  }
  var bubbleData = computeMarkerPosition(marker, BIG_BUBBLE);
  
  jQuery.ajax({
    url: '/service/popup/'+marker.key+'/'+bubbleData[0]+'/'+jQuery('#prop_operation_id').val(),
    type: 'get',
    error: function(jqXHR, textStatus, errorThrown) {
      hideLoading();
      return false;
    },
    success: function(data){
      var infoHtml = data;
      showInfoBox('bubble_ib', marker, infoHtml, "391px", bubbleData[1], BIG_BUBBLE);
      if(!scrollToListItem)
      { 
        hideLoading();
        return false;
      }
      try{
        jQuery('#prop_container').scrollTo(jQuery('[key|='+key+']'), 800 );
      }
      catch(err){}
      hideLoading();
      return false;
    } 
  });  
  return false;
}

function showInfoBox(m_ib_desc, marker, infoHtml, width, mMapPixelOffset, bubble_type)
{
  var myOptions = {
             content: infoHtml, disableAutoPan:true, maxWidth:0, pixelOffset: mMapPixelOffset, zIndex: 1
            ,boxStyle:{width: width, height:'auto', cursor:'pointer'}
            ,closeBoxMargin: "4px 0px 0px 0px", closeBoxURL: "/img/pixel-transp.gif"
            ,infoBoxClearance: new google.maps.Size(1, 1), isHidden: false
            ,enableEventPropagation:(bubble_type==SMALL_BUBBLE)
            ,pane: "floatPane"};
  
  var m_ib = bubble_ib;
  if(m_ib_desc=='minibubble_ib') 
  {
    if(minibubble_ib!=null) 
    {  
      minibubble_ib.close();
      minibubble_ib=null;
    }
  }  
  else
  {
    if(minibubble_ib!=null)
    {
      minibubble_ib.close();
      minibubble_ib = null;
    }
    if(bubble_ib!=null) 
    {
      bubble_ib.close();
      bubble_ib = null;
    }
  }
  m_ib = new InfoBox(myOptions);                
  m_ib.open(map, marker);
  
  if(m_ib_desc=='bubble_ib') 
  {
    if(myLastSelectedMarker!=null)
    {
      myLastSelectedMarker.setIcon(iconsArray['default']);
    }
    marker.setIcon(iconsArray['selected']);
    myLastSelectedMarker = marker;
    jQuery('#prop_container .prop_box.active').removeClass('active');
    jQuery('#prop_container [key|='+marker.key+']').find('.prop_box').addClass('active');
    bubble_ib = m_ib;
    return false;
  }
  
  minibubble_ib = m_ib;
  return false;
}
function onMouseOverProp(key){
  if(!g_mapPanListener)
    return false;
  marker = markersArray[key];
  return onMouseOverMarker(marker);
}
function onMouseOutProp(key){
  marker = markersArray[key];
  return onMouseOutMarker(marker);
}

function onMouseOverMarker(marker){
  if(bubble_ib!=null)
    return false;
  var infoHtml = jQuery("#prop_mini_bubble_"+marker.key).html();
  /* Esto del compute marker position lo voy a tener que sacary meter en el infobox */
  var bubble_data = computeMarkerPosition(marker, SMALL_BUBBLE);
  infoHtml = infoHtml.replace(/bubble_css/g,bubble_data[0]);
  showInfoBox('minibubble_ib', marker, infoHtml, "222px", bubble_data[1], SMALL_BUBBLE);
  return false;
}
function onMouseOutMarker(marker){
  
  if(minibubble_ib==null)
  {
    return false;
  }
  minibubble_ib.close();
  minibubble_ib = null;
  
  if(marker!=null)
    marker.setIcon(iconsArray['default']);
  return false;
}

var SMALL_BUBBLE = 1;
var BIG_BUBBLE = 2;
function computeMarkerPosition(marker, bubble_size){
  var point = myProjectionHelperOverlay.getPixelPoint(marker.getPosition());
  var theWidth = jQuery('#map_container').width();
  var theHeight = jQuery('#map_container').height();
  theWidth = theWidth/2;
  theHeight = theHeight/2;
  
  var bubble_css = '';
  if(point.x >= theWidth)
  {  
    if(point.y <= theHeight ) 
    { bubble_css = 'left_bottom';}
    else  
    { bubble_css = 'left_top';}
  }
  else
  {  
    if(point.y <= theHeight ) 
    {  bubble_css = 'right_bottom';}
    else 
    {  bubble_css = 'right_top';}
  }
  var position = bubble_css;
  var gMapsPixelOffset = null;
  if(position=='left_bottom')
  {  
    if(bubble_size==SMALL_BUBBLE)
    {  gMapsPixelOffset = new google.maps.Size(-214, -5.5);}
    else
      {gMapsPixelOffset = new google.maps.Size(-351, -29);}
  }
  else if(position=='right_bottom')
  {  
    if(bubble_size==SMALL_BUBBLE)
    {  gMapsPixelOffset = new google.maps.Size(11, -5.5);}
    else
    {  gMapsPixelOffset = new google.maps.Size(24, -29);}
  }
  else if(position=='left_top')
  {  
    if(bubble_size==SMALL_BUBBLE)
    {  gMapsPixelOffset = new google.maps.Size(-214, -74.5);}
    else
    {  gMapsPixelOffset = new google.maps.Size(-351, -303);}
  }
  else if(position=='right_top')
  {  
    if(bubble_size==SMALL_BUBBLE)
    {  gMapsPixelOffset = new google.maps.Size(11, -74.5);}
    else
    {  gMapsPixelOffset = new google.maps.Size(24, -303);}
  }  
  return [bubble_css, gMapsPixelOffset];
}

function onShowPopupClosed(marker){
  if(marker!=null)
    marker.setIcon(iconsArray['default']);
  jQuery('#prop_container .prop_box.active').removeClass('active');
  return false;
}

function updateObject(dest, src) {
  dest = dest || {};
  src = src || {};
  
  for (var k in src)
  {
    dest[k] = src[k];
  }
  
  return dest;
}

function clearSearchResults() {
  closeBubbles();
  for (i in markersArray) {
    markersArray[i].setMap(null);
  }
  jQuery('#prop_container').html('');
  myLastSelectedMarker = null;
  markersArray=[];
}

/* EVENT Handlers*/
function closeBubble()
{
  if(bubble_ib==null)
    return false;
  onShowPopupClosed(myLastSelectedMarker);
  bubble_ib.close();
  bubble_ib=null;
  return false;
}

function closeBubbles()
{
  // jQuery('#bubble').fadeOut('slow', function() { jQuery('#bubble').remove();return false;	});
  closeBubble();
  if(minibubble_ib!=null)
  {  
    minibubble_ib.close();
    minibubble_ib=null;
  }
  return false;
}

 /**@private 
   * In V3 it is quite hard to gain access to Projection and Panes. 
   * This is a helper class 
   * @param {google.maps.Map} map 
   */ 
  function ProjectionHelperOverlay(map) { 
    this.setMap(map); 
  } 
  
  ProjectionHelperOverlay.prototype = new google.maps.OverlayView(); 
  
  ProjectionHelperOverlay.prototype.draw = function () { 
    if (!this.ready) { 
      this.ready = true; 
      google.maps.event.trigger(this, 'ready'); 
    } 
  }; 
  
  ProjectionHelperOverlay.prototype.getPixelPoint = function (coord) { 
    var projection;
    try
    {
      projection = this.getProjection();
    }
    catch(err)
    {
      projection = this.getProjection();
    }
    if(typeof projection !== 'undefined' && projection !== null && projection != null)
    { 
      var point = projection.fromLatLngToContainerPixel(coord);
      return point;
    }
    return null;
  };
  /* End Projection Overlay */
  
  function getImage(direction)
  {
    if( $(".popupimg").length == 0 )
      return false;
      
    var visible = $(".popupimg:visible").hide();
    
    var prox = direction > 0 ? visible.next() : visible.prev();
    if( prox.length == 0 ) prox = direction > 0 ? $(".popupimg:first") : prox = $(".popupimg:last");
    
    prox.show();
    visible.hide();

    $('.qty>font').text( prox.attr('id').substring(6) );
    
    return false;
  }
  
  //////// SHOW FILTERBOX //////////
  function toggleFilter()
  {
    if(jQuery('#btnFilters').hasClass("hide"))
      return hideFilter();
    return showFilter();
  }
  
  function showFilter() {
      jQuery("#searchbox").addClass("filters");
      jQuery("#filterbox").show();
      jQuery('#btnFilters').addClass("hide");
      return false;
    }
  function hideFilter() {
    jQuery("#searchbox").removeClass("filters");
    jQuery("#filterbox").hide();
    jQuery('#btnFilters').removeClass("hide");
    return false;	
  } 
  
  function removeProperty(key){
    var marker = markersArray[key];
    marker.setMap(null);
    jQuery('#prop_container [key|='+key+']').remove();
  }
  
  function applyFilterOptions(){
    toggleFilter();
    checkFiltersOptions();
    doSearch();
  }
  
  function checkFiltersOptions(){
    var selectedItems = getMoreFilterOptions();
    //console.log(selectedItems);
    if(!jQuery.isEmptyObject(selectedItems))
      jQuery('#btnFilters').addClass('selected');
    else
      jQuery('#btnFilters').removeClass('selected');
  }
  
  function getMoreFilterOptions() {
    
    var my_options = jQuery('#box-options-form').serializeArray();
    var my_options_array = [];
    jQuery.each(my_options, function(i, my_option){
      my_options_array[my_option.name] = my_option.value;
    });

    jQuery.each(filter_ranges, function(key, value) { 
      var slider_obj  = key+'_slider';
      var value_obj = jQuery('#'+slider_obj).slider('value');
      if(value_obj>0)
      {
        my_options_array[key] = jQuery('#'+slider_obj).slider('value');
      }
    });
    
    return my_options_array;
  }

  function setTransCheckboxState(input_id, checked)
  {
    var relative_main_id = '#'+input_id;
    var relative_main_alink_id = '#alink_'+input_id;
    if(checked==true)
    {
      jQuery(relative_main_id).attr('checked', 'checked');
      // jQuery(relative_main_alink_id).addClass('jqTransformChecked');
    }
    else
    {
      jQuery(relative_main_id).removeAttr("checked");
      // jQuery(relative_main_alink_id).removeClass('jqTransformChecked');
    }
  }
  
/* =========================================================================== */
/* TABS Carousel: esta funcion activa los botones y el carousel para los tabs. */
/* En template frontend/templates/win_tabs.html hay que mostrar los botones de */
/*  y hay que modificar el width del estilo "body.frontend_search ul.wintabs"  */ 
/*  en frontend css con width=10000px;                                         */
function checkTabNavButtons(){
  
  if($(".main_tabs").hasClass('carouselfied'))
    return false;
    
  $(".main_tabs").jCarouselLite({
      btnNext: "#next",
      btnPrev: "#prev",
      mouseWheel: true,
      circular: false
  });
  
  $(".main_tabs").addClass('carouselfied');
  return false;
  
}
/* =========================================================================== */
function getRule(){
	var tmp = document.styleSheets;
	if (tmp) 
  {		
    for (var i=0;i<tmp.length;i++) {			
      if (tmp[i].href!=null)
      {
        if (tmp[i].href.indexOf('mapa_tabs') != -1) 
        {				
          return tmp[i];				
          break;			
        }
      }
    }	
  }
}

var rules = null;
var containerTabsWidth = null;
var defaultTabWidth = 150;
var currentTabWidth = 150;
function calculateWinTabsVisibility(){
  if(rules==null)
  {  
    var rule = getRule();
    rules=rule['rules'];
    if(rules == null || typeof(rules) == 'undefined' || !rules)
      rules=rule['cssRules'];
  }
  if(containerTabsWidth==null)
    containerTabsWidth = jQuery('#main_tabs .wintabs').innerWidth();
  
  var totalAddressDivInnerWidth     = 0;
  var totalTabsDivWidth             = 0;
  var countAddressDiv               = jQuery('#main_tabs .wintabs li.resizable').length;
  
  jQuery('#main_tabs .wintabs li.resizable').each(
    function(index, value)
    {
      var addressDiv                = $(value);
      totalAddressDivInnerWidth     += addressDiv.find('.address').innerWidth();
      totalTabsDivWidth             += addressDiv.innerWidth();
    }
  );
  
  var diff = totalTabsDivWidth-(containerTabsWidth-jQuery('#main_tabs .wintabs li.non_resizable').innerWidth());
  if(diff>0)
  {
    var dx = currentTabWidth-Math.ceil(parseFloat(diff/countAddressDiv))-5;
    currentTabWidth = dx;
    rules[0].style['width'] = dx + 'px';
    return false;
  }
  else
  {
    var dx = currentTabWidth + Math.ceil(parseFloat(Math.abs(diff)/countAddressDiv)) - 6;
    if(dx<defaultTabWidth)
    {
      currentTabWidth = dx;
      rules[0].style['width'] = dx + 'px';
    }
    else
    {
      setWinTabsDefault();
    }
  }
}

function setWinTabsDefault(){
  currentTabWidth = defaultTabWidth;
  rules[0].style['width']=defaultTabWidth+'px';
}


/* COMPARE Functions */
function getNextImage(key, direction)
  {
    if( $("#comparebox_"+key+" .thumblnk").length == 0 )
      return false;
      
    var visible = $("#comparebox_"+key+" .thumblnk:visible").hide();
    
    var prox = direction > 0 ? visible.next() : visible.prev();
    if( prox.length == 0 ) prox = direction > 0 ? $("#comparebox_"+key+" .thumblnk:first") : prox = $("#comparebox_"+key+" .thumblnk:last");
    
    prox.show();
    visible.hide();

    $("#comparebox_"+key+" .qty>font").text( prox.attr('id').substring(6) );
    
    return false;
  }
function closeCompareTabWindow(sender, key){
  jQuery('#tab_compare_'+key).remove();
  jQuery('#tab_compare_content_'+key).remove();
  selectTabMap(null);
  return false;
  // closeTabWindow(sender, key) -> chequear si quedan fichas y si es necesario cerrarlas y dejar mapa en full-state.
}
function showCompareTabWindow(sender, key){
  hideCurrentTab();
  jQuery('#tab_compare_content_'+key).show();
  jQuery('#tab_compare_'+key).addClass('active');
  
}

function onShowCompare(){
  var checkeds = jQuery('#prop_container input.chk:checked');
  
  if(checkeds.length<2)
  {
    showErrorMessageBox('Debe seleccionar al menos 2 propiedades del listado.');
    return false;
  }
    
  var winTabs = jQuery('#main_tabs');
  if(!winTabs.is(':visible'))
  {
    enableSearchOnPan(false);
    jQuery('#foot_map').hide();
    winTabs.show();
  }
  
  var props    = '';
  checkeds.each(
    function(index, value)
    {
      props+=jQuery(value).attr('key')+',';
    }
  );
  
  // Obtengo comparacion.
  jQuery.ajax({
    url: '/compare/'+props+'/'+jQuery('#prop_operation_id').val()
    , type: 'get'
    , error: function(jqXHR, textStatus, errorThrown) {
      showErrorMessageBox(jqXHR.responseText);
      return false;
    }
    , success: function(data){
      var tab = data.tab;
      var compare = data.compare;
      hideCurrentTab();
      
      jQuery('#main_tabs .wintabs').append(tab);
      jQuery('#tabs_container').append(compare);
      
      closeBubbles();
      
      calculateWinTabsVisibility();
      
      return false;
    } 
  });
  return false;
}
      
function onShowFicha(sender, key)
{
  // HACK: para debuggear la apertura de tabs -> comentar las dos lineas siguientes.
  if(jQuery('#ficha_'+key).length>0)
    return showTabWindow(null, key);
  
  showLoading();
  
  var winTabs = jQuery('#main_tabs');
  if(!winTabs.is(':visible'))
  {
    enableSearchOnPan(false);
    jQuery('#foot_map').hide();
    winTabs.show();
  }
  
  // Obtengo ficha de propiedad
  jQuery.ajax({
    url: '/service/ficha/'+key+'/'+jQuery('#prop_operation_id').val()
    , type: 'get'
    , error: function(jqXHR, textStatus, errorThrown) {
      hideLoading();
      showErrorMessageBox(jqXHR.responseText);
      return false;
    }
    , success: function(data){
      var tab = data.tab;
      var ficha = data.ficha;
      hideCurrentTab();
      
      jQuery('#main_tabs .wintabs').append(tab);
      jQuery('#tabs_container').append(ficha);
      
      var newFichaId = '#ficha_'+key;
     
      doKetchup(newFichaId+' form');

      var iNoPhoto = jQuery(newFichaId+' li.nophoto').length;
      var galleries = jQuery(newFichaId).find('.ad-gallery').adGallery();
      $(newFichaId+' #switch-effect').change(
        function() {
          galleries[0].settings.effect = $(this).val();
          return false;
        }
      );
      
      //Hackeo si no tiene fotos (oculto).
      if(iNoPhoto>0)
      {
        jQuery('div.ad-thumbs').css('display', 'none');
      }
      
      jQuery(newFichaId+' input[placeholder]').addPlaceholder({ 'class': 'hint'}); 
      
      closeBubbles();
      
      calculateWinTabsVisibility();
      
      try{
        jQuery('#prop_container').scrollTo(jQuery('[key|='+key+']'), 800 );
      }
      catch(err)
      {}
      onListedPropertyIsActive(key);
      
      hideLoading();
      return false;
    } 
  });
  return false;
  
}

function selectTabMap(sender)
{
  hideCurrentTab();
  onListedPropertyRemoveStyles();
  jQuery('#map_tab').addClass('active');
  jQuery('#map_tab_content').show();
  
  if (map!=null && map_size_changed)
  { 
    map_size_changed=false;
    google.maps.event.trigger(map, 'resize');
  }
  
  if(jQuery('#main_tabs .wintabs li.resizable').length>=1)
  {
    // console.log('selectTabMap: hay liss');
    enableSearchOnPan(true);
    return false;
  }
  
  var winTabs = jQuery('#main_tabs');
  if(!winTabs.is(':visible'))
  {
    enableSearchOnPan(true);
    return false;
  }
  
  winTabs.hide();
  jQuery('#foot_map').show();
  
  setWinTabsDefault();
  enableSearchOnPan(true);
  
  return false;
  
}

function hideCurrentTab(){
  if(jQuery('#main_tabs .wintabs li.active').length<=0)
  {  
    return false;
  }
  var selectedTab = jQuery('#main_tabs .wintabs li.active');
  jQuery('#'+selectedTab.attr('window')).hide();
  selectedTab.removeClass('active');
  return false;
}

function showTabWindow(sender, key){
  showLoading();
  enableSearchOnPan(false);
  hideCurrentTab();
  var newTab = jQuery('#tab_'+key);
  jQuery('#'+newTab.attr('window')).show();
  newTab.addClass('active');
  closeBubbles();
  hideLoading();
  
  jQuery('#prop_container').scrollTo(jQuery('[key|='+key+']'), 800 );
  onListedPropertyIsActive(key);

  return false;
}


function closeTabWindow(sender, key)
{
  var next = jQuery('#main_tabs .wintabs #tab_'+key+' + li.resizable').next();
  jQuery('#tab_'+key).remove();
  jQuery('#ficha_'+key).remove();
  if(next.length>0)
  {
    calculateWinTabsVisibility();
    showTabWindow(null, next.attr('key'));
    return false;
  }
  selectTabMap(null);
  return false;
}

/* ========================================= */
/* Acrive/Hover Property On Sidebar List Activator */
function onListedPropertyIsHover(key){
  return onListedPropertySetStyle(key, 'hover');
}

function onListedPropertyIsActive(key){
  return onListedPropertySetStyle(key, 'active');
}

function onListedPropertySetStyle(key, style){
  onListedPropertyRemoveStyle(null, style);
  var a_activar =jQuery('.prop_content li.prop_box[id=prop_box_'+key+']');
  !a_activar.hasClass(style) && a_activar.addClass(style);
  return false;
}

function onListedPropertyIsNotHover(key){
  return onListedPropertyRemoveStyle(key, 'hover');
}

function onListedPropertyIsNotActive(key){
  return onListedPropertyRemoveStyle(key, 'active');
}

function onListedPropertyRemoveStyle(key, style){
  var a_desactivar = null;
  if(key!=null)
    a_desactivar = jQuery('.prop_content li.prop_box.'+style+'[id=prop_box_'+key+']');
  else
    a_desactivar = jQuery('.prop_content li.prop_box.'+style);
  a_desactivar.length>0 && a_desactivar.removeClass(style); 
  return false;
}

function onListedPropertyRemoveStyles(){
  onListedPropertyRemoveStyle(null, 'hover');
  onListedPropertyRemoveStyle(null, 'active');
  return false;
}
/* ========================================= */

/* ======================================= */
/* Loading Indicator                       */
function showLoading(){
  jQuery('#loading_map').show(); 
  jQuery('#loading_sidebar').show();
}

function hideLoading(){
  jQuery('#loading_map').hide(); 
  jQuery('#loading_sidebar').hide();
}
/* ======================================= */

/* ======================================= */
/* LINK copy */
function copyLink(){
  
  showLoading();
  var tabs    = '';
  jQuery('#main_tabs .wintabs [id*="tab_"][key]').each(
    function(index, value)
    {
      tabs+=jQuery(value).attr('key')+',';
    }
  );
  var params  = updateObject(g_searchOptions, { opened_ficha_keys:  tabs });
  params      = updateObject(g_searchOptions, { zoom_level:         map.getZoom() });
  params      = updateObject(g_searchOptions, { currency:           jQuery('#currency').val() });
  
  g_currentSearchXHR = jQuery.ajax({
    url: '/link/copy',
    type: 'get',
    data: params,
    error: function(jqXHR, textStatus, errorThrown) {
      hideLoading();
      jQuery('#copylink').hide();
      showErrorMessageBox(jqXHR.responseText);
      return false;
    },
    success: function(obj) {
      g_currentSearchXHR = null;
      jQuery('#copied_link').val(obj.bitly);
      jQuery('#copied_link2').val(obj.bitly);
      jQuery('#copylink').show();
      if (clip==null)
      {
        clip = new ZeroClipboard.Client();
        clip.glue('copier_button');
        clip.setHandCursor( true );
        clip.addEventListener( 'onComplete', onCopyLinkComplete );
      }
      clip.setText(obj.bitly);
      
      jQuery('#emailer_button').unbind();
      jQuery('#emailer_button').click(
        function(){
          showLoading();
          jQuery.ajax({
            url: '/link/copy/sendmail',
            type: 'post',
            data: jQuery('#share_link_by_mail').serialize(),
            error: function(jqXHR, textStatus, errorThrown) {
              hideLoading();
              jQuery('#copylink').hide();
              showErrorMessageBox(jqXHR.responseText);
              return false;
            },
            success: function(obj) {
              hideLoading();
              jQuery('#copylink').hide();
              showOkMessageBox(obj);
            }
        });
      });
      hideLoading();
      return false;
    }
  });
  return false;
}

/* Link copy Object. ZeroClipboard client*/
var clip = null;

function onCopyLinkComplete( client, text ) {
  jQuery('#copylink').hide();
  var msg = 'El enlace "'+text+'" fue copiado con éxito al portapapeles.';
  return showOkMessageBox(msg);
}

/* Messaging */
var msgbox_interval;
function showOkMessageBox(msg){
  return showMessageBox(msg, false);
}
function showErrorMessageBox(msg){
  return showMessageBox(msg, true);
}
function showMessageBox(msg, is_error ){
  jQuery('#message_content').html(msg);
  if(is_error)
    jQuery('#messagebox').addClass('error');
  else
    jQuery('#messagebox').removeClass('error');
  jQuery('#messagebox').slideDown('slow', function() {});
  msgbox_interval = setInterval(
            function() { 
                clearInterval(msgbox_interval); 
                jQuery('#messagebox').slideUp('slow', function() {});
              }
            , 4000);
  return false;
}

/* ================================================ */
/* HTML Ficha Help functions                        */
function scrollFichaToBottom(obj_id){
  jQuery('#'+obj_id).animate({ scrollTop: $('#'+obj_id).attr('scrollHeight') }, 3000); 
  return false;
}

function sendMail(form){
  
  var params = updateObject(g_searchOptions, { zoom_level:         map.getZoom(),
                                               currency:           jQuery('#currency').val()});
  
  jQuery.each(jQuery(form).serializeArray(), function(i, field){
    params[field.name] = field.value;
  });
  
  var url          = jQuery(form).attr('action');
  
  showLoading();
  jQuery.ajax({
      url:    url,
      type:   'get',
      data:   params,
      error:  function(jqXHR, textStatus, errorThrown) {
                hideLoading();
                showErrorMessageBox(jqXHR.responseText);
                return false;
              },
      success: function(obj) {
                hideLoading();
                showOkMessageBox(obj);
                return false;
              }
  });
  return false;
}
/* ================================================ */
// --- funciones de  Home.js ---
/* ================================================ */
function init_home()
{
  // jQuery('[jqtransform|=true]').jqTransform(); // en _base.html.
  
  jQuery("#price_slider").slider({
    orientation: 'horizontal', min: default_slider_min, max: default_slider_max, range: true, step: default_slider_step, values: [default_slider_min, default_slider_max], 
    slide: function(event, ui) { 
        formatRangePriceText('price_display'
                              , getPriceValue(ui.values[0])
                              , getPriceValue(ui.values[1])
                              , 'ars'
                              ,jQuery( "#price_slider" ).slider( "option", "max") );
      },
    change: function(event, ui) {
      formatRangePriceText('price_display'
                            , getPriceValue(ui.values[0])
                            , getPriceValue(ui.values[1])
                            , 'ars'
                            ,jQuery( "#price_slider" ).slider( "option", "max") );
    }
  });
  formatRangePriceText('price_display'
                      , getPriceValue(jQuery("#price_slider").slider( "option", "values" )[0])
                      , getPriceValue(jQuery("#price_slider").slider( "option", "values" )[1])
                      , 'ars'
                      ,jQuery( "#price_slider" ).slider( "option", "max") );
  
  function handle_result_home(location)
  {
      jQuery('#center_lat').val(location.lat());
      jQuery('#center_lon').val(location.lng());
  }
  
  jQuery("#btnSearchHome").click( function() {
    checkForm();
    
    //TODO: Unificar -> Esta funcion esta en backend/frontend x 2 (home e index)
    var address = document.getElementById("searchmap").value;

    put_marker = true;
    geocoder.geocode({'address': address,'region' : 'ar'}, function(results, status){ 
    
      var handled = false;
      $.each(results, function(i, item) {
        if( is_from_country(item, 'Argentina') )
        {
          handle_result_home(item.geometry.location);
          handled = true;
          return false;
        }
      });
      
      // if (status != google.maps.GeocoderStatus.OK || handled == false) 
      // {
        // return false;
      // }
      
      $('#home_search_form').submit();
    });
  });
  
  jQuery("#searchmap").autocomplete({
    source: function(request, response) {
      geocoder.geocode( {'address': request.term, 'region' : 'ar'}, function(results, status) {
        response(jQuery.map(results, function(item) {
            //Solo direcciones de argentina
            if( !is_from_country(item,'Argentina') )
              return null;

            return {
                  label: item.formatted_address,
                  value: item.formatted_address,
                  result: item
            };
        }));
      })
    },
    select: function(event, ui) {
      handle_result_home(ui.item.result.geometry.location);
    }
  }); 
  
  $('#prop_operation_id_container input[type="radio"]').change(function(){
    if ($(this).attr('id') == 'prop_operation_id2' && $(this).is(':checked'))
    {
      $('#prop_operation_id').val(OPER_RENT);
      setPriceSliderOptions('price_slider', default_slider_max2, default_slider_step2, default_slider_min2, default_slider_max2);
    }
    else 
    if ($(this).attr('id') == 'prop_operation_id1' && $(this).is(':checked'))
    {
      $('#prop_operation_id').val(OPER_SELL);
      setPriceSliderOptions('price_slider', default_slider_max1, default_slider_step1, default_slider_min1, default_slider_max1);
    }
  });
  
  jQuery('input[placeholder]').addPlaceholder({ 'class': 'hint'}); //{dotextarea:false, class:hint}
}

function checkForm()
{
  var priceValues = getPriceValues(); // funcion en utils.js
  jQuery('#price_min').val(priceValues[0]);
  jQuery('#price_max').val(priceValues[1]);
  return true;
}

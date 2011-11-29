//--------------------------------
//  INIT COMUN PARA TODAS BACKEND 
//--------------------------------
var paymentadvice_interval = null;
jQuery(document).ready(function() {
  jQuery('input[placeholder]').addPlaceholder({ 'class': 'hint'});
  if(jQuery('#realestate_disabled_close').length>0)
  {
    paymentadvice_interval = setInterval(
      function() { 
            clearInterval(paymentadvice_interval); 
            jQuery('#realestate_disabled_close').click();
          }
      , 5000);
  }
});

//----------------------------------
// FUNCIONES COMUNES
//----------------------------------
function check_pass_pair()
{
  jQuery('#password').keyup(function(){
    var pwd_len = jQuery('#password').val().length;
    var textos = ['Muy bajo', 'Bajo', 'Regular', 'Alto', 'Muy alto'];
    var pwd_index = 1;
    if(pwd_len>6)
    {
      if (pwd_len>=7&pwd_len<=8)
        pwd_index = 2;
      else if (pwd_len>=9&pwd_len<=10)
        pwd_index = 3;
      else if (pwd_len>=11&pwd_len<=12)
        pwd_index = 4;
      else if (pwd_len>=13)
        pwd_index = 5;
    }
    jQuery('div.progressbar.password p').html(textos[pwd_index-1]);
    jQuery('div.progressbar.password div.point').removeClass('level1').removeClass('level2').removeClass('level3').removeClass('level4').removeClass('level5').addClass('level'+pwd_index);
    checkPasswords();
    return true;
  });
  
  jQuery('#confirm_password').keyup(function(){checkPasswords();return true;});
}

function checkPasswords()
{
  if(jQuery('#confirm_password').val()!=jQuery('#password').val())
  {
    jQuery('#password_unequal').show();
    return false;
  }
  jQuery('#password_unequal').hide();
}

function bytesToSize(bytes, precision)
{  
    var kilobyte = 1024;
    var megabyte = kilobyte * 1024;
    var gigabyte = megabyte * 1024;
    var terabyte = gigabyte * 1024;
   
    if ((bytes >= 0) && (bytes < kilobyte)) {
        return bytes + ' B';
 
    } else if ((bytes >= kilobyte) && (bytes < megabyte)) {
        return (bytes / kilobyte).toFixed(precision) + ' KB';
 
    } else if ((bytes >= megabyte) && (bytes < gigabyte)) {
        return (bytes / megabyte).toFixed(precision) + ' MB';
 
    } else if ((bytes >= gigabyte) && (bytes < terabyte)) {
        return (bytes / gigabyte).toFixed(precision) + ' GB';
 
    } else if (bytes >= terabyte) {
        return (bytes / terabyte).toFixed(precision) + ' TB';
 
    } else {
        return bytes + ' B';
    }
}

//----------------------------------
// PROPERTY->FORM
//---------------------------------- 
var map;
var marker;
var geocoder;
var put_marker;

function map_initialize() {
  geocoder = new google.maps.Geocoder();
  var latlng;
  var zoom = 18;
  if( $('#location').val() != '')
  {
    var parts = $('#location').val().split(',');
    latlng = new google.maps.LatLng(parts[0], parts[1]);
  }
  else
  {
    // LatLong del centro de laplata
    latlng = new google.maps.LatLng(-34.921267,-57.954597);
    //$('#location').val(latlng.lat() + ',' + latlng.lng());
    zoom = 15;
  }
  
  var myOptions = {
    zoom: zoom,
    center: latlng,
    mapTypeId: google.maps.MapTypeId.ROADMAP
  };
  
  map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);
  
  //if( $('#location').val() != '')
  //{
  put_marker_at(latlng);
  //}
}
 
function loadScript() {
  var script = document.createElement("script");
  script.type = "text/javascript";
  script.src = "http://maps.google.com/maps/api/js?sensor=false&callback=map_initialize&language=es";
  document.body.appendChild(script);
}

function handle_result(result, status, latlong)
{
  $('#searchmap').val(result.formatted_address);
  
  //Limpiamos y actualizamos actualizamos campos del form
  $('form#registerform>dl.form.x2col').find('input').val('');

  if( latlong == null )
  {
    $('#location').val(result.geometry.location.lat() + ',' + result.geometry.location.lng());
  }
  else
  {
    $('#location').val(latlong.lat() + ',' + latlong.lng());
  }
            
  for(var r in result.address_components)
  {
    var x = result.address_components[r];
    if( x.types[0] == 'street_number' )
    {
      var parts = x.short_name.split('-');
      $('#street_number').val(parts[0]);
    }
    if( x.types[0] == 'route' )
      $('#street_name').val(x.long_name);
    if( x.types[0] == 'administrative_area_level_1' )
      $('#state').val(x.long_name);
    if( x.types[0] == 'locality' )
      $('#city').val(x.long_name);
    if( x.types[0] == 'country' )
      $('#country').val(x.long_name);
    if( x.types[0] == 'neighborhood' )
      $('#neighborhood').val(x.long_name);
  }
        
  if( put_marker )
  {
    map.setCenter(result.geometry.location);
    put_marker_at(result.geometry.location);
  }
}

function put_marker_at(position)
{
    if( marker ) 
      marker.setMap(null);
    
    marker = new google.maps.Marker({
        map: map, 
        position: position,
        draggable: true
    });

    google.maps.event.addListener(marker, 'dragend', function() {
      put_marker = false;
      geocoder.geocode({latLng:marker.getPosition()}, function(results, status) { 
        //alert('tengo geocode result:' + marker.getPosition() + ' - ' + results[0].geometry.location );
        handle_result(results[0], status, marker.getPosition() ); 
      });
    });
}

function is_from_country(item, country)
{
  //Solo direcciones de argentina
  for(var i=0; i<item.address_components.length; i++)
  {
    var acomp = item.address_components[i];
    if( acomp.types[0] == 'country' && acomp.long_name.toUpperCase() == country.toUpperCase())
      return true;
  }
  
  return false;
}

  
function init_new_property()
{
  //Cargamos maps api
  loadScript();
  
  //Pone estilo 'Selected' cuando marcan checkbox y limpia errores <p>
  $(".typebox input[type=checkbox]").click( function() {
    var typebox = $(this).parents('.typebox:first');
    $(typebox).toggleClass('selected'); //, this.checked);

    var op = $(this).parents('dd.operation:first');
    op.removeClass('errorbox');
    op.find('p.error').remove();
  });
  
  //Auto checkea el box cuando hay precio
  $("#price_rent").keyup(function(event){
    chk = $('input[name=rent_yes]');
    if( ($(this).val() != '' && chk.is(':checked') == false) ||
        ($(this).val() == '' && chk.is(':checked') == true ) )
      chk.trigger('click'); 
  });
  
  $("#price_sell").keyup(function(event){
    chk = $('input[name=sell_yes]');
    if( ($(this).val() != '' && chk.is(':checked') == false) ||
        ($(this).val() == '' && chk.is(':checked') == true ) )
      chk.trigger('click'); 
  });
 
  $("#description").focus( function() {
    $(this).removeClass('errorbox');
  });
  
  //Boton localizador
  $('#btnSearch2').click( function() {
    var address = document.getElementById("searchmap").value;

    put_marker = true;
    geocoder.geocode({'address': address,'region' : 'ar'}, function(results, status){ 
    
      var handled = false;
      $.each(results, function(i, item) {
        if( is_from_country(item, 'Argentina') )
        {
          handle_result(item, status, null);
          handled = true;
          return false;
        }
      });
      
      if (status != google.maps.GeocoderStatus.OK || handled == false) 
      {
        alert("Imposible ubicar dirección, intente 'altura calle,ciudad'");
        return;
      }
      
    });
  });  

  //Autocomplete textbox
  $("#searchmap").autocomplete({
    source: function(request, response) {
      geocoder.geocode( {'address': request.term, 'region' : 'ar'}, function(results, status) {
        response($.map(results, function(item) {
                  
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
    select: function(event, ui) {
      put_marker = true;
      handle_result(ui.item.result, google.maps.GeocoderStatus.OK, null);
    }
  });   

  //No submit cuando enter en el campo de busqueda
  $("#searchmap").keydown(function(event){
    if(event.keyCode == 13) {
      event.preventDefault();
      return false;
    }
  });
  
  $("#toimages").click( function(e) {
    $("input[name=goto]").val('go');
  });
  
  //Boton de maximizar
  $('#btnMaximize').toggle(function() {
    $('#location_box').addClass('fullsize');
    $(this).removeClass('maximize');
    $(this).addClass('minimize');
    $('#map_canvas').css('width',$('#location_box').width()+'px').css('height',$('#location_box').height()-$('#location_box .location_head').innerHeight()+'px');
    google.maps.event.trigger(map, 'resize');
  }, function() {
    $('#location_box').removeClass('fullsize');
    $(this).removeClass('minimize');
    $(this).addClass('maximize');
    $('#map_canvas').css('width','740px').css('height','300px');
    google.maps.event.trigger(map, 'resize');
    map.setCenter(marker.getPosition());
  });
  
  $('#new_property_form').submit(function() {
    //recalculate operation
    var val=0;
    $(".typebox input[type=checkbox]:checked").each( function(i, field) {
      var tmp = field.id.split('_');
      val |= parseInt( tmp[1] );
    });
    $("#prop_operation_id").val(val);
    return true;
  });
    
}

//----------------------------------
//         PROPERTY->IMAGES
//---------------------------------- 
var swfu      = null;
var changed   = false;
var working   = false;
var dragging  = false;
var saved_order;

function get_images_order()
{
  var tmp = Array();
  $("#masterpic>li").each( function(i, field) {
    tmp.push( $(field).attr('key') );
  });
  return tmp;
}

function update_percent(el, percent)
{
  $(el).find('div.point').width(percent);
  $(el).find('td.percent').html(percent);
}

function img_loaded_callback(img)
{
  if( $(img).attr('src') == $(img).attr('orig') )
    return false;
  
  $(img).attr('src', $(img).attr('orig'));
}

function bind_pic_boxes()
{
  //Borrar imagen
  $('.btnClose').unbind('click');
  $('.btnClose').click( function() {
    $(this).parent().find(".confirm").show();
  });
  
  //Borrar imagen [NO]
  $('a.no').unbind('click');
  $('a.no').click( function() {
    $(this).parent().parent().hide();
  });
  
  //Borrar imagen [YES]
  $('a.yes').unbind('click');
  $('a.yes').click( function() {
    var div = $(this).parent().parent();
    var img = div.parent().find('div>img.propImg');
    var oldimg = img.attr('orig');
    img.attr('src', '/img/ajax-loader.gif');
    div.parent().find('.btnClose').hide();
    div.hide();
    
    $.ajax({
      url:  img.attr('delme'),
      type: "GET",
      success: function(res) {
        div.parent().fadeOut("slow", function() {
          $(this).remove();
          if( $('#masterpic>li').length < 2 && $('#drag_msg').is(':visible') )
            $('#drag_msg').fadeOut("slow");
        });
      },
      error: function(xml, txt, err) {
        div.parent().find('.btnClose').show();
        img.attr('src', oldimg);
      } 
    }); 
  });
  
  //Click en imagen
  $('.propImg').unbind('click');
  $('.propImg').click( function() {
    if( dragging ) 
      return false;
    $(this).parents('li').find('input[type=checkbox]').each( function(i, field) {
      if( $(field).attr('checked') )
        $(field).attr('checked', false);
      else
        $(field).attr('checked', 'checked');
    });
  });
}

function init_pictures(bulk_remove_url, img_reorder_url, img_upload_url)
{
  //Tomamos el orden inicial de las imagenes
  saved_order = get_images_order();

  $('#selectall').click( function(e) {
    e.preventDefault();
    if ( working ) return false;
    $('input[type=checkbox]').attr('checked', 'checked');
  });  
  
  $('#deselectall').click( function(e) {
    e.preventDefault();
    if ( working ) return false;
    $('input[type=checkbox]').attr('checked', false);
  });
  
  $('#delselected').click( function(e) {
    e.preventDefault();
    if ( working ) return false;
    working = true;
    
    if( $("input:checked").length && confirm('Esta seguro que quiere borrar las imagenes seleccionadas?') == true )
    {
      var li = $('input:checked').parent().parent().parent();
      li.find('.propImg').attr('src','/img/ajax-loader.gif');

      var was_disabled = $('#reorder').hasClass('disable');
      $('a.uibutton').addClass('disable');

      function restore_del()
      {
        working = false;
        $('a.uibutton').removeClass('disable');
        if(was_disabled) $('#reorder').addClass('disable');
      }
      
      $.ajax({
        url:  bulk_remove_url,
        type: "POST",
        data: $('form').serialize(),
        success: function(res) {
          $("input:checked").parent().parent().parent().fadeOut("slow", function() {
            $(this).remove();
          });
          restore_del();
          if( $('#masterpic>li').length < 2 && $('#drag_msg').is(':visible') )
            $('#drag_msg').fadeOut("slow");
        },
        error: function(xml, txt, err) {
          li.find('.propImg').attr('src','/img/ajax-loader.gif');
          restore_del();
          alert('error');
        } 
      }); 
    }
    
    working = false;
  });  

  $('#reorder').click( function(e) {
    e.preventDefault();
    
    if( working || !changed ) 
      return false;
    
    working = true;
    $("#masterpic").sortable("option", "disabled", working);
    
    $('a.uibutton').addClass('disable');
    
    var new_order = get_images_order();
    $('#wait').show();

    function reenable()
    {
      $('a.uibutton').removeClass('disable');
      $('#wait').hide();
      working = false;
      $("#masterpic").sortable("option", "disabled", working);
    }
    
    $.ajax({
      url:  img_reorder_url,
      type: "POST",
      data: {keys:new_order.join(',')},
      success: function(res) {
        reenable();
        saved_order = new_order;
        changed     = false;
        $('#reorder').addClass('disable');
        $("#masterpic").css('background-color','#FF5');
        $("#masterpic").animate({'background-color': '#FFF'},3000);
      },
      error: function(xml, txt, err) {
        reenable();
        alert('error');
      } 
    });
  });

  bind_pic_boxes();
  
  $("#masterpic").sortable({
    revert: true,
    start: function(event, ui) { 
      dragging = true;
    },
    stop: function(event, ui) { 
      changed = false;
      $("#masterpic>li").each( function(i, field) {
        if( saved_order[i] != $(field).attr('key') )
        {
          changed = true;
          return !changed;
        }
      });
      
      if( changed )
        $('#reorder').removeClass('disable');
        
      dragging = false;
    }
  });
	
  $( "ul, li" ).disableSelection();

  swfu = new SWFUpload({
    file_post_name         : "file",
    flash_url              : "/js/swfupload.swf",
    upload_url             : img_upload_url,
    file_size_limit        : "10 MB",
    file_types             : "*.jpg;*.png",
    file_types_description : "Archivos de imágenes",
    file_upload_limit      : 30,
    file_queue_limit       : 0,
    prevent_swf_caching    : false,
    debug                  : false,

    button_image_url       : "/img/backgrounds/btnupload.png",
    button_width           : "167",
    button_height          : "40",
    button_placeholder_id  : "addphoto",
    
    swfupload_load_failed_handler : function() { 
      //TODO: poner lo que nos de emo
      alert('error cargando flash');
    },
    
    file_queued_handler           : function(file) {
      var el = $('#masterrow').clone().appendTo('#filelist');
      $(el).find(".filename").html(file.name);
      $(el).find(".size").html(bytesToSize(file.size));
      $(el).attr('id',file.id);
      $(el).show();      
    },
    
    file_queue_error_handler      : function(file, errorCode, message) {
      alert('error:' + errorCode + '->' + message);
    },
    
    file_dialog_complete_handler  : function(numFilesSelected, numFilesQueued) {
      if( numFilesSelected > 0 ) {
        $("#uploader").show();
        this.startUpload();
      }
    },
    
    upload_progress_handler       : function(file, bytesLoaded, bytesTotal) {
      var percent = Math.ceil((bytesLoaded / bytesTotal) * 100);
      update_percent('#' + file.id, percent + '%');
    },
    
		upload_error_handler          : function(file, errorCode, message){
      alert('error:' + errorCode + '->' + message);
    },
    
    upload_success_handler        : function(file, serverData) {
      update_percent('#' + file.id, '100%');
      if(serverData)
      {
        $('div.noelement').remove();
        
        $('#' + file.id).fadeOut("slow", function() {
            $(this).remove();
            
            if ( $('#filelist>tr').length == 1 )
              $("#uploader").hide();
        });
        
        $('#masterpic').append(serverData);
        bind_pic_boxes();
        
        if( $('#masterpic>li').length > 1 && !$('#drag_msg').is(':visible') )
          $('#drag_msg').fadeIn("slow");
      }
      this.startUpload();
    },
    
    upload_complete_handler       : function(file) {
      //alert('cuando se llama esto??');
    }
  });
  
  if( $('#masterpic>li').length > 1 ) 
    $('#drag_msg').show();
}

//----------------------------------
//         PROPERTY->LIST
//---------------------------------- 
function init_property_list(property_new_url)
{
  $('#prop_operation_id').change( function(e) {
    var hide = $('#prop_operation_id').val() != 0;
    
    $('#cosas').toggle(hide);
  });
  
  $('#fake_sort').change( function(e) {
    $('#sort').val( $('#fake_sort').val() );
    $('form#filter').submit();
  });
  
  $('#apply').click( function(e) {
    $('form#filter').submit();
  });
  
  $('#prop_type, #currency, #rooms, #area_indoor, #status, #realestate_network').change( function(e) {
    $('form#filter').submit();
  });
  
  $('#nprop').click( function(e) {
    window.location = property_new_url;
  });
  
  $('a.selall, a.dselall').click( function(e) {
    var on = $(this).hasClass('selall');
    $('input[type=checkbox].chkprop').each( function(i,field) {
      $(field).attr('checked', on ? 'checked' : false);
      //$('#alink_' + field.id).toggleClass('jqTransformChecked', on);
    })
    return false;
  });
  
  $('a.delsel, a.ressel').click( function(e) {
    var sel = 'input[type=checkbox].chkprop:checked';
    var del = $(this).hasClass('delsel');
    var question = 'Esta seguro que desea ' + ( del ? 'borrar' : 'recuperar') + ' estas propiedades?';
    if ( $(sel).length && confirm(question) )
    {
      //_NOT_PUBLISHED = 2
      //_DELETED       = 3
      $('#newstatus').val( del ? 3 : 2);
      $('form#remove').submit();
    }
    return false;
  });
  
  $('a.restorer').click( function(e) {
    e.preventDefault();
    if( confirm('Esta seguro que desea recuperar esta propiedad? Aparecera como NO publicada.') )
    {
      $(this).addClass('disable');
      var link = $(this);
      $.ajax({
        url:  $(this).attr('href'),
        type: "GET",
        success: function(res) {
          link.parent().parent().fadeOut("slow", function() {
            $(this).remove();
          });
        },
        error: function(xml, txt, err) {
          alert('error');
          $(this).removeClass('disable');
        } 
      }); 
    }
    
    return false;
  });
  
  $('a.publisher').click( function(e) {
    e.preventDefault();
    var status = $(this).attr('published');
    var action = status == 1 ? 'desactivar' : 'publicar';
    
    var explain;

    if( action == 'desactivar' )
      explain = 'La propiedad no sera visible en las busquedas de los usuario.';
    else
      explain = 'La propiedad sera visible en las busquedas de los usuarios.';
    
    var question = 'Esta seguro que desea ' + action + ' esta propiedad?';
    
    if( confirm(explain+question) )
    {
      $(this).addClass('disable');
      var link = $(this);
      $.ajax({
        url:  $(this).attr('href'),
        type: "GET",
        success: function(res) {
          link.parent().parent().fadeOut("slow", function() {
            $(this).remove();
          });
        },
        error: function(xml, txt, err) {
          alert('error');
          $(this).removeClass('disable');
        } 
      }); 
    }
    return false;
  });
}

//----------------------------------
//         PROFILE->REALESTATE
//---------------------------------- 
function init_realestate()
{
  //////// ADD NEW PHONE //////////
  $("#btnAddPhone").click(function()
    {	
      $('#phone2').slideDown('slow', function() {
      // Animation complete.
    });
    return false;
  });
  
  $("#btnDeletePhone").click(function()
   {	
    $('#phone2').slideUp('slow', function() {
      // Animation complete.
    });
    return false;
  });
  
  $('#form_logo_input').change( function() {
    var tmp = $(this).val();
    var inx = tmp.lastIndexOf('\\') + 1;
    $('#filename').html(tmp.substr(inx));
    $('div.filename').show();
  });
  
  $("#goto_website").click( function(e) {
    $("input[name=goto]").val('website');
  });
  
}
//----------------------------------
//         PROFILE->REALESTATE WEBSITE
//---------------------------------- 
function init_realestate_website(didurl){
  //Validar slug de domain id
  $('#validate_domain_id').click( function() {
    
    $(this).addClass('disable');
    
    $.ajax({
      url:  didurl,
      type: "GET",
      data: {did:$('#domain_id').val()},
      success: function(res) {
        $('#validate_domain_id').removeClass('disable');
        if(res.result=='free')
        {
          $('#did_dd>p').attr('class','ok');
          $('#did_dd').attr('class',false);
          alert('El nombre se encuentra disponible. Puede utilizarlo.');
        }
        else
        {
          $('#did_dd>p').attr('class','error');
          $('#did_dd').attr('class','errorbox');
          alert('El nombre ya esta siendo utilizado. Por favor ingrese otro nombre.');
        }

        $('#did_dd>p').html(res.msg);
        $('#did_dd>p').show();
      },
      error: function(xml, txt, err) {
        $('#validate_domain_id').removeClass('disable');
        alert('Error verificando');
      } 
    }); 
    
    return false;
  });
  //
  setTimeout("hideFlashMessageSlow()", 5000);
}

function hideFlashMessageSlow(){
  if (jQuery('#flash_message').length>0)
    jQuery('#flash_message').fadeOut('slow');
}

//----------------------------------
//         RESTORE PASSWORD
//---------------------------------- 
function init_restore_password()
{
  check_pass_pair();
}

//----------------------------------
//         SIGNUP
//---------------------------------- 
function init_signup()
{
  check_pass_pair();
}

//----------------------------------
//         USER
//---------------------------------- 
function init_user()
{
  check_pass_pair();
  
  //////// CHANGE EMAIL //////////
  jQuery("#btnChangeEmail").click(function(){	 
    if(jQuery('#user_name[readonly]').length >0){
      jQuery('#user_name').removeAttr('readonly');
      jQuery('#user_name').removeClass('hint');
      return false;
    }
    jQuery('#user_name').attr('readonly', 'readonly');
    jQuery('#user_name').addClass('hint');
    return false;
  });
  
  //////// CHANGE PASSWORD //////////
  jQuery("#btnChangePassword").click(function(){	
    if( jQuery('#change_password').is(':visible')){
      jQuery("#btnCancelNewPassword").click();
      return false;
    }
    jQuery('#change_password').slideDown('slow', function() {
      // Animation complete.
    });
    jQuery("#actual_password").css({ opacity: 0.5 });
  });
  
  //////// SAVE NEW PASSWORD //////////
  jQuery("#btnSaveNewPassword").click(function(){
    jQuery('#change_password').slideUp('slow', function() {
      // Animation complete.
    });
    jQuery("#actual_password").css({ opacity: 1 });
  });
  
  //////// CANCEL NEW PASSWORD //////////
  jQuery("#btnCancelNewPassword").click(function(){
    jQuery('#change_password').slideUp('slow', function() {
      // Animation complete.
    });
    jQuery("#actual_password").css({ opacity: 1 });
  });
}

//----------------------------------
//         ACCOUNT
//---------------------------------- 

function init_account()
{
  $('.action>form').submit( function() {
    $('#msg1').show();
    $('#msg2').show();
    return true;
  });
}
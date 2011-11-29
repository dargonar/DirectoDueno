/* ========================================================================================== */
/* Utils  =================================================================================== */
var sellPrices = ['0','5000','10000','25000','50000','75000','100000', 
                  '125000','150000','175000','200000','250000','300000', '350000', '400000','500000', '500001']; // 500001 hacked en search_helper_func.
var tmp_currency='$';
                  
function swithPropertyLocationMap(sender, img_id, img_map_src, map_type, map_type_selector_id){
  var new_src = img_map_src.replace('roadmap',map_type);
  jQuery('#'+img_id).attr('src', new_src); 
  jQuery('#'+map_type_selector_id+' span.selected').removeClass('selected'); 
  jQuery(sender).addClass('selected');
  return false;
}


function getPriceValue(value){
  if(jQuery('#prop_operation_id').val()==OPER_RENT)
    return value;
  return sellPrices[value];
}

function getPriceValues(){
  var values = jQuery("#price_slider").slider( "option", "values" );
  return [getPriceValue(values[0]), getPriceValue(values[1])];
}

function setPriceSliderOptions(price_slider, max, step, value0, value1)
{
  jQuery("#"+price_slider).slider( "option" , 'max' ,  max);
  jQuery("#"+price_slider).slider( "option" , 'step' , step);
  jQuery("#"+price_slider).slider( "option" , 'values' , [value0, value1] );
}
      
function formatRangePriceText(object_id, from, to, currency, max)
{
  tmp_currency = currency.toUpperCase();
  var max_limit = formatPriceText(to);
  
  if((to == max) |(jQuery('#prop_operation_id').val()==OPER_SELL & to == parseInt(sellPrices[sellPrices.length-1])))
  {
    max_limit = '-sin límite-';
  }
  var str_html = '<small>'+tmp_currency+' </small><b>' + formatPriceText(from) + '</b>&nbsp;<font class="to">a</font>&nbsp;<b>' + max_limit + '</b>';
  jQuery('#'+object_id).html(str_html);
  
}

function formatPriceText(level) {
  
  var valor = level.toString();
  if(level>0)
    //valor = new Number(level*1000).numberFormat('#,#,#,#').replace(/,/g,'.').toString();
    valor = new Number(level).numberFormat('#,#,#,#').replace(/,/g,'.').toString();
  
  return valor;  
}

function formatPriceRange(level1, level2) {
  return 'US$ ' + level1.toString() + 'K a ' + level2.toString() + 'K';
}

function formatPrice(level) {
  if (level === null || typeof(level) == 'undefined')
    return '';
  
  if (level == -1) return '-';
  
  return 'US$ ' + formatCurrency(level);
}

/* Helper de Geocoding. */
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
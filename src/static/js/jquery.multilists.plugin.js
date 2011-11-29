/*************************************************
**  jQuery Multi Column Lists version 1.0.0
**  copyright Fred Kelly, licensed GPL & MIT
**  http://fredkelly.net/
**************************************************/

(function($){
	$.fn.multilists = function(options) {
		
		var defaults = {
			cols: 2
		};
		
		var options = $.extend(defaults, options);

		return this.each(function() {
			
			obj = $(this);
			$items = obj.children('li');
			
			// don't waste time on empty lists
			if ($items.size()>1) {
				
				// if no width set, container divided by columns
				if (!options.colWidth) {
					options.colWidth = Math.floor(obj.width()/options.cols);
				}
			
				var colSize = Math.round($items.size()/options.cols);
				var currentCol = 0;
				var vertReturn = 0;

				// loop list items
				$items.each(function(i) {
					// negative top margin
					if (i % colSize == 0 && i>0) {
						$(this).css('margin-top', -vertReturn);
						vertReturn = 0;
						currentCol++;
					}
					// add left margin
					if (currentCol>0) {
						//$(this).css('margin-left', currentCol * options.colWidth + 'px');
						$(this).css('margin-left', currentCol * options.colWidth + 25 + 'px');
					}
					vertReturn += $(this).height();
				});
				
			}
			
		});
		
	};
})(jQuery);
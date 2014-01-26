$(document).ready(function() {
	var options = $(".box-option");
	$(options).each(function() {
		var obj = this;
		if ($(obj).is(':checked')) {
			$(obj).parent().addClass("box-selected");
		}
		$(obj).parent().click(function() {
			$(obj).prop('checked', true);
			$(options).not(obj).each(function() {
				// LOL UGLY HACK ROFL HTML SUCKS  -- kaniini.
				if ($(this).attr('name') != $(obj).attr('name'))
					return;
				$(this).prop('checked', false);
				$(this).parent().removeClass("box-selected");
			});
			$(obj).parent().addClass("box-selected");
		});
	});
});

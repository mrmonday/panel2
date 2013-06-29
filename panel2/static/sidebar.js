function equalize(p) {
	function equalize_worker() {
		var maxheight = 0;

		/* find maximum height */
		p.children().each(function() {
			var height = $(this).height("auto").height();
			if (height > maxheight)
				maxheight = height;
		});

		/* apply maximum height */
		p.children().each(function() {
			$(this).height(maxheight);
		});
	}

	equalize_worker();
}

$(document).ready(function() {
	$(".row-equalize").each(function() {
		var maxheight = 0;
		var recurse = false;

		equalize($(this));
		$(this).bind("DOMSubtreeModified", function() {
			if (recurse)
				return;

			recurse = true;
			equalize($(this));
			recurse = false;
		});
	});

	$('.launchconsole').click(function() {
		window.open($(this).attr('href'),'', 'scrollbars=no,location=no,status=no,toolbar=no,menubar=no,width=640,height=460');
		return false;	
	});
});


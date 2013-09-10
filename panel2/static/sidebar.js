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
	setInterval(equalize_worker, 500);
}

$(document).ready(function() {
	$(".row-equalize").each(function() {
		equalize($(this));
	});

	$('.launchconsole').click(function() {
		window.open($(this).attr('href'),'', 'scrollbars=no,location=no,status=no,toolbar=no,menubar=no,width=640,height=460');
		return false;	
	});
});


// Sticky sidebar w/jQuery
$(document).load(function() {
	sidebarwidth = $(".row-fluid .span2").css('width');
	bodypaddingtop = $("header").css('height');
	sidebarheight = $("body").css('height');
	$('#sidebar').css('width', sidebarwidth);
	$('#sidebar').css('height', sidebarheight);
	contentmargin = parseInt(sidebarwidth);
	$('#container-base').css('paddingTop', bodypaddingtop);
	$('.contentfix').css('marginLeft', contentmargin + 20);
	$('.contentfix').css('marginRight', 0);
});

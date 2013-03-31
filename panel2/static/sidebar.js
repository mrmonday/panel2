// Sticky sidebar w/jQuery
function setup_sidebar() {
	cellwidth = ($(document).width() / 12) - 35;
	sidebarwidth = cellwidth * 2 + (cellwidth / 2);
	bodypaddingtop = $("header").css('height');
	sidebarheight = $(window).height() - $("header").height();
	$('#sidebar').css('width', sidebarwidth);
	$('#sidebar').css('height', sidebarheight);
	$('#container-base').css('paddingTop', bodypaddingtop);
	$('.contentfix').css('marginLeft', sidebarwidth);
	$('.contentfix').css('marginRight', 0);
}

$(document).ready(setup_sidebar);
$(window).resize(setup_sidebar);

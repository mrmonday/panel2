$(document).ready(function() {
	$(".row-equalize").eqHeight(".span1, .span2, .span3, .span4, .span5, .span6, .span7, .span8, .span9, .span10, .span11, .span12");

	$('#launchconsole').click(function() {
		window.open($(this).attr('href'),'', 'scrollbars=no,location=no,status=no,toolbar=no,menubar=no,width=640,height=460');
		return false;	
	});
});


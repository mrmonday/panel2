var icon_checking = $('<i class="icon-spinner icon-spin"></i>');
var icon_running  = $('<i class="icon-ok-sign text-success"></i>');
var icon_stopped  = $('<i class="icon-remove-sign text-error"></i>');

function status_fetch(url, target) {
	function __data_received(data) {
		if (data.running)
			target.html(icon_running);
		else
			target.html(icon_stopped);
	}

	$.ajax({
		url: url,
		type: 'GET',
		dataType: 'json',
		success: __data_received,
	});
}

function status_setup(url, target) {
	target.html(icon_checking);

	function __fetch() {
		status_fetch(url, target);
	}

	__fetch();
	setInterval(__fetch, 5000);
}

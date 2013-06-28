function status_setup(url, target) {
	var icon_checking = $('<i class="icon-spinner icon-spin"></i>');
	var icon_running  = $('<i class="icon-ok-sign text-success"></i>');
	var icon_stopped  = $('<i class="icon-remove-sign text-error"></i>');

	var tg = target;

	tg.html(icon_checking);

	function __fetch() {
		function __data_received(data) {
			if (data.running)
				tg.html(icon_running);
			else
				tg.html(icon_stopped);
		}

		$.getJSON(url, null, __data_received);
	}

	__fetch();
	setInterval(__fetch, 30000);
}

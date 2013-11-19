function logdata_fetch(url, target, header) {
	var method_names = {
		vps_create: "Initialize VPS image",
		vps_format: "Initialize VPS filesystem",
		vps_rootpass: "Set VPS Root Password",
		vps_image: "Install OS to VPS",
		create: "Start VPS",
		destroy: "Forcefully Shutdown VPS",
		shutdown: "Gracefully Shutdown VPS",
	}

	function on_log_data_received(json_data, target) {
		var table = $('<table></table>').addClass('table table-striped');
		var header_row = $('<tr><th style="width: 24px"></th></tr>');
                var headers = ['Description', 'When'];

                for (i = 0; i < headers.length; i++) {
                    header_row.append($('<th>' + headers[i] + '</th>'));
		}

		if (header != false)
	                table.append(header_row);

		if (json_data) {
			for (i = 0; i < json_data.length; i++) {
				var row = $('<tr></tr>');

				var td = $('<td class="text-center span1"></td>');

				if (!json_data[i].start_ts) {
					td.append($('<i class="icon-time"></i>'));
				} else if (!json_data[i].rsp_env) {
					td.append($('<i class="icon-spinner"></i>'));
				} else if (!json_data[i].rsp_env.params) {
					td.append($('<i class="icon-remove-sign text-error" title="No error message provided"></i>'));
				} else if (json_data[i].rsp_env.params.success) {
					td.append($('<i class="icon-ok-sign text-success"></i>'));
				} else if (json_data[i].rsp_env.params.error) {
					td.append($('<i class="icon-remove-sign text-error" title="' + json_data[i].rsp_env.params.error + '"></i>'));
				}

				row.append(td);
				row.append($('<td>' + method_names[json_data[i].req_env.method] + ' (' + json_data[i].req_env.params.domname + ')</td>'));

				if (json_data[i].end_ts) {
	                                var end_ts = new Date(json_data[i].end_ts);
					row.append($('<td>' + end_ts.toLocaleString() + '</td>'));
				} else if (json_data[i].start_ts) {
	                                var start_ts = new Date(json_data[i].start_ts);
					row.append($('<td>' + start_ts.toLocaleString() + '</td>'));
				} else {
					row.append($('<td></td>'));
				}

				table.append(row);
			}
		}

                target.html(table);
	}

	$.ajax({
		url: url,
		type: 'GET',
		dataType: 'json',
		success: function (data) { on_log_data_received(data, target); },
	});
}

function logdata_setup(url, target, refresh, header) {
	function __fetch() {
		logdata_fetch(url, target, header);
	}

	__fetch();
	setInterval(__fetch, refresh);
}

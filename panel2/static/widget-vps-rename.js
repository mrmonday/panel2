function renamewidget(posturi, name, parent, token) {
	var displayname = $("<span></span>").append(name);
	var icon_pencil = $("<i class='icon-pencil text-warning'></i>");

	function set_displayname(newname) {
		name = newname;
		displayname = $("<span></span>").append(name);
	}

	function set_default() {
		var container = $("<span></span>").append(displayname).append("&nbsp;").append(icon_pencil);
		parent.html(container);

		icon_pencil.bind('click', set_editable);
	}

	function set_editable() {
		var icon_save = $("<i class='icon-save text-warning'></i>");
		var input = $("<input type='text' name='nickname' value='" + name + "'>");
		var container = $("<span></span>").append(input).append("&nbsp;").append(icon_save);

		parent.html(container);

		icon_save.bind('click', function() {
			var nm = input.attr('value');

			$.ajax({
				url: posturi,
				type: 'POST',
				dataType: 'json',
				data: {
					nickname: nm,
                    session_validation_key: token
				},
				success: function(data) {
					if (data.nickname)
						set_displayname(data.nickname);
					else
						set_displayname(data.name);

					set_default();
				},
			});

			parent.html($('<i class="icon-spinner icon-spin"></i>'));
		});
	}

	set_default();
}

function show_notifications(data) {
	notifications = data['messages'];
	for (i = 0; i < notifications.length; i++)
		$('.bottom-right').notify(notifications[i]).show();
}

function update() {
	randval = Math.floor((Math.random()*100000)+1);
	$.ajax({
		url: '/notifications.json?random=' + randval,
		type: 'GET',
		dataType: 'json',
		success: show_notifications
	});
}

$(document).ready(function() {
	update();
	setInterval(update, 1000);
	$('.jsonify').click(function(event) {
		event.preventDefault();
		$.ajax({
			url: event.target.href,
			type: 'GET',
		});
	});
});

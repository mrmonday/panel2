#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs LLC

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice, this permission notice and all necessary source code
to recompile the software are included or otherwise available in all
distributions.

This software is provided 'as is' and without any warranty, express or
implied.  In no event shall the authors be liable for any damages arising
from the use of this software.
"""

import re

from flask import Markup, redirect, url_for, request, abort
from jinja2 import evalcontextfilter, Markup, escape

from panel2.user import User, get_session_user, login_required, admin_required
from panel2.utils import strip_unprintable, render_template_or_json
from panel2.support.models import Ticket, Reply, send_message
from panel2.support import support
from panel2 import app, db

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@app.template_filter()
@evalcontextfilter
def breakln(eval_ctx, value):
    result = escape(value).replace('\n', Markup(' <br> \n'))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result

def user_can_access_ticket(ticket, user=None):
    if user is None:
        user = get_session_user()
    if user.is_admin is True:
        return True
    if ticket.user != user:
        return False
    return True

@support.route('/')
@support.route('/tickets')
@login_required
def list():
    user = get_session_user()
    tickets = Ticket.query.filter_by(user_id=user.id).order_by(Ticket.is_open).order_by(Ticket.id)
    return render_template_or_json('support/ticketlist.html', tickets=tickets)

@support.route('/tickets/all')
@admin_required
def list_all():
    tickets = Ticket.query.order_by(Ticket.is_open).order_by(Ticket.id)
    return render_template_or_json('support/ticketlist.html', tickets=tickets)

@support.route('/tickets/open')
@admin_required
def list_open():
    tickets = Ticket.query.filter_by(is_open=True).order_by(Ticket.id)
    return render_template_or_json('support/ticketlist.html', tickets=tickets)

@support.route('/tickets/closed')
@admin_required
def list_closed():
    tickets = Ticket.query.filter_by(is_open=False).order_by(Ticket.id)
    return render_template_or_json('support/ticketlist.html', tickets=tickets)

@support.route('/ticket/<ticket_id>', methods=['GET', 'POST'])
@login_required
def view(ticket_id):
    ticket = Ticket.query.filter_by(id=ticket_id).first_or_404()
    if user_can_access_ticket(ticket) is not True:
        abort(403)
    if request.method == 'POST':
        reply = strip_unprintable(request.form['message'])
        ticket.add_reply(get_session_user(), reply)
        return redirect(url_for('.view', ticket_id=ticket_id))

    return render_template_or_json('support/ticketview.html', ticket=ticket)

@support.route('/ticket/<ticket_id>/close')
@login_required
def close(ticket_id):
    ticket = Ticket.query.filter_by(id=ticket_id).first_or_404()
    if user_can_access_ticket(ticket) is not True:
        abort(403)
    ticket.close()

    return redirect(url_for('.list'))

@support.route('/ticket/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        subject = strip_unprintable(request.form['subject'])
        message = strip_unprintable(request.form['message'])

        if len(subject) == 0:
            abort(500)
        if len(message) == 0:
            abort(500)

        ticket = Ticket(get_session_user(), subject, message)
        return redirect(url_for('.view', ticket_id=ticket.id))

    return render_template_or_json('support/ticketnew.html')

@support.route('/message/<username>', methods=['GET', 'POST'])
@admin_required
def message(username):
    if request.method == 'POST':
        subject = strip_unprintable(request.form['subject'])
        message = strip_unprintable(request.form['message'])

        if len(subject) == 0:
            abort(500)
        if len(message) == 0:
            abort(500)

        user = User.query.filter_by(username=username).first()
        ticket = send_message(user, get_session_user(), subject, message)
        return redirect(url_for('.view', ticket_id=ticket.id))

    return render_template_or_json('support/sendmessage.html', username=username)

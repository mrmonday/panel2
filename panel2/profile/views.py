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

from panel2.profile import profile
from panel2.user import User, admin_required
from panel2.utils import render_template_or_json

@profile.route('/')
@admin_required
def list():
    users = User.query
    return render_template_or_json('profile/userlist.html', users=users)

@profile.route('/<username>')
@profile.route('/<username>/index')
@admin_required
def view_base(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template_or_json('profile/userview.html', user=user)

@profile.route('/<username>/invoices')
@admin_required
def view_invoices(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template_or_json('profile/userinvoices.html', user=user)

@profile.route('/<username>/services')
@admin_required
def view_services(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template_or_json('profile/userservices.html', user=user)

@profile.route('/<username>/tickets')
@admin_required
def view_tickets(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template_or_json('profile/usertickets.html', user=user)


#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from flask import render_template, Markup, redirect, url_for, request
from panel2.models import User, get_session_user
from panel2.dns.models import Domain, Record
from panel2.dns import dns

@dns.route('/')
@dns.route('/zones')
def list():
    user = get_session_user()
    return render_template('dns/zones.html', zones=user.domains)

@dns.route('/zone/<zone>')
def view_zone(zone):
    domain = Domain.query.filter_by(id=zone).first()
    return render_template('dns/view-zone.html', zone=domain)

@dns.route('/zone/<zone>/record/<record>', methods=['GET', 'POST'])
def edit_record(zone, record):
    record_obj = Record.query.filter_by(domain_id=zone, id=record).first()
    if request.method == 'POST':
        record_obj.set_name(request.form['subdomain'] + '.' + record_obj.domain.name)
        record_obj.set_content(request.form['content'])
        return redirect(url_for('.view_zone', zone=request_obj.id))

    return render_template('dns/edit-record.html', zone=record_obj.domain, record=record_obj)

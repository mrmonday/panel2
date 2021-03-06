#!/usr/bin/env python
"""
Copyright (c) 2012, 2013, 2014 Centarra Networks, Inc.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice, this permission notice and all necessary source code
to recompile the software are included or otherwise available in all
distributions.

This software is provided 'as is' and without any warranty, express or
implied.  In no event shall the authors be liable for any damages arising
from the use of this software.
"""

from flask import Markup, redirect, url_for, request, abort, flash
from panel2.user import User, get_session_user, login_required, require_permission
from panel2.utils import strip_unprintable, render_template_or_json
from panel2.dns.models import Domain, Record, valid_records
from panel2.dns import dns
from panel2.dns.axfr import do_axfr
from panel2 import db

def is_valid_host(host):
    '''IDN compatible domain validator'''
    if '.arpa' in host:
        return True
    try:
        host = host.encode('idna').lower()
    except:
        return False
    if not hasattr(is_valid_host, '_re'):
        import re
        is_valid_host._re = re.compile(r'^([0-9a-z_]([-\w]*[0-9a-z_]|)\.)+[a-z0-9\-_]{1,15}$')
    checkhost = host
    if host[0] == '*':
        checkhost = host[2:]
    return bool(is_valid_host._re.match(checkhost))

def user_can_access_domain(domain, user=None, modify=False):
    if user is None:
        user = get_session_user()
    if domain.user == user:
        return True
    if not modify and user.has_permission('dns:auspex'):
        return True
    if modify and user.has_permission('dns:modify'):
        return True
    return False

@dns.route('/')
@dns.route('/zones')
@login_required
def list():
    user = get_session_user()
    return render_template_or_json('dns/zones.html', zones=user.domains)

@dns.route('/zones/all')
@require_permission('dns:auspex')
def list_all():
    return render_template_or_json('dns/zones.html', zones=Domain.query)

@dns.route('/zone/<zone_id>')
@login_required
def view_domain(zone_id):
    domain = Domain.query.filter_by(id=zone_id).first_or_404()
    if user_can_access_domain(domain) is False:
        abort(403)
    return render_template_or_json('dns/view-zone.html', zone=domain)

@dns.route('/zone/<zone_id>/record/<record_id>', methods=['GET', 'POST'])
@login_required
def edit_record(zone_id, record_id):
    domain = Domain.query.filter_by(id=zone_id).first_or_404()
    if user_can_access_domain(domain, modify=True) is False:
        abort(403)
    record_obj = Record.query.filter_by(domain_id=domain.id, id=record_id).first_or_404()
    if request.method == 'POST':
        record_obj.update_name(record_obj.domain.full_name(request.form['subdomain']))
        record_obj.update_content(request.form['content'])
        return redirect(url_for('.view_domain', zone_id=domain.id))

    return render_template_or_json('dns/edit-record.html', zone=record_obj.domain, record=record_obj)

@dns.route('/zone/new', methods=['GET', 'POST'])
@login_required
def new_domain():
    if request.method == 'POST':
        user = get_session_user()
        domain_name = request.form['domain_name']
        if is_valid_host(domain_name) is not True:
            flash('Domain %s is invalid' % domain_name, 'error')
            return redirect(url_for('.new_domain'))
        if Domain.query.filter_by(name=domain_name).first() is not None:
            flash('Domain %s already exists' % domain_name, 'error')
            return redirect(url_for('.new_domain'))
        if Record.query.filter_by(name=domain_name).first() is not None:
            flash('Record {0} already exists, cannot make domain {0}'.format(domain_name), 'error')
            return redirect(url_for('.new_domain'))

        domain = Domain(user, domain_name)
        return redirect(url_for('.view_domain', zone_id=domain.id))

    return render_template_or_json('dns/new-domain.html')

@dns.route('/zone/<zone_id>/record/new', methods=['GET', 'POST'])
@login_required
def new_record(zone_id):
    domain = Domain.query.filter_by(id=zone_id).first_or_404()
    if user_can_access_domain(domain, modify=True) is False:
        abort(403)
    if request.method == 'POST':
        full_name = domain.full_name(request.form['subdomain'])
        if is_valid_host(full_name) is not True:
            flash('Subdomain %s is invalid' % full_name, 'error')
            return redirect(url_for('.new_record', zone_id=zone_id))
        content = strip_unprintable(request.form['content'])
        domain.add_record(full_name,
                          content, request.form['type'],
                          request.form['prio'], request.form['ttl'])
        return redirect(url_for('.view_domain', zone_id=domain.id))

    return render_template_or_json('dns/new-record.html', zone=domain, record_types=valid_records)

@dns.route('/zone/<zone_id>/record/<record_id>/delete')
@login_required
def delete_record(zone_id, record_id):
    domain = Domain.query.filter_by(id=zone_id).first_or_404()
    if user_can_access_domain(domain, modify=True) is False:
        abort(403)
    Record.query.filter_by(domain_id=domain.id, id=record_id).delete()
    db.session.commit()

    return redirect(url_for('.view_domain', zone_id=zone_id))

@dns.route('/zone/<zone_id>/delete')
@login_required
def delete_domain(zone_id):
    domain = Domain.query.filter_by(id=zone_id).first_or_404()
    if user_can_access_domain(domain, modify=True) is False:
        abort(403)

    # Surprise, surprise!  The SQLAlchemy documentation lies.
    # Remove all dependent records in a separate transaction before
    # removing the parent.  This way we can avoid MySQL derping.
    for record in domain.records:
        db.session.delete(record)

    db.session.commit()

    db.session.delete(domain)
    db.session.commit()

    return redirect(url_for('.list'))

@dns.route('/zone/<zone_id>/axfr-import', methods=['GET', 'POST'])
@login_required
def import_domain(zone_id):
    domain = Domain.query.filter_by(id=zone_id).first_or_404()
    if user_can_access_domain(domain, modify=True) is False:
        abort(403)
    if request.method == 'POST':
        def record_callback(pname, qtype, ttl, prio, content):
            domain.add_record(pname, content, qtype, prio, ttl)

        if len(request.form['nameserver']) != 0:
            try:
                do_axfr(request.form['nameserver'], domain.name, record_callback)
            except:
                pass

        return redirect(url_for('.view_domain', zone_id=domain.id))

    return render_template_or_json('dns/import-records.html', zone=domain)

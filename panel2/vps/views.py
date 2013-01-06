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

import json

from flask import render_template, redirect, url_for, abort, flash, jsonify, make_response
from panel2.vps import vps
from panel2.vps.models import XenVPS
from panel2.user import login_required, admin_required, get_session_user

def can_access_vps(vps, user=None):
    if user is None:
        user = get_session_user()
    if user.is_admin is True:
        return True
    if vps.user != user:
        return False
    return True

@vps.route('/')
@vps.route('/list')
@login_required
def list():
    return render_template('vps/list.html')

@vps.route('/list/all')
@login_required
@admin_required
def list_all():
    return render_template('vps/list.html', vpslist=XenVPS.query.order_by(XenVPS.id))

@vps.route('/<vps>')
def view(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)
    return render_template('vps/view.html', service=vps)

@vps.route('/<vps>/delete')
def adm_delete(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)
    vps.delete()
    flash('Your VPS has been deleted.')
    return redirect(url_for('.list'))

@vps.route('/<vps>/create')
def create(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)

    job = vps.create()
    flash('Your request has been queued.  Job ID: {}'.format(job.id))
    return redirect(url_for('.view', vps=vps.id))

@vps.route('/<vps>/shutdown')
def shutdown(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)

    job = vps.shutdown()
    flash('Your request has been queued.  Job ID: {}'.format(job.id))
    return redirect(url_for('.view', vps=vps.id))

@vps.route('/<vps>/destroy')
def destroy(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)

    job = vps.destroy()
    flash('Your request has been queued.  Job ID: {}'.format(job.id))
    return redirect(url_for('.view', vps=vps.id))

@vps.route('/<vps>/powercycle')
def powercycle(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)

    job = vps.destroy()
    job = vps.create()
    flash('Your request has been queued.  Job ID: {}'.format(job.id))
    return redirect(url_for('.view', vps=vps.id))

@vps.route('/<vps>/cpustats/<start>/<step>')
def cpustats(vps, start, step):
    vps = XenVPS.query.filter_by(id=vps).first()
    return jsonify(vps.get_cpu_stats(start=int(start), step=int(step)))

@vps.route('/<vps>/netstats/<start>/<step>')
def netstats(vps, start, step):
    vps = XenVPS.query.filter_by(id=vps).first()
    response = make_response(json.dumps(vps.get_net_stats(start=int(start), step=int(step))))
    response.headers['Content-Type'] = 'application/json'
    return response

@vps.route('/<vps>/vbdstats/<start>/<step>')
def vbdstats(vps, start, step):
    vps = XenVPS.query.filter_by(id=vps).first()
    response = make_response(json.dumps(vps.get_vbd_stats(start=int(start), step=int(step))))
    response.headers['Content-Type'] = 'application/json'
    return response

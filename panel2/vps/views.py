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

from flask import render_template, redirect, url_for, abort, flash, jsonify, make_response, request
from panel2 import db
from panel2.job import Job
from panel2.service import IPAddress, IPAddressRef, IPRange
from panel2.vps import vps
from panel2.vps.models import XenVPS
from panel2.user import login_required, admin_required, get_session_user

# XXX: this should eventually be moved to a DB and the template IR should just be
# sent with the vps_image() opcall.  --nenolod
template_map = {
    'debian6_login.xml': 'Debian 6.0 (minimal)',
    'debian7_login.xml': 'Debian 7.0 (minimal) (beta)',
    'ubuntu12.04_login.xml': 'Ubuntu Server 12.04 LTS (minimal)',
    'alpine2.5_login.xml': 'Alpine 2.5 (minimal)',
}

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
    return render_template('vps/view-graphs.html', service=vps)

@vps.route('/<vps>/expiry')
def expiry(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)
    return render_template('vps/view-expiry.html', service=vps)

@vps.route('/<vps>/admin')
@login_required
@admin_required
def staff_toolbox(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)
    return render_template('vps/view-admin.html', service=vps)

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

@vps.route('/<vps>/deploy', methods=['GET', 'POST'])
@login_required
def deploy(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)
    if request.method == 'POST':
        flash('Your deployment request is in progress, check back later.')
        vps.reimage(request.form['imagename'], request.form['rootpass'])
        return redirect(url_for('.jobs', vps=vps.id))
    else:
        return render_template('vps/view-deploy.html', service=vps, templates=template_map)

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

@vps.route('/<vps>/admin/ip/<ip>/delete')
@login_required
@admin_required
def adm_del_ip(vps, ip):
    IPAddress.query.filter_by(id=ip).delete()
    db.session.commit()
    return redirect(url_for('.staff_toolbox', vps=vps))

@vps.route('/<vps>/admin/ip/add', methods=['POST'])
@login_required
@admin_required
def adm_add_ip(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    postdata = request.form['ipbox']
    ipnetid, ip = postdata.split('!')
    ipnet = IPRange.query.filter_by(id=ipnetid).first()
    vps.attach_ip(ip, ipnet)
    return redirect(url_for('.staff_toolbox', vps=vps.id))

@vps.route('/<vps>/jobs.json')
@login_required
def jobs_json(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)
    joblist = vps.jobs().order_by(Job.id.desc()).limit(100)
    lst = []
    javascript_time = lambda f: f * 1000 if f is not None else None
    for job in joblist:
        d = dict()
        d['id'] = job.id
        d['req_env'] = json.loads(job.request_envelope)
        if job.response_envelope:
            d['rsp_env'] = json.loads(job.response_envelope)
        else:
            d['rsp_env'] = None
        d['start_ts'] = javascript_time(job.start_ts)
        d['entry_ts'] = javascript_time(job.entry_ts)
        d['end_ts'] = javascript_time(job.end_ts)
        lst.append(d)

    response = make_response(json.dumps(lst))
    response.headers['Content-Type'] = 'application/json'
    return response

@vps.route('/<vps>/jobs')
def jobs(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)
    return render_template('vps/view-jobs.html', service=vps)

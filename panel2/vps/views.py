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
import time

from flask import redirect, url_for, abort, flash, jsonify, make_response, request, session
from panel2 import db
from panel2.job import Job
from panel2.service import IPAddress, IPAddressRef, IPRange
from panel2.dns.views import is_valid_host
from panel2.vps import vps
from panel2.vps.models import XenVPS, ResourcePlan, Region, KernelProfile, HVMISOImage
from panel2.user import login_required, admin_required, get_session_user, User, Session
from panel2.invoice import Invoice, get_discount_code
from panel2.utils import render_template_or_json
from ediarpc.rpc_client import ServerProxy

# XXX: this should eventually be moved to a DB and the template IR should just be
# sent with the vps_image() opcall.  --nenolod
template_map = {
    'debian6_login.xml': 'Debian 6.0 (minimal)',
    'debian7_login.xml': 'Debian 7.0 (minimal) (beta)',
    'ubuntu12.04_login.xml': 'Ubuntu Server 12.04 LTS (minimal)',
    'alpine2.5_login.xml': 'Alpine 2.5 (minimal)',
    'centos6_login.xml': 'CentOS 6 (minimal)',
    'arch_login.xml': 'Arch Linux (minimal)',
    'gentoo_login.xml': 'Gentoo (minimal)',
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
    user = get_session_user()
    return render_template_or_json('vps/list.html', vpslist=filter(lambda x: x.type == 'xenvps', user.services))

@vps.route('/list/all')
@login_required
@admin_required
def list_all():
    return render_template_or_json('vps/list-all.html', vpslist=XenVPS.query.order_by(XenVPS.id))

@vps.route('/list/u/<user>')
@login_required
@admin_required
def list_user(user):
    u = User.query.filter_by(username=user).first()
    return render_template_or_json('vps/list.html', vpslist=filter(lambda x: x.type == 'xenvps', u.services))

@vps.route('/signup', methods=['GET', 'POST'])
def signup():
    user = get_session_user()
    regions = Region.query.all()
    resource_plans = ResourcePlan.query.order_by(ResourcePlan.memory).all()
    discount = get_discount_code(request.args.get('c', 'DEFAULT'))

    if request.method == 'POST':
        discount = get_discount_code(request.form.get('c', 'DEFAULT'))

        if user is None:
            try:
                username = request.form['username'].strip().rstrip()
                password = request.form['password'].strip().rstrip()
                email = request.form['email'].strip().rstrip()
                if len(username) == 0:
                    return render_template_or_json('vps/signup.html', regions=regions, resource_plans=resource_plans, error='No username provided', discount=discount)
                if len(password) == 0: 
                    return render_template_or_json('vps/signup.html', regions=regions, resource_plans=resource_plans, error='No password provided', discount=discount)
                if len(email) == 0:
                    return render_template_or_json('vps/signup.html', regions=regions, resource_plans=resource_plans, error='No email provided', discount=discount)
                if User.query.filter_by(username=username).first() is not None:
                    return render_template_or_json('vps/signup.html', regions=regions, resource_plans=resource_plans, error='Username is already taken', discount=discount)
                user = User(username, password, email)
            except Exception as e:
                return render_template_or_json('vps/signup.html', regions=regions, resource_plans=resource_plans, error='Exception: ' + repr(e), discount=discount)

            if user is not None:
                sess = Session(user)
                session['session_id'] = sess.id
                session['session_challenge'] = sess.challenge

        vpsname = user.next_service_name()

        region = Region.query.filter_by(id=int(request.form['region'])).first()
        if not region:
            abort(404)
        resource_plan = ResourcePlan.query.filter_by(id=int(request.form['plan'])).first()
        if not resource_plan:
            abort(404)

        vps = resource_plan.create_vps(user, region, vpsname, discount)
        if not vps:
            return redirect(url_for('.nostock'))
        vps.expiry_ts = time.time()
        if user.is_admin:
            vps.price = 0.00
        db.session.add(vps)
        db.session.commit()

        invoice = Invoice(user)
        vps.invoice(invoice)
        invoice.mark_ready()

        if not invoice.payment_ts:
            return redirect(url_for('invoice.view', invoice_id=invoice.id))

        return redirect(url_for('.view', vps=vps.id))

    return render_template_or_json('vps/signup.html', regions=regions, resource_plans=resource_plans, discount=discount)

@vps.route('/nostock')
@login_required
def nostock():
    return render_template_or_json('vps/nostock.html')

@vps.route('/<vps>')
@login_required
def view(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if vps is None:
        abort(404)
    if can_access_vps(vps) is False:
        abort(403)
    return render_template_or_json('vps/view-base.html', service=vps, profiles=KernelProfile.query.all(), templates=template_map)

@vps.route('/<vps>/setnickname', methods=['POST'])
@login_required
def setnickname(vps):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    nickname = request.form.get('nickname', None)
    if not is_valid_host(nickname + '.localdomain'):
        nickname = None
    vps.nickname = nickname
    db.session.add(vps)
    db.session.commit()

    return jsonify({'nickname': vps.nickname, 'name': vps.name})

@vps.route('/<vps>/setprofile', methods=['POST'])
@login_required
def setprofile(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    profile = KernelProfile.query.filter_by(id=int(request.form['profid'])).first()
    if vps is None or profile is None:
        abort(404)
    if can_access_vps(vps) is False:
        abort(403)
    vps.set_profile(profile)
    return redirect(url_for('.view', vps=vps.id))

@vps.route('/<vps>/monitoring/disable')
@login_required
def stop_monitoring(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if vps is None:
        abort(404)
    if can_access_vps(vps) is False:
        abort(403)
    vps.watchdog = False
    db.session.add(vps)
    db.session.commit()
    return redirect(url_for('.view', vps=vps.id))

@vps.route('/<vps>/monitoring/enable')
@login_required
def start_monitoring(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if vps is None:
        abort(404)
    if can_access_vps(vps) is False:
        abort(403)
    vps.watchdog = True
    db.session.add(vps)
    db.session.commit()
    return redirect(url_for('.view', vps=vps.id))

@vps.route('/<vps>/graphs')
@login_required
def graphs(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if vps is None:
        abort(404)
    if can_access_vps(vps) is False:
        abort(403)
    return render_template_or_json('vps/view-graphs.html', service=vps)

@vps.route('/<vps>/admin')
@login_required
def ip_admin(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if vps is None:
        abort(404)
    if can_access_vps(vps) is False:
        abort(403)
    return render_template_or_json('vps/view-admin.html', service=vps)

@vps.route('/<vps>/delete')
@login_required
def adm_delete(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if vps is None:
        abort(404)
    if can_access_vps(vps) is False:
        abort(403)
    vps.delete()
    flash('Your VPS has been deleted.')
    return redirect(url_for('.list'))

@vps.route('/<vps>/renew')
@login_required
def renew(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if vps is None:
        abort(404)
    if can_access_vps(vps) is False:
        abort(403)
    if vps.disable_renew:
        abort(403)

    inv = Invoice(vps.user)
    vps.invoice(inv)
    inv.mark_ready()

    if not inv.payment_ts:
        return redirect(url_for('invoice.view', invoice_id=inv.id))

    return redirect(url_for('.view', vps=vps.id))

@vps.route('/<vps>/create', methods=['GET', 'POST'])
@login_required
def create(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if vps is None:
        abort(404)
    if can_access_vps(vps) is False:
        abort(403)

    if request.method == 'POST':
        prof = KernelProfile.query.filter_by(id=int(request.form['profid'])).first()
        job = vps.create(profile=prof)
        flash('Your request has been queued.  Job ID: {}'.format(job.id))
        return redirect(url_for('.view', vps=vps.id))
    else:
        job = vps.create()

    flash('Your request has been queued.  Job ID: {}'.format(job.id))
    return jsonify({'job': job.id})

@vps.route('/<vps>/shutdown')
@login_required
def shutdown(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if vps is None:
        abort(404)
    if can_access_vps(vps) is False:
        abort(403)

    job = vps.shutdown()
    flash('Your request has been queued.  Job ID: {}'.format(job.id))
    return jsonify({'job': job.id})

@vps.route('/<vps>/destroy')
@login_required
def destroy(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if vps is None:
        abort(404)
    if can_access_vps(vps) is False:
        abort(403)

    job = vps.destroy()
    flash('Your request has been queued.  Job ID: {}'.format(job.id))
    return jsonify({'job': job.id})

@vps.route('/<vps>/powercycle')
@login_required
def powercycle(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if vps is None:
        abort(404)
    if can_access_vps(vps) is False:
        abort(403)

    job = vps.destroy()
    job = vps.create()
    flash('Your request has been queued.  Job ID: {}'.format(job.id))
    return jsonify({'job': job.id})

@vps.route('/<vps>/deploy', methods=['GET', 'POST'])
@login_required
def deploy(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if vps is None:
        abort(404)
    if can_access_vps(vps) is False:
        abort(403)
    if request.method == 'POST':
        create = 'startvps' in request.form
        flash('Your deployment request is in progress, check back later.')
        vps.reimage(request.form['imagename'], request.form['rootpass'], create=create, arch=request.form['arch'])
        return redirect(url_for('.view', vps=vps.id))
    else:
        return render_template_or_json('vps/view-deploy.html', service=vps, templates=template_map)

@vps.route('/<vps>/cpustats/<start>/<step>')
def cpustats(vps, start, step):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    return jsonify(vps.get_cpu_stats(start=int(start), step=int(step)))

@vps.route('/<vps>/netstats/<start>/<step>')
def netstats(vps, start, step):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    response = make_response(json.dumps(vps.get_net_stats(start=int(start), step=int(step))))
    response.headers['Content-Type'] = 'application/json'
    return response

@vps.route('/<vps>/vbdstats/<start>/<step>')
def vbdstats(vps, start, step):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    response = make_response(json.dumps(vps.get_vbd_stats(start=int(start), step=int(step))))
    response.headers['Content-Type'] = 'application/json'
    return response

@vps.route('/<vps>/admin/ip/<ip>/delete')
@login_required
def adm_del_ip(vps, ip):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    IPAddress.query.filter_by(id=ip).delete()
    db.session.commit()
    return redirect(url_for('.ip_admin', vps=vps.id))

@vps.route('/<vps>/admin/ip/<ip>/rdns-modify', methods=['POST'])
@login_required
def adm_modify_ip_rdns(vps, ip):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)

    rdns = request.form.get('rdns', None)
    if not rdns:
        return redirect(url_for('.ip_admin', vps=vps.id))

    if not is_valid_host(rdns):
        flash('Provided rDNS was invalid')
        return redirect(url_for('.ip_admin', vps=vps.id))

    ip = IPAddress.query.filter_by(id=ip).first()

    if ip.service_id != vps.service_id:
        abort(403)

    ip.update_rdns(rdns)

    return redirect(url_for('.ip_admin', vps=vps.id))

@vps.route('/<vps>/admin/ip/add', methods=['POST'])
@login_required
def adm_add_ip(vps):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    postdata = request.form['ipbox']
    ipnetid, ip = postdata.split('!')
    ipnet = IPRange.query.filter_by(id=ipnetid).first()

    if not ipnet.is_ipv6() and not vps.ipv4_quota():
        flash('No additional IPv4 addresses available')
        return redirect(url_for('.ip_admin', vps=vps.id))
    elif ipnet.is_ipv6() and not vps.ipv6_quota():
        flash('No additional IPv6 addresses available')
        return redirect(url_for('.ip_admin', vps=vps.id))

    vps.attach_ip(ip, ipnet)
    return redirect(url_for('.ip_admin', vps=vps.id))

@vps.route('/<vps>/jobs.json')
@login_required
def jobs_json(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if vps is None:
        abort(404)
    if can_access_vps(vps) is False:
        abort(403)
    limit = int(request.args.get('limit', 100))
    joblist = vps.jobs().order_by(Job.id.desc()).limit(limit)
    lst = []
    javascript_time = lambda f: f * 1000 if f is not None else None
    for job in joblist:
        d = dict()
        d['id'] = job.id
        d['req_env'] = json.loads(job.request_envelope)
        if job.response_envelope:
            try:
                d['rsp_env'] = json.loads(job.response_envelope)
            except:
                d['rsp_env'] = None
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
@login_required
def jobs(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)
    return render_template_or_json('vps/view-jobs.html', service=vps)

@vps.route('/<vps>/profiler')
@login_required
def profiler(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)
    return render_template_or_json('vps/view-profiler.html', service=vps)

@vps.route('/<vps>/console')
@login_required
def console(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)
    return render_template_or_json('vps/view-console.html', service=vps)

@vps.route('/<vps>/console.html')
@login_required
def console_real(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)
    return render_template_or_json('vps/view-console-real.html', service=vps)

@vps.route('/<vps>/hvm')
@login_required
def hvmvnc(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    if can_access_vps(vps) is False:
        abort(403)
    user = get_session_user()
    return render_template_or_json('vps/view-hvm.html', service=vps, isolist=HVMISOImage.query.filter((HVMISOImage.public == True) | (HVMISOImage.user_id == vps.user.id)).all())

@vps.route('/<vps>/hvm/setiso', methods=['POST'])
@login_required
def hvmisoset(vps):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    hvmiso = HVMISOImage.query.filter_by(id=int(request.form['isoid'])).first_or_404()
    vps.set_hvmiso(hvmiso)
    return redirect(url_for('.hvmvnc', vps=vps.id))

@vps.route('/<vps>/hvm/setbootorder', methods=['POST'])
@login_required
def hvmbootorder(vps):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    vps.hvm_bootorder = request.form.get('bootorder', 'cd')
    db.session.add(vps)
    db.session.commit()
    return redirect(url_for('.hvmvnc', vps=vps.id))

@vps.route('/<vps>/hvm/setnictype', methods=['POST'])
@login_required
def hvmnictype(vps):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    vps.hvm_nictype = request.form.get('nictype', 'e1000')
    db.session.add(vps)
    db.session.commit()
    return redirect(url_for('.hvmvnc', vps=vps.id))

@vps.route('/<vps>/hvmiso/new', methods=['POST'])
@login_required
def hvmiso_new(vps):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)

    name = request.form.get('isoname', None)
    iso = request.form.get('isouri', None)

    if not name or not iso:
        flash('missing necessary parameters')
        return redirect(url_for('.hvmvnc', vps=vps.id))

    HVMISOImage(get_session_user(), name, iso)
    return redirect(url_for('.hvmvnc', vps=vps.id))

@vps.route('/<vps>/hvmiso/<isoid>/delete')
@login_required
def hvmiso_delete(vps, isoid):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    hvmiso = HVMISOImage.query.filter_by(id=int(isoid)).first_or_404()
    if can_access_vps(hvmiso) is False:
        abort(403)
    db.session.delete(hvmiso)
    db.session.commit()
    return redirect(url_for('.hvmvnc', vps=vps.id))

@vps.route('/<vps>/clone', methods=['GET', 'POST'])
@login_required
def clone(vps):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    if request.method == 'POST':
        create = 'startvps' in request.form
        flash('Your clone is in progress, check back later.')
        vps.clone(request.form['imagename'], request.form['targetip'], create=create)
        return redirect(url_for('.jobs', vps=vps.id))
    return render_template_or_json('vps/view-clone.html', service=vps, templates=template_map)

@vps.route('/<vps>/keypair')
@login_required
def keypair(vps):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    return jsonify({'pubkey': vps.node.gen_keypair()})

@vps.route('/<vps>/rawstats.json')
@login_required
def rawstats(vps):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    data = vps.node.api(ServerProxy).domain_list()[vps.name]
    if data:
        return jsonify({'stats': data})

@vps.route('/<vps>/status.json')
@login_required
def status_json(vps):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    return jsonify({"running": vps.online})

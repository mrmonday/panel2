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

from flask import request, redirect, url_for, render_template, jsonify

from panel2 import db
from panel2.profile import profile
from panel2.user import User, admin_required
from panel2.utils import render_template_or_json
from panel2.vps.models import Node, Region
from panel2.service import Service
from panel2.invoice import Invoice, DiscountCode, ServiceCreditItem

import time

@profile.route('/')
@admin_required
def list():
    users = User.query
    return render_template_or_json('profile/userlist.html', users=users,
           revenue_sum=sum([user.total_revenue() for user in users]))

@profile.route('/_list/filter/paid')
@admin_required
def list_paid():
    users = filter(lambda x: x.total_revenue() > 0, User.query)
    return render_template_or_json('profile/userlist.html', users=users,
           revenue_sum=sum([user.total_revenue() for user in users]))

@profile.route('/_list/filter/free')
@admin_required
def list_free():
    users = filter(lambda x: x.total_revenue() == 0 and len(x.services) > 0, User.query)
    return render_template_or_json('profile/userlist.html', users=users,
           revenue_sum=sum([user.total_revenue() for user in users]))

@profile.route('/_list/filter/active')
@admin_required
def list_active():
    users = filter(lambda x: len(x.services) > 0, User.query)
    return render_template_or_json('profile/userlist.html', users=users,
           revenue_sum=sum([user.total_revenue() for user in users]))

@profile.route('/_statistics/node/_new', methods=['GET', 'POST'])
@admin_required
def node_new():
    if request.method == 'POST':
        region = Region.query.filter_by(id=int(request.form['region_id'])).first()
        node = Node(request.form['name'], request.form['ipaddr'], request.form['secret'], region, dnsname=request.form['dnsname'],
                    memorycap=int(request.form['memorycap']), diskcap=int(request.form['diskcap']))
        return redirect(url_for('.node_info', node=node.id))

    return render_template('profile/nodenew.html', regions=Region.query.filter_by(hidden=False).all())

@profile.route('/_statistics/node')
@admin_required
def node_stats():
    nodes = Node.query
    revenue = dict()
    for node in nodes:
        revenue[node.name] = sum([service.price for service in node.vps])
    return render_template_or_json('profile/nodestats.html', nodes=nodes, revenue=revenue)

@profile.route('/_statistics/node/<node>')
@admin_required
def node_info(node):
    node = Node.query.filter_by(id=node).first_or_404()
    return render_template_or_json('profile/nodeinfo.html', node=node)

@profile.route('/_statistics/node/<node>/_togglelock')
@admin_required
def node_lock(node):
    node = Node.query.filter_by(id=node).first_or_404()
    if node.locked:
        node.locked = False
    else:
        node.locked = True
    db.session.add(node)
    db.session.commit()
    return redirect(url_for('.node_stats'))

@profile.route('/_services/delinquent')
@admin_required
def delinquent_services():
    delinquent = Service.query.filter(Service.expiry < time.time())
    return render_template_or_json('profile/servicelist.html', svslist=delinquent,
           revenue_sum=sum([svs.price for svs in delinquent]))

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

@profile.route('/<username>/invoices/new')
@admin_required
def new_invoice(username):
    user = User.query.filter_by(username=username).first_or_404()
    inv = Invoice(user)
    return redirect(url_for('invoice.view', invoice_id=inv.id))

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

@profile.route('/<username>/credits')
@admin_required
def view_credits(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template_or_json('profile/usercredits.html', user=user)

@profile.route('/<username>/credits/new', methods=['POST'])
@admin_required
def add_credit(username):
    user = User.query.filter_by(username=username).first_or_404()
    ServiceCreditItem(user, float(request.form['amount']), request.form['description'])
    return redirect(url_for('.view_credits', username=username))

@profile.route('/_couponcodes')
@admin_required
def coupons_list():
    return render_template_or_json('profile/couponcodes.html', codes=DiscountCode.query.all())

@profile.route('/_couponcodes/<code_id>/delete')
@admin_required
def coupon_delete(code_id):
    code = DiscountCode.query.filter_by(id=code_id).first()
    db.session.delete(code)
    db.session.commit()

    return redirect(url_for('.coupons_list'))

@profile.route('/_couponcodes/_new', methods=['POST'])
@admin_required
def coupon_new():
    code = DiscountCode(request.form['name'], float(request.form['amount']), request.form['type'])
    return redirect(url_for('.coupons_list'))

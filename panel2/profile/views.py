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
from panel2.user import User, Permission, require_permission, get_all_permissions, admin_required
from panel2.utils import render_template_or_json
from panel2.vps.models import Node, Region
from panel2.service import Service
from panel2.invoice import Invoice, DiscountCode, ServiceCreditItem
from panel2.navigation import NavigationManager

import time

profile_nav = NavigationManager()
profile_nav.register('Account List', 'icon-user', 'profile.list', True, 'account:auspex')
profile_nav.register('Paid Accounts', 'icon-user', 'profile.list_paid', True, 'account:auspex')
profile_nav.register('Free Accounts', 'icon-user', 'profile.list_free', True, 'account:auspex')
profile_nav.register('Accounts with Active Services', 'icon-user', 'profile.list_active', True, 'account:auspex')

profile_nav.register('Node Statistics', 'icon-cloud', 'profile.node_stats', True, 'vps:node_auspex')
profile_nav.register('Delinquent Services', 'icon-usd', 'profile.delinquent_services', True, 'account:auspex')

profile_nav.register('Coupon Codes', 'icon-usd', 'profile.coupons_list', True, 'coupon:auspex')

@profile.route('/')
@require_permission('account:auspex')
def list():
    users = User.query
    return render_template_or_json('profile/userlist.html', profile_nav=profile_nav, users=users,
           revenue_sum=sum([user.total_revenue() for user in users]))

@profile.route('/_list/filter/paid')
@require_permission('account:auspex')
def list_paid():
    users = filter(lambda x: x.total_revenue() > 0, User.query)
    return render_template_or_json('profile/userlist.html', profile_nav=profile_nav, users=users,
           revenue_sum=sum([user.total_revenue() for user in users]))

@profile.route('/_list/filter/free')
@require_permission('account:auspex')
def list_free():
    users = filter(lambda x: x.total_revenue() == 0 and len(x.services) > 0, User.query)
    return render_template_or_json('profile/userlist.html', profile_nav=profile_nav, users=users,
           revenue_sum=sum([user.total_revenue() for user in users]))

@profile.route('/_list/filter/active')
@require_permission('account:auspex')
def list_active():
    users = filter(lambda x: len(x.services) > 0, User.query)
    return render_template_or_json('profile/userlist.html', profile_nav=profile_nav, users=users,
           revenue_sum=sum([user.total_revenue() for user in users]))

@profile.route('/_statistics/node/_new', methods=['GET', 'POST'])
@require_permission('vps:node_create')
def node_new():
    if request.method == 'POST':
        region = Region.query.filter_by(id=int(request.form['region_id'])).first()
        node = Node(request.form['name'], request.form['ipaddr'], request.form['secret'], region, dnsname=request.form['dnsname'],
                    memorycap=int(request.form['memorycap']), diskcap=int(request.form['diskcap']))
        return redirect(url_for('.node_info', node=node.id))

    return render_template('profile/nodenew.html', profile_nav=profile_nav, regions=Region.query.filter_by(hidden=False).all())

@profile.route('/_statistics/node')
@require_permission('vps:node_auspex')
def node_stats():
    nodes = Node.query
    revenue = dict()
    for node in nodes:
        revenue[node.name] = sum([service.price for service in node.vps])
    return render_template_or_json('profile/nodestats.html', profile_nav=profile_nav, nodes=nodes, revenue=revenue)

@profile.route('/_statistics/node/<node>')
@require_permission('vps:node_auspex')
def node_info(node):
    node = Node.query.filter_by(id=node).first_or_404()
    return render_template_or_json('profile/nodeinfo.html', profile_nav=profile_nav, node=node)

@profile.route('/_statistics/node/<node>/_togglelock')
@require_permission('vps:node_lock')
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
@require_permission('account:auspex')
def delinquent_services():
    delinquent = Service.query.filter(Service.expiry < time.time())
    return render_template_or_json('profile/servicelist.html', profile_nav=profile_nav, svslist=delinquent,
           revenue_sum=sum([svs.price for svs in delinquent]))

@profile.route('/<username>')
@profile.route('/<username>/index')
@require_permission('account:auspex')
def view_base(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template_or_json('profile/userview.html', profile_nav=profile_nav, subject=user)

@profile.route('/<username>/invoices')
@require_permission('account:auspex')
def view_invoices(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template_or_json('profile/userinvoices.html', profile_nav=profile_nav, subject=user)

@profile.route('/<username>/invoices/new')
@require_permission('invoice:create')
def new_invoice(username):
    user = User.query.filter_by(username=username).first_or_404()
    inv = Invoice(user)
    return redirect(url_for('invoice.view', invoice_id=inv.id))

@profile.route('/<username>/services')
@require_permission('account:auspex')
def view_services(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template_or_json('profile/userservices.html', profile_nav=profile_nav, subject=user)

@profile.route('/<username>/tickets')
@require_permission('account:auspex')
def view_tickets(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template_or_json('profile/usertickets.html', profile_nav=profile_nav, subject=user)

@profile.route('/<username>/credits')
@require_permission('account:auspex')
def view_credits(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template_or_json('profile/usercredits.html', profile_nav=profile_nav, subject=user)

@profile.route('/<username>/permissions', methods=['GET', 'POST'])
@admin_required
def view_permissions(username):
    ptable = get_all_permissions()
    user = User.query.filter_by(username=username).first_or_404()
    if request.method == 'POST' and request.form['perm'] in ptable.keys():
        Permission(user, request.form['perm'])
    return render_template_or_json('profile/userpermissions.html', profile_nav=profile_nav, subject=user, ptable=ptable)

@profile.route('/<username>/credits/new', methods=['POST'])
@require_permission('invoice:push_credit')
def add_credit(username):
    user = User.query.filter_by(username=username).first_or_404()
    ServiceCreditItem(user, float(request.form['amount']), request.form['description'])
    return redirect(url_for('.view_credits', username=username))

@profile.route('/_couponcodes')
@require_permission('coupon:auspex')
def coupons_list():
    return render_template_or_json('profile/couponcodes.html', profile_nav=profile_nav, codes=DiscountCode.query.all())

@profile.route('/_couponcodes/<code_id>/delete')
@require_permission('coupon:modify')
def coupon_delete(code_id):
    code = DiscountCode.query.filter_by(id=code_id).first()
    db.session.delete(code)
    db.session.commit()

    return redirect(url_for('.coupons_list'))

@profile.route('/_couponcodes/_new', methods=['POST'])
@require_permission('coupon:modify')
def coupon_new():
    code = DiscountCode(request.form['name'], float(request.form['amount']), request.form['type'])
    return redirect(url_for('.coupons_list'))

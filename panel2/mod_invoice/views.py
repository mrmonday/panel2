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

from flask import render_template, redirect, url_for, abort, flash, jsonify, make_response, request
from panel2 import app, db
from panel2.mod_invoice import invoice
from panel2.user import User, get_session_user, login_required, admin_required
from panel2.invoice import Invoice

@invoice.route('/')
@login_required
def index():
    return render_template("invoice/invoice-list.html", invoices=get_session_user().invoices)

@invoice.route('/user/<uid>')
@admin_required
def user_index(uid):
    user = User.query.filter_by(id=uid).first()
    if not user:
        abort(404)
    return render_template("invoice/invoice-list.html", invoices=user.invoices)

@invoice.route('/<invoice_id>')
@login_required
def view(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id).first()
    if not invoice:
        abort(404)
    return render_template("invoice/invoice-view.html", invoice=invoice)

@invoice.route('/<invoice_id>/credit')
@admin_required
def credit(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id).first()
    if not invoice:
        abort(404)
    invoice.mark_paid()
    return redirect(url_for('.view', invoice_id=invoice.id))

@invoice.route('/unpaid')
@admin_required
def list_unpaid():
    invlist = Invoice.query.filter_by(payment_ts=None)
    return render_template("invoice/invoice-list.html", invoices=invlist)

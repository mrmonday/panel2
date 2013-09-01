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

from flask import redirect, url_for, abort, flash, jsonify, make_response, request, render_template
from flask_weasyprint import HTML, render_pdf
from panel2 import app, db
from panel2.mod_invoice import invoice
from panel2.user import User, get_session_user, login_required, admin_required
from panel2.utils import render_template_or_json
from panel2.invoice import Invoice, InvoiceItem, PendingCreditItem, ServiceCreditItem

def can_access_invoice(invoice, user=None):
    if user is None:
        user = get_session_user()
    if user.is_admin is True:
        return True
    if invoice.user != user:
        return False
    return True

@invoice.route('/')
@invoice.route('/list')
@login_required
def index():
    return render_template_or_json("invoice/invoice-list.html", invoices=get_session_user().invoices)

@invoice.route('/user/<uid>')
@admin_required
def user_index(uid):
    user = User.query.filter_by(id=uid).first()
    if not user:
        abort(404)
    return render_template_or_json("invoice/invoice-list.html", invoices=user.invoices)

@invoice.route('/<invoice_id>')
@login_required
def view(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id).first()
    if not invoice:
        abort(404)
    if can_access_invoice(invoice) is False:
        abort(403)
    return render_template_or_json("invoice/invoice-view.html", invoice=invoice)

@invoice.route('/<invoice_id>.pdf')
@login_required
def view_pdf(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id).first_or_404()
    if can_access_invoice(invoice) is False:
        abort(403)
    data = render_template("invoice/invoice-view-pdf.html", invoice=invoice)
    return render_pdf(HTML(string=data))

@invoice.route('/<invoice_id>.html')
@login_required
def view_html(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id).first_or_404()
    if can_access_invoice(invoice) is False:
        abort(403)
    return render_template("invoice/invoice-view-pdf.html", invoice=invoice)

@invoice.route('/<invoice_id>/credit')
@admin_required
def credit(invoice_id):
    user = get_session_user()
    invoice = Invoice.query.filter_by(id=invoice_id).first()
    if not invoice:
        abort(404)
    invoice.credit(invoice.total_due(), "Service credit (per {})".format(user.username))
    return redirect(url_for('.view', invoice_id=invoice.id))

@invoice.route('/unpaid')
@admin_required
def list_unpaid():
    invlist = Invoice.query.filter_by(payment_ts=None)
    return render_template_or_json("invoice/invoice-list.html", invoices=invlist)

@invoice.route('/svccredit', methods=['POST'])
@login_required
def creditamt():
    user = get_session_user()
    invoice = Invoice(user)
    creditamt = round(float(request.form.get('creditamt', 0)), 2)
    if creditamt < 1.00:
        return redirect(url_for('.index'))
    InvoiceItem(None, invoice, creditamt, 'Add Service Credit')
    PendingCreditItem(invoice)
    invoice.mark_ready(apply_credit=False)
    return redirect(url_for('.view', invoice_id=invoice.id))

@invoice.route('/<invoice_id>/svccredit')
@login_required
def credit_invoice(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id).first()
    if not invoice:
        abort(404)
    u = invoice.user
    total = invoice.total_due()

    if u.total_credit() > total:
        cred = ServiceCreditItem(u, -total, 'Invoice {}'.format(invoice.id))
        invoice.credit(total, 'Service Credit - {}'.format(cred.id))
    elif u.total_credit() > 0:
        tcred = u.total_credit()
        cred = ServiceCreditItem(u, -tcred, 'Invoice {}'.format(invoice.id))
        invoice.credit(tcred, 'Service Credit - {}'.format(cred.id))
        assert u.total_credit() == 0
    return redirect(url_for('.view', invoice_id=invoice.id))

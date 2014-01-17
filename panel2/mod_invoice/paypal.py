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

from flask import redirect, url_for, abort, flash, jsonify, make_response, request
from panel2 import app, db
from panel2.mod_invoice import invoice
from panel2.user import User, get_session_user, login_required, admin_required
from panel2.invoice import Invoice, InvoiceItem
from werkzeug.datastructures import ImmutableOrderedMultiDict
from urllib import urlencode
from collections import OrderedDict
import requests

@invoice.route('/<invoice_id>/ipn-post', methods=['POST'])
def ipn_post(invoice_id):
    request.parameter_storage_class = ImmutableOrderedMultiDict
    values = request.form

    if values['receiver_email'] != app.config['PAYPAL_EMAIL']:
        return 'INVALID'

    if values['mc_currency'] != 'USD':
        return 'INVALID'

    if values['payment_status'] != 'Completed':
        return 'INVALID'

    args = OrderedDict([('cmd', '_notify-validate')] + [(k, v) for k, v in values.iteritems()])
    validate_url = u'https://www.paypal.com/cgi-bin/webscr'

    r = requests.get(validate_url, params=args)
    if 'VERIFIED' not in r.text:
        return r.text

    # search for conflicting paypal payment by searching description
    reference = 'PayPal Payment - {}'.format(values['txn_id'])
    inv_item = InvoiceItem.query.filter_by(description=reference).first()
    if inv_item:
        return 'DUPLICATE'

    invoice = Invoice.query.filter_by(id=invoice_id).first()
    invoice.credit(float(values['mc_gross']), reference)

    return r.text

@invoice.route('/fallback/ipn-post', methods=['POST'])
def ipn_fallback_post():
    return 'VERIFIED'

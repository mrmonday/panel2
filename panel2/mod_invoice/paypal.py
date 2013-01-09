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
from werkzeug.datastructures import ImmutableOrderedMultiDict
import requests

@invoice.route('/<invoice_id>/ipn-post')
def ipn_post(invoice_id):
    request.parameter_storage_class = ImmutableOrderedMultiDict()
    values = request.form

    for x, y in values.iteritems():
        arg += "&{x}={y}".format(x=x,y=y)

    validate_url = 'https://www.paypal.com' \
       '/cgi-bin/webscr?cmd=_notify-validate{arg}' \
       .format(arg=arg)

    print 'Validating IPN using {url}'.format(url=validate_url)

    r = requests.get(validate_url)
    if r.text not 'VERIFIED':
        return r.text

    invoice = Invoice.query.filter_by(id=invoice_id).first()
    invoice.mark_paid()

    return r.text



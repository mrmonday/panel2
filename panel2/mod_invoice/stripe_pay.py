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

from panel2 import app
from panel2.mod_invoice import invoice
from panel2.invoice import Invoice, InvoiceItem
from flask import request, flash, redirect, url_for
import stripe  # pip install --index-url https://code.stripe.com --upgrade stripe, https://stripe.com/docs/libraries

@invoice.route("/<invoice_id>/stripe_pay", methods=["POST"])
def stripe_pay(invoice_id):
    """ Accept Stripe payments for cards. Remember to set STRIPE_PRIVATE_KEY and STRIPE_PUBLIC_KEY in panel2.conf """
    invoice = Invoice.query.filter_by(id=invoice_id).first()
    stripe.api_key = app.config['STRIPE_PRIVATE_KEY']
    # Get the credit card details submitted by the form
    token = request.form['stripeToken']

    # Create the charge on Stripe's servers - this will charge the user's card
    try:
        charge = stripe.Charge.create(
            amount=request.form['amount'],  # amount in cents
            currency="usd",
            card=token,
            description="Invoice %s Payment - %s" % (invoice_id, app.config['NAME'])
        )
    except Exception as e:
        flash("An error occurred while processing your payment: " + e.args[0])
        return redirect(url_for('.index'))
    invoice.credit(invoice.total_due(), "Stripe Payment - %s (**** **** **** %s)" %
                                        (request.form['stripeEmail'], charge['card']['last4']))
    flash("Payment successfully processed: %s (for $%s)" % (invoice_id, invoice.total_due()))
    return redirect(url_for('.index'))

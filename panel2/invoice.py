#!/usr/bin/env python
"""
Copyright (c) 2013 TortoiseLabs LLC

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice, this permission notice and all necessary source code
to recompile the software are included or otherwise available in all
distributions.

This software is provided 'as is' and without any warranty, express or
implied.  In no event shall the authors be liable for any damages arising
from the use of this software.
"""

from panel2 import app, db
import time
import blinker

invoice_create_signal = blinker.Signal('A signal which is fired when an invoice is created')
invoice_paid_signal = blinker.Signal('A signal which is fired when an invoice is paid')

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creation_ts = db.Column(db.Integer)
    payment_ts = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='invoices')

    def __repr__(self):
        return "<Invoice {}>".format(self.id)

    def __init__(self, user):
        self.user_id = user.id
        self.user = user
        self.creation_ts = time.time()

        db.session.add(self)
        db.session.commit()

    def mark_ready(self):
        invoice_create_signal.send(app, invoice=self)
        if self.total_due() == 0:
            self.mark_paid()

    def mark_paid(self):
        self.payment_ts = time.time()

        db.session.add(self)
        db.session.commit()

        [item.mark_paid() for item in self.items]
        invoice_paid_signal.send(app, invoice=self)

    def total_due(self):
        return sum([child.price for child in self.items])

invoice_item_paid_signal = blinker.Signal('A signal which is fired when an invoice item is marked paid')

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255))
    entry_ts = db.Column(db.Integer)
    price = db.Column(db.Float)

    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    service = db.relationship('Service')

    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'))
    invoice = db.relationship('Invoice', backref='items')

    def __init__(self, service, invoice, price):
        self.description = '{} renewal'.format(service.name)
        self.entry_ts = time.time()
        self.price = price

        self.invoice_id = invoice.id
        self.invoice = invoice

        self.service_id = service.id
        self.service = service

        db.session.add(self)
        db.session.commit()

    def mark_paid(self):
        invoice_item_paid_signal.send(app, invoice=self.invoice, service=self.service, invoice_item=self)

@invoice_create_signal.connect_via(app)
def invoice_paid_sig_hdl(*args, **kwargs):
    invoice = kwargs.get('invoice', None)
    invoice.user.send_email('Invoice Created', 'email/invoice-new.txt', invoice=invoice)

@invoice_paid_signal.connect_via(app)
def invoice_paid_sig_hdl(*args, **kwargs):
    invoice = kwargs.get('invoice', None)
    invoice.user.send_email('Invoice Payment Received', 'email/invoice-paid.txt', invoice=invoice)

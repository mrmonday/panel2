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

from panel2 import app, db, cron
from panel2.user import User
from panel2.cron import DAILY

import time
import blinker
import requests
import json

invoice_create_signal = blinker.Signal('A signal which is fired when an invoice is created')
invoice_paid_signal = blinker.Signal('A signal which is fired when an invoice is paid')

class ExchangeRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    currency_name = db.Column(db.String(3))
    currency_value = db.Column(db.Float)

    def __repr__(self):
        return "<ExchangeRate {}>".format(self.currency_name)

    def __init__(self, currency_name, currency_value):
        self.currency_name = currency_name
        self.currency_value = currency_value

        db.session.add(self)
        db.session.commit()

    def convert_from(self, value):
        return value * self.currency_value

    def convert_to(self, value):
        return value / self.currency_value

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creation_ts = db.Column(db.Integer)
    payment_ts = db.Column(db.Integer)
    btc_adr = db.Column(db.String(255))

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
        if self.payment_ts:
            return

        self.payment_ts = time.time()

        db.session.add(self)
        db.session.commit()

        [item.mark_paid() for item in self.items]
        invoice_paid_signal.send(app, invoice=self)

    def credit(self, amount, description='Payment'):
        item = InvoiceItem(None, self, -amount, description)
        if self.total_due() == 0:
            self.mark_paid()
        return item

    def total_due(self):
        return sum([child.price for child in self.items])

    def total_btc_due(self):
        return sum([child.bitcoin_cost() for child in self.items])

    def btc_callback_url(self):
        return 'https://manage.tortois.es/invoice/{0}/btc-notify'.format(self.id)

    def bitcoin_address(self):
        if self.btc_adr:
            return self.btc_adr

        uri = 'https://blockchain.info/api/receive?method=create&address={0}&callback={1}'.format(app.config['BITCOIN_ADDRESS'], self.btc_callback_url())
        resp = requests.get(uri)
        try:
            resp_obj = json.loads(resp.text)
            self.btc_adr = resp_obj['input_address']
        except:
            return None

        db.session.add(self)
        db.session.commit()

        return self.btc_adr

    def _serialize(self):
        return dict(invoice=self.id, user=self.user.username, creation_ts=self.creation_ts, payment_ts=self.payment_ts,
                    total=self.total_due(),
                    items=[item._serialize() for item in self.items])

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

    def __repr__(self):
        return "<InvoiceItem {0}: {1} (${2})>".format(self.id, self.description, self.price)

    def __init__(self, service, invoice, price, description=None):
        if not description and service:
            self.description = '{} renewal'.format(service.name)
        else:
            self.description = description

        self.entry_ts = time.time()
        self.price = price

        self.invoice_id = invoice.id
        self.invoice = invoice

        if service:
            self.service_id = service.id
            self.service = service

        db.session.add(self)
        db.session.commit()

    def bitcoin_cost(self):
        btc = ExchangeRate.query.filter_by(currency_name='BTC').first()
        return btc.convert_to(self.price)

    def mark_paid(self):
        invoice_item_paid_signal.send(app, invoice=self.invoice, service=self.service, invoice_item=self)

    def _serialize(self):
        return dict(line_item=self.id, invoice=self.invoice_id, service=self.service.name, price=self.price,
                    btc_price=self.bitcoin_cost(), entry_ts=self.entry_ts)

@invoice_create_signal.connect_via(app)
def invoice_paid_sig_hdl(*args, **kwargs):
    invoice = kwargs.get('invoice', None)
    invoice.user.send_email('Invoice Created', 'email/invoice-new.txt', invoice=invoice)

@invoice_paid_signal.connect_via(app)
def invoice_paid_sig_hdl(*args, **kwargs):
    invoice = kwargs.get('invoice', None)
    invoice.user.send_email('Invoice Payment Received', 'email/invoice-paid.txt', invoice=invoice)

def due_invoices(user):
    return filter(lambda x: x.expiry is None or x.expiry - time.time() <= 604800, user.services)

def is_open_invoice_covering_service(user, service):
    open_invs = filter(lambda x: x.payment_ts is None, user.invoices)
    for i in open_invs:
        for line in i.items:
            if line.service.id == service.id:
                return True
    return False

@cron.task(DAILY)
def invoice_task():
    ctx = app.test_request_context()
    ctx.push()

    for user in User.query:
        print user.username
        due = due_invoices(user)
        if len(due) == 0:
            continue
        print user.username, len(due), "service(s) due"
        for service in list(due):
            if is_open_invoice_covering_service(user, service) is True:
                due.remove(service)
        print user.username, len(due), "service(s) not covered by prior invoices"
        if len(due) == 0:
            continue
        invoice = Invoice(user)
        for service in due:
            service.invoice(invoice)
        invoice.mark_ready()
        print user.username, "invoice ID", invoice.id
        print user.username, "invoice auto PAID?", invoice.payment_ts is not None

    ctx.pop()

@cron.task(DAILY)
def update_btc_exchange_rate():
    exc_table_json = requests.get('https://blockchain.info/ticker')
    exc_table = json.loads(exc_table_json.text)

    btc = ExchangeRate.query.filter_by(currency_name='BTC').first()
    btc.currency_value = exc_table['USD']['24h']

    db.session.add(btc)
    db.session.commit()

    print "BTC is now set to", btc.currency_value

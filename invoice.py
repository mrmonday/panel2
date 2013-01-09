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

import time

from panel2 import app
from panel2.user import User
from panel2.invoice import Invoice, InvoiceItem

def due_invoices(user):
    return filter(lambda x: x.expiry - time.time() <= 604800, user.services)

def is_open_invoice_covering_service(user, service):
    open_invs = filter(lambda x: x.payment_ts is None, user.invoices)
    for i in open_invs:
        for line in i.items:
            if line.service == service:
                return True
    return False

ctx = app.test_request_context()
ctx.push()

for user in User.query:
    due = due_invoices(user)
    if len(due) == 0:
        continue
    print user.username, len(due), "service(s) due"
    for service in due:
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

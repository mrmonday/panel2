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

from panel2 import db, mail, app

def strip_unprintable(s, printable="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!$%&'()*+,-./:;<=>?@[\\]^_`{|}~ \n"):
    return filter(lambda x: x in printable, s)

def is_email_valid(email):
    s = strip_unprintable(email)
    if '@' not in s:
        return False
    return True

def send_simple_email_list(recipients, subject, message):
    mail.send_message(subject=subject, body=message, recipients=recipients, sender=app.config['NOREPLY_MAIL'])

def send_simple_email(recipient, subject, message):
    send_simple_email_list([recipient], subject, message)

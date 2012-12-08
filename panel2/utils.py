#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
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

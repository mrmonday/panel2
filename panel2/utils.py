#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from panel2 import db

class CommitableMixIn(object):
    def commit(self):
        db.session.add(self)
        db.commit()

def strip_unprintable(s, printable="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!$%&'()*+,-./:;<=>?@[\\]^_`{|}~ \n"):
    return filter(lambda x: x in printable, s)

def is_email_valid(email):
    s = strip_unprintable(email)
    if '@' not in s:
        return False
    return True

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


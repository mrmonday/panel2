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

from panel2 import app, db

class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(255))
    type = db.Column(db.String(50))
    expiry = db.Column(db.Integer)
    price = db.Column(db.Float)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='services')

    __mapper_args__ = {'polymorphic_on': type}

    def create(self):
        pass

    def suspend(self):
        pass

    def destroy(self):
        pass

    def invoice(self, invoice):
        pass


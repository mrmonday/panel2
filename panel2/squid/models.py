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
from panel2 import app, db
from collections import OrderedDict

class SquidServers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.string(255))
    ipaddr = db.Column(db.string(255))
    port = db.Column(db.Integer)
    name = db.Column(db.string(255))

    def __init__(self, location, ipaddr, port, name):
        self.location = location
        self.ipaddr = ipaddr
        self.port = port
        self.name = name

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<SquidServer: '%s' [%s]>" % (self.name, self.ipaddr)

class SquidUsers(db.Model):
    squiduser = db.Column(db.string(255), primary_key=True) # this is what squid checks for
    password = db.Column(db.string(255))
    user = db.Column(db.string(255)) #tortoiselabs user
    enabled = db.Column(db.Boolean)

    def __init__(self, squiduser, password, user, enabled=1):
        self.squiduser = squiduser
        self.password = password
        self.user = user
        self.enabled = enabled

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<Squiduser: '%s' [%s]>" % (self.squiduser, self.user)

class access_log(db.Model):
    id = db.Column(db.Integer, auto_increment=True, primary_key=True)
    time_since_epoch= db.Column(db.Decimal)
    response_time = db.Column(db.Integer)
    client_src_ip_addr = db.Column(db.string(255))
    squid_request_status = db.Column(db.string(255))
    http_status_code = db.Column(db.string(255))
    reply_size = db.Column(db.Integer)
    request_method = db.Column(db.string(255))
    request_url = db.Column(db.string(255))
    squiduser = db.Column(db.string(255)) #corresponds to squidusers.squiduser test
    squid_hier_status = db.Column(db.string(255))
    ipaddr = db.Column(db.string(255)) # corresponds to squidservers.ipaddr
    mime_type = db.Column(db.string(255))

    def __init__(self, id, time_since_epoch, response_time, client_src_ip_addr, squid_request_status, http_status_code, reply_size, request_method, request_url, squiduser, squid_hier_status, ipaddr, mime_type ):
        self.id = id
        self.time_since_epoch = time_since_epoch
        self.response_time = response_time
        self.client_src_ip_addr = client_src_ip_addr
        self.squid_request_status = squid_request_status
        self.http_status_code = http_status_code
        self.reply_size = reply_size
        self.request_method = request_method
        self.request_url = request_url
        self.squiduser = squiduser
        self.squid_hier_status = squid_hier_status
        self.ipaddr = ipaddr
        self.mime_type = mime_type

        db.session.add(self)
        db.session.commit()
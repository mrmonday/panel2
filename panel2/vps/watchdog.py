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

import rrdtool, os, time
from panel2 import app, db, cron
from panel2.vps.models import Node, XenVPS
from panel2.cron import MONITORING
from ediarpc.rpc_client import ServerProxy

@cron.task(MONITORING)
def watchdog():
    print 'watchdog monitoring'
    nodes = Node.query.filter_by(skip_crons=False).all()
    for node in nodes:
        api = node.api(ServerProxy)
        dl = api.domain_list()
        checklist = XenVPS.query.filter_by(node_id=node.id).filter_by(watchdog=True).filter_by(is_entitled=True).all()
        deadlist = filter(lambda x: x.name not in dl and not x.has_pending_work(), checklist)

        print 'dead:', deadlist
        [vps.create() for vps in deadlist]
        for vps in node.vps:
            vps.online = vps.name in dl
            print "vps:", vps.name, vps.online
            db.session.add(vps)

    print "committing vps state --"
    db.session.commit()

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

import rrdtool, os, time
from panel2 import app
from panel2.vps.models import Node
from ediarpc.rpc_client import ServerProxy

RRDPATH = app.config['RRDPATH']

now = str(int(time.time()))

def make_path(nodename, vpsname, type):
    return RRDPATH + '/' + nodename + '-' + vpsname + '-' + type + '.rrd'

def make_cpu_rrd(path):
    rrdtool.create(str(path), '--step', '60',
                   'DS:cpu:COUNTER:666:0:10000',
                   'RRA:LAST:0.5:1:15000',
                   'RRA:MIN:0.5:60:1000', 'RRA:MIN:0.5:1440:1000',
                   'RRA:MAX:0.5:60:1000', 'RRA:MAX:0.5:1440:1000',
                   'RRA:AVERAGE:0.5:60:1000', 'RRA:AVERAGE:0.5:1440:1000')

def update_cpu_usage(nodename, vpsinfo):
    path = make_path(nodename, vpsinfo['name'], 'cpu')
    if not os.access(path, os.F_OK):
        make_cpu_rrd(path)
    cputime_msec = int(float(vpsinfo['cputime_sec'])*1000)
    rrdtool.update(str(path), '%s:%d' % (now, cputime_msec))

nodes = Node.query.all()
for node in nodes:
    api = node.api(ServerProxy)
    dl = api.domain_list()

    for vps in dl.keys():
        update_cpu_usage(node.name, dl[vps])

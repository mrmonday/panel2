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

import rrdtool, os, time, subprocess
from panel2 import app, cron
from panel2.vps.models import Node
from panel2.cron import MINUTELY
from ediarpc.rpc_client import ServerProxy

RRDPATH = app.config['RRDPATH']

now = str(int(time.time()))

def make_path(nodename, vpsname, type):
    return RRDPATH + '/' + nodename + '-' + vpsname + '-' + type + '.rrd'

def make_cpu_rrd(path):
    args = ["rrdtool", "create", path, '--step', '60',
                   'DS:cpu:COUNTER:666:0:10000',
                   'RRA:LAST:0.5:1:15000',
                   'RRA:MIN:0.5:60:1000', 'RRA:MIN:0.5:1440:1000',
                   'RRA:MAX:0.5:60:1000', 'RRA:MAX:0.5:1440:1000',
                   'RRA:AVERAGE:0.5:60:1000', 'RRA:AVERAGE:0.5:1440:1000']
    print ' '.join(args)
    subprocess.call(args)

def make_net_rrd(path):
    subprocess.call(['rrdtool', 'create', path, '--step', '60',
                   'DS:rxbytes:COUNTER:666:0:125000000',
                   'DS:txbytes:COUNTER:666:0:125000000',
                   'DS:rxpkts:COUNTER:666:0:125000000',
                   'DS:txpkts:COUNTER:666:0:125000000',
                   'RRA:LAST:0.5:1:15000',
                   'RRA:MIN:0.5:60:1000', 'RRA:MIN:0.5:1440:1000',
                   'RRA:MAX:0.5:60:1000', 'RRA:MAX:0.5:1440:1000',
                   'RRA:AVERAGE:0.5:60:1000', 'RRA:AVERAGE:0.5:1440:1000'])

def make_vbd_rrd(path):
    subprocess.call(['rrdtool', 'create', path, '--step', '60',
                   'DS:rdreq:COUNTER:666:0:125000000',
                   'DS:wrreq:COUNTER:666:0:125000000',
                   'DS:ooreq:COUNTER:666:0:125000000',
                   'RRA:LAST:0.5:1:15000',
                   'RRA:MIN:0.5:60:1000', 'RRA:MIN:0.5:1440:1000',
                   'RRA:MAX:0.5:60:1000', 'RRA:MAX:0.5:1440:1000',
                   'RRA:AVERAGE:0.5:60:1000', 'RRA:AVERAGE:0.5:1440:1000'])

def update_cpu_usage(nodename, vpsinfo):
    path = make_path(nodename, vpsinfo['name'], 'cpu')
    if not os.access(path, os.F_OK):
        make_cpu_rrd(path)
    cputime_msec = int(float(vpsinfo['cputime_sec'])*1000)
    try:
        rrdtool.update(str(path), '%s:%d' % (now, cputime_msec))
    except rrdtool.error as e:
        pass

def update_net_usage(nodename, vpsinfo):
    if vpsinfo['netif'] is None:
        return
    path = make_path(nodename, vpsinfo['name'], 'net')
    if not os.access(path, os.F_OK):
        make_net_rrd(path)
    netif = vpsinfo['netif']
    try:
        rrdtool.update(str(path), str("%s:%s:%s:%s:%s" % (now, netif['trans_bytes'], netif['recv_bytes'], netif['trans_packets'], netif['recv_packets'])))
    except rrdtool.error as e:
        pass

def update_vbd_usage(nodename, vpsinfo):
    if vpsinfo['blkif'].has_key('rd_req') is False:
        return
    path = make_path(nodename, vpsinfo['name'], 'vbd')
    if not os.access(path, os.F_OK):
        make_vbd_rrd(path)
    blkif = vpsinfo['blkif']
    try:
        rrdtool.update(str(path), str("%s:%s:%s:%s" % (now, blkif['rd_req'], blkif['wr_req'], blkif['oo_req'])))
    except rrdtool.error as e:
        pass

@cron.task(MINUTELY)
def rrdcrawl():
    print 'rrdcrawl!'
    nodes = Node.query.filter_by(skip_crons=False).all()
    for node in nodes:
        print 'crawling', node.name
        api = node.api(ServerProxy)
        dl = api.domain_list()

        for vps in dl.keys():
            update_cpu_usage(node.name, dl[vps])
            update_net_usage(node.name, dl[vps])
            update_vbd_usage(node.name, dl[vps])

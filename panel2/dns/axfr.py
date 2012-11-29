#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

import dns.query
import dns.zone
import dns.rdatatype
import dns.resolver

def print_record(pname, qtype, ttl, preference, content):
    print pname, qtype, ttl, preference, content

def do_axfr(nameserver, domain, callback=print_record):
    zone = dns.zone.from_xfr(dns.query.xfr(nameserver, domain))
    for name, node in zone.nodes.items():
        pname = ''
        if str(name) == '@':
            pname = domain
        else:
            pname = str(name) + '.' + domain

        rdatasets = node.rdatasets
        for rdataset in rdatasets:
            if rdataset.rdtype == dns.rdatatype.NS or \
               rdataset.rdtype == dns.rdatatype.SOA:
                continue

            for rdata in rdataset:
                qtype = dns.rdatatype.to_text(rdataset.rdtype)
                ttl = rdataset.ttl
                content = ''
                preference = 0
                if 'target' in rdata.__slots__:
                    content = str(rdata.target)
                    if content == '@':
                        content = domain + '.'
                    if content.endswith('.') is False:
                        content = content + '.' + domain + '.'
                elif 'address' in rdata.__slots__:
                    content = str(rdata.address)
                elif 'exchange' in rdata.__slots__:
                    preference = rdata.preference
                    content = str(rdata.exchange)
                    if content == '@':
                        content = domain + '.'
                    if content.endswith('.') is False:
                        content = content + '.' + domain + '.'
                else:
                    print "unhandled: %s" % rdata.__slots__
                    continue

                final_content = content.rstrip('.')
                callback(pname, qtype, ttl, preference, final_content)

if __name__ == '__main__':
    do_axfr('204.152.221.168', 'tortois.es')

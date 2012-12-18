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
from panel2.job import Job
from time import sleep
import socket

def wait(timeout=5):
    while True:
        # Synchronize ORM with database state, otherwise query will be
        # cached.
        db.session.commit()
        lst = Job.query.filter_by(start_ts=None).all()
        if len(lst) == 0:
            sleep(timeout)
            continue
        return lst

def run(job):
    job.checkout()

    sock = socket.create_connection((job.target_ip, int(job.target_port)))
    def read_loop(sock):
        data = []
        end = '}\r\n'
        while True:
            try:
                packet = sock.recv(1024)
                if end in packet:
                    data.append(packet[:packet.find(end)])
                    break
                data.append(packet)
                if len(data) > 1:
                    last_pair = data[-2] + data[-1]
                    if end in last_pair:
                        data[-2] = last_pair[:last_pair.find(end)]
                        data.pop()
                        break
            except:
                break
        return ''.join(data).strip() + '}'

    sock.sendall(job.request_envelope)
    response = read_loop(sock)
    job.checkin(response)
    sock.close()

def main():
    while True:
       jobs = wait()
       for job in jobs:
           run(job)

if __name__ == '__main__':
    main()

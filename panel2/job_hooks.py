#!/usr/bin/env python
"""
Copyright (c) 2013 TortoiseLabs LLC

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice, this permission notice and all necessary source code
to recompile the software are included or otherwise available in all
distributions.

This software is provided 'as is' and without any warranty, express or
implied.  In no event shall the authors be liable for any damages arising
from the use of this software.
"""

from panel2 import app
from panel2.job import job_checkin_signal, job_checkout_signal
from panel2.service import Service
import json
import requests

@job_checkin_signal.connect_via(app)
@job_checkout_signal.connect_via(app)
def send_webhook_notification(*args, **kwargs):
    job = kwargs.pop('job', None)
    if not job:
        return

    svc = Service.query.filter_by(id=job.refid).first()
    if not svc or not svc.user:
        return

    if not svc.user.job_webhook_uri:
        return

    st_base = {
        'refid': job.refid,
        'service': svc.name,
        'finished': job.is_finished(),
        'request_envelope': json.loads(job.request_envelope),
        'entry_ts': job.entry_ts,
        'start_ts': job.start_ts,
        'end_ts': job.end_ts,
    }

    if job.response_envelope:
        st_base['response_envelope'] = json.loads(job.response_envelope)

    st_json = json.dumps(st_base)

    r = requests.post(svc.user.job_webhook_uri, st_json, timeout=2.0)
    return (r.status_code == 200)

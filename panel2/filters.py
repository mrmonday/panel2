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

import hashlib
from datetime import datetime

from panel2 import app

@app.template_filter('gravatar')
def user_gravatar_url(email, size=24):
    return "https://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + ("?s=%d" % size)

@app.template_filter('strftime')
def strftime_filter(time=False, format='%c'):
    from datetime import datetime
    if type(time) is long:
        time = int(time)
    t = datetime.fromtimestamp(time)
    return t.strftime(format)

@app.template_filter('iso8601')
def iso8601_data(time=False):
    if type(time) is long:
        time = int(time)
    dtime = datetime.fromtimestamp(time)
    return dtime.strftime("%Y-%m-%dT%H:%M:%SZ")

@app.template_filter('time_ago')
def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc.  Pretty much ganked this from Atheme and rewrote
    it in python.
    """
    now = datetime.now()
    if type(time) is long:
        time = int(time)
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
        diff = now - time 
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return str( second_diff / 60 ) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str( second_diff / 3600 ) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff/7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff/30) + " months ago"
    return str(day_diff/365) + " years ago"

@app.template_filter('truncate')
def truncate(data, length=50):
    if len(data) < (length + 1):
        return data

    return data[0:length] + '...'

@app.template_filter('strf')
def strf(data, fmt):
    return fmt.format(data)


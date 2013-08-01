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
from panel2.user import get_session_user
from panel2.utils import render_template_or_json

from flask import redirect, url_for, flash, request

@app.route('/profile', subdomain=app.config['DEFAULT_SUBDOMAIN'])
@app.route('/profile/index', subdomain=app.config['DEFAULT_SUBDOMAIN'])
def profile_index():
    return render_template_or_json('profile.html')

@app.route('/profile/password', methods=['POST'], subdomain=app.config['DEFAULT_SUBDOMAIN'])
def profile_change_pw():
    user = get_session_user()
    if user.validate_password(request.form['oldpass']) is not True:
        flash('Your password was incorrect', 'error')
        return redirect(url_for('.profile_index'))

    user.assign_password(request.form['newpass'])
    flash('Your password has been changed', 'success')
    return redirect(url_for('.profile_index'))

@app.route('/profile/webhook-uri', methods=['POST'], subdomain=app.config['DEFAULT_SUBDOMAIN'])
def profile_webhook_uri():
    uri = request.form.get('webhook_uri', None)
    if uri and len(uri) == 0:
        uri = None

    user = get_session_user()
    user.job_webhook_uri = uri
    db.session.add(user)
    db.session.commit()

    flash('Your webhook URI has been changed', 'success')
    return redirect(url_for('.profile_index'))

@app.route('/profile/email', methods=['POST'], subdomain=app.config['DEFAULT_SUBDOMAIN'])
def profile_change_email():
    user = get_session_user()
    user.assign_email(request.form['new_email'])
    flash('Your e-mail address has been changed', 'success')
    return redirect(url_for('.profile_index'))

@app.route('/profile/new-apikey', subdomain=app.config['DEFAULT_SUBDOMAIN'])
def profile_new_key():
    user = get_session_user()
    user.set_api_key()
    flash('Your API key has been changed', 'success')
    return redirect(url_for('.profile_index'))

@app.route('/profile/new-totpkey', subdomain=app.config['DEFAULT_SUBDOMAIN'])
def profile_new_totp_key():
    user = get_session_user()
    user.set_totp_key()
    flash('Your TOTP key has been changed', 'success')
    return redirect(url_for('.profile_index'))

@app.route('/profile/totp/enable', subdomain=app.config['DEFAULT_SUBDOMAIN'])
def profile_totp_enable():
    user = get_session_user()
    user.require_totp = True
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('.profile_index'))

@app.route('/profile/totp/disable', subdomain=app.config['DEFAULT_SUBDOMAIN'])
def profile_totp_disable():
    user = get_session_user()
    user.require_totp = False
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('.profile_index'))


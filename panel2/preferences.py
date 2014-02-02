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

from panel2 import app, db
from panel2.user import get_session_user, login_required
from panel2.utils import render_template_or_json

from flask import redirect, url_for, flash, request

@app.route('/profile')
@app.route('/profile/index')
@login_required
def profile_index():
    return render_template_or_json('profile.html')

@app.route('/profile/password', methods=['POST'])
@login_required
def profile_change_pw():
    user = get_session_user()
    if user.validate_password(request.form['oldpass']) is not True:
        flash('Your password was incorrect', 'error')
        return redirect(url_for('.profile_index'))

    user.assign_password(request.form['newpass'])
    flash('Your password has been changed', 'success')
    return redirect(url_for('.profile_index'))

@app.route('/profile/webhook-uri', methods=['POST'])
@login_required
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

@app.route('/profile/email', methods=['POST'])
@login_required
def profile_change_email():
    user = get_session_user()

    user.email = request.form['new_email']
    user.organization = request.form['organization']
    user.contact_name = request.form['contact_name']
    user.address1 = request.form['address1']
    user.address2 = request.form['address2']
    user.city = request.form['city']
    user.state = request.form['state']
    user.country = request.form['country']
    user.phone = request.form['phone']
    user.zip = request.form['zip']

    db.session.add(user)
    db.session.commit()

    flash('Your contact information has been changed', 'success')
    return redirect(url_for('.profile_index'))

@app.route('/profile/new-apikey')
@login_required
def profile_new_key():
    user = get_session_user()
    user.set_api_key()
    flash('Your API key has been changed', 'success')
    return redirect(url_for('.profile_index'))

@app.route('/profile/new-totpkey')
@login_required
def profile_new_totp_key():
    user = get_session_user()
    user.set_totp_key()
    flash('Your TOTP key has been changed', 'success')
    return redirect(url_for('.profile_index'))

@app.route('/profile/totp/enable')
@login_required
def profile_totp_enable():
    user = get_session_user()
    user.require_totp = True
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('.profile_index'))

@app.route('/profile/totp/disable')
@login_required
def profile_totp_disable():
    user = get_session_user()
    user.require_totp = False
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('.profile_index'))


@app.route('/profile/login-preferences', methods=['POST'])
@login_required
def profile_login_preferences():
    user = get_session_user()
    user.set_login_preferences(request.form.get('success', 0), request.form.get('fail', 0))
    flash('Your login notice preferences have been updated', 'success')
    return redirect(url_for('.profile_index'))

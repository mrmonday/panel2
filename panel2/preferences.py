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

from panel2 import app
from panel2.models import get_session_user

from flask import render_template, redirect, url_for, flash, request

@app.route('/profile')
@app.route('/profile/index')
def profile_index():
    return render_template('profile.html')

@app.route('/profile/password', methods=['POST'])
def profile_change_pw():
    user = get_session_user()
    if user.validate_password(request.form['oldpass']) is not True:
        flash('Your password was incorrect', 'error')
        return redirect(url_for('.profile_index'))

    user.assign_password(request.form['newpass'])
    flash('Your password has been changed', 'success')
    return redirect(url_for('.profile_index'))

@app.route('/profile/email', methods=['POST'])
def profile_change_email():
    user = get_session_user()
    user.assign_email(request.form['new_email'])
    flash('Your e-mail address has been changed', 'success')
    return redirect(url_for('.profile_index'))


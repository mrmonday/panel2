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

import sys
import hashlib
import blinker

from panel2 import app, db
from panel2.user import User, Session, get_session_user, login_required_soft
from panel2.utils import is_email_valid, render_template_or_json
from flask import session, redirect, url_for, escape, request, get_flashed_messages, jsonify, escape
from sqlalchemy.exc import IntegrityError

login_signal = blinker.Signal('A signal sent when the user logs in')
logout_signal = blinker.Signal('A signal sent when the user logs out')
authfail_signal = blinker.Signal('A signal sent when the user fails authentication')

@login_signal.connect_via(app)
def handle_session_login(*args, **kwargs):
    user = kwargs.pop('user', None)
    sess = Session(user)
    session['session_id'] = sess.id
    session['session_challenge'] = sess.challenge

@logout_signal.connect_via(app)
def handle_session_logout(*args, **kwargs):
    sess = Session.query.filter_by(id=session['session_id']).first()

    if sess:
        db.session.delete(sess)
        db.session.commit()

    session.pop('session_id')
    session.pop('session_challenge')

def validate_login(username, password):
    u = User.query.filter_by(username=username).first()
    if u is None:
        authfail_signal.send(app, user=u, reason='Invalid username')
        return False
    if u.validate_password(password) is False:
        authfail_signal.send(app, user=u, reason='Invalid password')
        return False

    # Password validation was successful, fire the login event.
    login_signal.send(app, user=u)
    return True

@app.route('/totp-challenge', methods=['GET', 'POST'], subdomain=app.config['DEFAULT_SUBDOMAIN'])
@login_required_soft
def totp_challenge():
    if request.method == 'POST':
        user = get_session_user()
        response = int(request.form.get('response', 0))
        if not user.validate_totp(response):
            return redirect(url_for('totp_challenge'))
        sess = Session.query.filter_by(id=session['session_id']).first()
        if not sess:
            return redirect(url_for('login'))
        sess.totp_complete()
        return redirect(url_for('index'))

    return render_template_or_json('challenge.html')

@app.route('/login', methods=['GET', 'POST'], subdomain=app.config['DEFAULT_SUBDOMAIN'])
def login():
    if request.method == 'POST':
        user = validate_login(request.form['username'], request.form['password'])
        if user is not False:
            u = get_session_user()
            if not u.require_totp:
                return redirect(url_for('index'))
            else:
                return redirect(url_for('totp_challenge'))
        else:
            session.pop('session_id', None)
            session.pop('session_challenge', None)
            return render_template_or_json('login.html', error='Invalid username or password')

    return render_template_or_json('login.html')

@app.route('/logout', subdomain=app.config['DEFAULT_SUBDOMAIN'])
def logout():
    _user = get_session_user()
    if _user is not None:
        logout_signal.send(app, user=_user)

    return redirect(url_for('index'))

@app.route('/create', methods=['GET', 'POST'], subdomain=app.config['DEFAULT_SUBDOMAIN'])
def create():
    if request.method == 'POST':
        try:
            username = request.form['username'].strip().rstrip()
            password = request.form['password'].strip().rstrip()
            email = request.form['email'].strip().rstrip()
            if len(username) == 0:
                return render_template_or_json('create.html', error='No username provided') 
            if len(password) == 0:
                return render_template_or_json('create.html', error='No password provided') 
            if len(email) == 0:
                return render_template_or_json('create.html', error='No email provided') 
            user = User(username, password, email)
        except:
            return render_template_or_json('create.html', error='Username is already taken')
            
        if user is not None:
            sess = Session(user)
            session['session_id'] = sess.id
            session['session_challenge'] = sess.challenge
            return redirect(url_for('index'))

    return render_template_or_json('create.html')

@app.route('/reset', methods=['GET', 'POST'], subdomain=app.config['DEFAULT_SUBDOMAIN'])
def reset_ui():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().rstrip()
        email = request.form.get('email', '').strip().rstrip()
        user = User.query.filter_by(username=username).filter_by(email=email).first()

        if not user:
            return render_template_or_json('lost-password.html', error='The information provided does not match any account on file')

        user.set_pwreset_key()
        user.send_email('Please confirm your password reset request', 'email/lost-password-confirm.txt')

        return render_template_or_json('lost-password.html', error='A confirmation message has been sent to the e-mail address on file')

    return render_template_or_json('lost-password.html')

@app.route('/reset-confirm/<pwreset_key>', methods=['GET', 'POST'], subdomain=app.config['DEFAULT_SUBDOMAIN'])
def reset_confirm(pwreset_key):
    user = User.query.filter_by(pwreset_key=pwreset_key).first_or_404()

    if request.method == 'POST':
        password = request.form['password'].strip().rstrip()
        user.assign_password(password)
        user.set_pwreset_key()

        return redirect(url_for('login'))

    return render_template_or_json('lost-password-confirm.html', user=user)

@app.route('/notifications.json', methods=['GET', 'POST'], subdomain=app.config['DEFAULT_SUBDOMAIN'])
def notifications():
    messages = get_flashed_messages(with_categories=True)
    return jsonify({'messages': [{'type': type, 'message': escape(message)} for type, message in messages]})

@app.context_processor
def user_information_from_session():
    """A decorated function to give the templates a user object if we're logged in."""
    _user = get_session_user()
    if _user is not None:
        return dict(user=_user)

    return dict()

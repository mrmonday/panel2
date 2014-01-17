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

from panel2 import db, mail, app
from flask import render_template, request

import json

def strip_unprintable(s, printable="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!$%&'()*+,-./:;<=>?@[\\]^_`{|}~ \n"):
    return filter(lambda x: x in printable, s)

def is_email_valid(email):
    s = strip_unprintable(email)
    if '@' not in s:
        return False
    return True

def send_simple_email_list(recipients, subject, message):
    mail.send_message(subject=subject, body=message, recipients=recipients, sender=app.config['NOREPLY_MAIL'])

def send_simple_email(recipient, subject, message):
    send_simple_email_list([recipient], subject, message)

def serialize_obj(obj):
    if type(obj) is dict:
        lst = {}
        for k, v in obj:
            lst[k] = serialize_obj(v)
        return lst
    if hasattr(obj, '__iter__'):
        lst = []
        for child in obj.__iter__():
            lst.append(serialize_obj(child))
        return lst

    if hasattr(obj, '_serialize'):
        return obj._serialize()
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()

    try:
        json.dumps(obj)
    except:
        return None

    return obj

def to_json(obj):
    """Serialize an object to a JSON structure, if it supports serialization.

       This means, basically, that if an object implements _serialize(), we will take the
       result of that and convert it to JSON.

       So, here's how this works... kinda... sorta...

       class Creature(db.Model):
           __tablename__ = 'creatures'
           id = db.Column(db.Integer)
           species = db.Column(db.String(255))
           vertebrate = db.Column(db.Boolean)
           vegetarian = db.Column(db.Boolean)
           sound = db.Column(db.String(255))

           def __init__(self, species, sound, vertebrate=True, vegetarian=False, *args, **kwargs):
               self.species = species
               self.sound = sound
               self.vertebrate = vertebrate
               self.vegetarian = vegetarian
               self.polkadotted = kwargs.pop('polkadotted', None)

           def __repr__(self):
               return "The %s says '%s'." % (self.species, self.sound)

           def _serialize(self):
               return dict(species=self.species, vertebrate=self.vertebrate, vegetarian=self.vegetarian, sound=self.sound)

       cat = Creature('Feline', 'Meow!')
       dragon = Creature('Dragon', 'Rawr!')
       mouse = Creature('Mouse', 'Squeak!')
       shiro = Creature('Lupine', 'Howl!', vegetarian=True, polkadotted=True)

       >>> to_json(cat)
       '{'species': 'Feline', 'vertebrate': true, 'vegetarian': false, 'sound': 'Meow!'}'

       Everything looks good, there...

       >>> to_json(shiro)
       '{'species': 'Lupine', 'vertebrate': true, 'vegetarian': true, 'sound': 'Howl!'}'

       You may notice that the 'polkadotted' attribute here is not mentioned.  This is because the _serialize() function
       only handles a static set of fields in this example.  You might want to dynamically generate the dictionary if this
       is a problem, but that isn't covered here.
    """
    try:
        return json.dumps(obj)
    except:
        pass

    if hasattr(obj, '_serialize'):
        return json.dumps(obj._serialize())
    elif hasattr(obj, 'to_dict'):
        return json.dumps(obj.to_dict())

    # Nothing to serialize, so just return back 'null'
    return json.dumps(None)

def request_wants_json():
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    xhr = request.headers.get('X-Requested-With', '') == 'XMLHttpRequest'
    return xhr or (best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html'])

def render_template_or_json(template, **kwargs):
    if request.authorization or request_wants_json():
        structure = dict()
        for k, v in kwargs.iteritems():
            structure[k] = serialize_obj(v)
        return json.dumps(structure)

    return render_template(template, **kwargs)

# Copyright (C) 2018 Foundries.io
# Author: Andy Doan <andy@foundries.io>
from flask import Blueprint, current_app, jsonify

blueprint = Blueprint('devices', __name__, url_prefix='/devices')


@blueprint.route('/')
def list():
    user = current_app.OTAUser()
    r = jsonify([x for x in user.device_list()])
    maxd = user.max_devices
    if maxd != -1:
        r.headers['X-MAX-DEVICES'] = maxd
    return r


@blueprint.route('/<name>/')
def get(name):
    user = current_app.OTAUser()
    return jsonify(user.device_get(name))

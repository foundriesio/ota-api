# Copyright (C) 2018 Foundries.io
# Author: Andy Doan <andy@foundries.io>
from flask import (
    Blueprint, abort, current_app, jsonify, make_response, request
)

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


@blueprint.route('/<name>/packages/')
def packages(name):
    user = current_app.OTAUser()
    return jsonify(user.device_packages(name))


@blueprint.route('/<name>/updates/')
def updates(name):
    user = current_app.OTAUser()
    return jsonify(user.device_updates(name))


@blueprint.route('/<name>/', methods=('PUT',))
def update(name):
    data = request.get_json() or {}
    image = data.get('image')
    if not image:
        message = 'Missing required field: "image"'
        abort(make_response(jsonify(message=message), 400))
    if 'hash' not in image:
        message = 'Missing required field: "image[hash]"'
        abort(make_response(jsonify(message=message), 400))

    user = current_app.OTAUser()
    return jsonify(user.device_update(name, image['hash']))


@blueprint.route('/<name>/', methods=('PATCH',))
def patch(name):
    data = request.get_json() or {}

    enabled = data.get('auto-updates', None)
    if enabled is not None:
        user = current_app.OTAUser()
        return jsonify(user.device_enable_autoupdates(name, enabled))

    message = 'Input must include "auto-updates" attribute'
    abort(make_response(jsonify(message=message), 400))

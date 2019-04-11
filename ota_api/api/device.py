# Copyright (C) 2018 Foundries.io
# Author: Andy Doan <andy@foundries.io>
from flask import (
    Blueprint, abort, current_app, jsonify, make_response, request
)

from ota_api.sota_toml import sota_toml_fmt

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


@blueprint.route('/<name>/history/')
def install_list(name):
    user = current_app.OTAUser()
    return jsonify(user.device_install_history(name))


@blueprint.route('/<name>/history/<correlation_id>/')
def install_get(name, correlation_id):
    user = current_app.OTAUser()
    return jsonify(user.device_install_get(name, correlation_id))


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

    new_name = data.get('name')
    if new_name:
        return jsonify(current_app.OTAUser().device_rename(name, new_name))

    enabled = data.get('auto-updates', None)
    if enabled is not None:
        user = current_app.OTAUser()
        return jsonify(user.device_enable_autoupdates(name, enabled))

    message = 'Input must include "auto-updates" attribute'
    abort(make_response(jsonify(message=message), 400))


@blueprint.route('/<name>/', methods=('DELETE',))
def delete(name):
    current_app.OTAUser().device_delete(name)
    return jsonify({})


def _require_keys(dictionary, keys):
    missing = []
    for k in keys:
        try:
            yield dictionary[k]
        except KeyError:
            missing.append(k)
    if missing:
        message = 'Missing field(s): %s' % ', '.join(missing)
        abort(make_response(jsonify(message=message), 400))


@blueprint.route('/', methods=('POST',))
def post():
    data = request.get_json() or {}
    name, uuid, csr, hwid = _require_keys(
        data, ('name', 'uuid', 'csr', 'hardware-id'))

    user = current_app.OTAUser()

    user.assert_device_quota()

    overrides = data.get('overrides', {})
    overrides.setdefault(
        'provision', {}).setdefault('primary_ecu_hardware_id', hwid)

    client_pem = user.device_cert_create(name, uuid, csr)
    user.device_create(name, uuid, client_pem)
    r = jsonify({
        'root.crt': user.server_ca,
        'sota.toml': sota_toml_fmt(overrides=overrides),
        'client.pem': client_pem,
    })
    r.status_code = 201
    return r

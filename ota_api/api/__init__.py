# Copyright (C) 2018 Foundries.io
# Author: Andy Doan <andy@foundries.io>

from flask import Blueprint


def register_blueprints(app):
    from ota_api.api.device import blueprint as device_blueprint  # NOQA
    for obj in locals().values():
        if isinstance(obj, Blueprint):
            app.register_blueprint(obj)

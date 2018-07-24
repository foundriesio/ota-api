# Copyright (C) 2018 Foundries.io
# Author: Andy Doan <andy@foundries.io>
from importlib import import_module

from flask import Flask

from werkzeug.contrib.fixers import ProxyFix


def create_app(settings_object='ota_api.settings'):
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.config.from_object(settings_object)

    module, clazz = app.config['USER_MODULE'].split(':')
    module = import_module(module)
    app.OTAUser = getattr(module, clazz)

    import ota_api.api
    ota_api.api.register_blueprints(app)

    return app

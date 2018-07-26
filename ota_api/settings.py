# Copyright (C) 2018 Foundries.io
# Author: Andy Doan <andy@foundries.io>

import os

USER_MODULE = os.environ.get('USER_MODULE', 'ota_api.ota_user:UnsafeUser')
GATEWAY_SERVER = os.environ.get(
    'GATEWAY_SERVER', 'https://ota-ce.example.com:8443')

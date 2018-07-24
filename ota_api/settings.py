# Copyright (C) 2018 Foundries.io
# Author: Andy Doan <andy@foundries.io>

import os

USER_MODULE = os.environ.get('USER_MODULE', 'ota_api.ota_user:UnsafeUser')

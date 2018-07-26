# Copyright (C) 2018 Foundries.io
# Author: Andy Doan <andy@foundries.io>
import string

from flask import abort, jsonify, make_response, request

from ota_api.ota_ce import OTACommunityEditionAPI
from ota_api.settings import GATEWAY_SERVER

VALID_DEVICE_CHAR = set(string.ascii_letters + string.digits + '-' + '_' + '/')

SOTA_TOML_FMT = '''
[gateway]
http = true
socket = false

[network]
socket_commands_path = "/tmp/sota-commands.socket"
socket_events_path = "/tmp/sota-events.socket"
socket_events = "DownloadComplete, DownloadFailed"

[p11]
module = ""
pass = ""
uptane_key_id = ""
tls_ca_id = ""
tls_pkey_id = ""
tls_clientcert_id = ""

[tls]
server = "{gateway_server}"
ca_source = "file"
pkey_source = "file"
cert_source = "file"

[provision]
server = "{gateway_server}"
p12_password = ""
expiry_days = "36000"
provision_path = ""

[uptane]
polling = true
polling_sec = 10
device_id = ""
primary_ecu_serial = ""
primary_ecu_hardware_id = "{hardware_id}"
director_server = "{gateway_server}/director"
repo_server = "{gateway_server}/repo"
key_source = "file"

[pacman]
type = "ostree"
os = ""
sysroot = ""
ostree_server = "{gateway_server}/treehub"
packages_file = "/usr/package.manifest"

[storage]
type = "filesystem"
path = "/var/sota/"
uptane_metadata_path = "metadata"
uptane_private_key_path = "ecukey.der"
uptane_public_key_path = "ecukey.pub"
tls_cacert_path = "root.crt"
tls_pkey_path = "pkey.pem"
tls_clientcert_path = "client.pem"

[import]
uptane_private_key_path = ""
uptane_public_key_path = ""
tls_cacert_path = "/var/sota/root.crt"
tls_pkey_path = ""
tls_clientcert_path = ""
'''


class OTAUserBase(object):
    @property
    def max_devices(self):
        """Return the maximum number of devices a user can create."""
        raise NotImplementedError()

    def assert_device_quota(self):
        """Ensure that creating another device is allowed."""
        maxd = self.max_devices
        if maxd > 0 and len(list(self.device_list())) > maxd:
            message = 'MAX_DEVICES(%d) exceeded' % self.max_devices
            abort(make_response(jsonify(message=message), 403))

    def device_list(self):
        """This gives a developer the ability to provide restrictions on what
           devices a user can see.
        """
        api = OTACommunityEditionAPI('default')
        for d in api.device_list():
            d['deviceStatus'] = api.device_status(d)
            d['deviceImage'] = api.device_image(d)
            yield d

    def _get(self, name):
        api = OTACommunityEditionAPI('default')
        d = api.device_get(name)
        if d:
            return api, d
        message = 'Device(%s) does not exist' % name
        abort(make_response(jsonify(message=message), 404))

    def device_get(self, name):
        """This gives a developer the ability to provide restrictions on what
           devices a user can look up.
        """
        api, d = self._get(name)
        d['deviceStatus'] = api.device_status(d)
        d['deviceImage'] = api.device_image(d)
        d['hardwareInfo'] = api.device_hardware(d)
        d['networkInfo'] = api.device_network(d)
        if d['deviceImage']:
            d['autoUpdates'] = api.device_autoupdates_enabled(
                d, d['deviceImage']['id'])
        else:
            d['autoUpdates'] = False
        return d

    def device_packages(self, name):
        api, d = self._get(name)
        offset = request.args.get('offset', 0)
        limit = request.args.get('limit', 50)
        return api.device_packages(d, offset, limit)

    def device_updates(self, name):
        api, d = self._get(name)
        u = api.device_updates(d)
        return sorted(u, reverse=True, key=lambda x: x['custom']['updatedAt'])

    def device_update(self, name, image_hash):
        api, d = self._get(name)
        return api.device_update(d, image_hash)

    def device_enable_autoupdates(self, name, enabled):
        api, d = self._get(name)
        api.device_autoupdates_set(d, enabled)

    def device_name_validate(self, name):
        bad = set(name) - VALID_DEVICE_CHAR
        if bad:
            message = 'Invalid device name. Invalid characters: %r' % bad
            abort(make_response(jsonify(message=message), 400))

    def device_rename(self, name, new_name):
        api, d = self._get(name)
        self.device_name_validate(new_name)
        api.device_rename(d, new_name)

    def device_delete(self, name):
        api, d = self._get(name)
        api.device_delete(d)

    def device_create(self, name, uuid, client_pem):
        api = OTACommunityEditionAPI('default')
        api.device_create(name, uuid, client_pem)

    def device_toml(self, hardware_id):
        """Return the sota.toml needed by aktualizr."""
        return SOTA_TOML_FMT.format(
            gateway_server=GATEWAY_SERVER, hardware_id=hardware_id)

    def device_cert_create(self, name, uuid, csr):
        """Create a certificate with your CA based on the incoming Certificate
           Signing Request.
        """
        self.device_name_validate(name)
        raise NotImplementedError()

    @property
    def server_ca(self):
        """Return the contents of your ota-community-edition's
           generated/<site>/server_ca.pem file
        """
        raise NotImplementedError()


class UnsafeUser(OTAUserBase):
    """An unsafe example of implementing the OTAUserBase class."""
    USERS = ('foo', 'bar')

    def __init__(self):
        key = request.headers.get('OTA-TOKEN', None)
        if not key or key not in self.USERS:
            abort(make_response(
                jsonify(message='Authorization required'), 401))

    @property
    def max_devices(self):
        return 10

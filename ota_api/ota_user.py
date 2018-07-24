# Copyright (C) 2018 Foundries.io
# Author: Andy Doan <andy@foundries.io>
from flask import abort, jsonify, make_response, request

from ota_api.ota_ce import OTACommunityEditionAPI


class OTAUserBase(object):
    @property
    def max_devices(self):
        """Return the maximum number of devices a user can create."""
        raise NotImplementedError()

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

# Copyright (C) 2018 Foundries.io
# Author: Andy Doan <andy@foundries.io>
import os
import functools

import requests

from flask import abort, make_response, jsonify
from werkzeug.exceptions import HTTPException

DIRECTOR_URL = os.environ.get('DIRECTOR_URL', 'http://director')
REGISTRY_URL = os.environ.get('REGISTRY_URL', 'http://device-registry')
REPO_URL = os.environ.get('REPO_URL', 'http://tuf-reposerver')


class _Server(object):
    def __init__(self, namespace, base_url):
        self._base = base_url
        self._namespace = namespace
        self.get = functools.partial(self.request, requests.get)
        self.post = functools.partial(self.request, requests.post)
        self.put = functools.partial(self.request, requests.put)
        self.delete = functools.partial(self.request, requests.delete)

    def request(self, method, resource, *args, **kwargs):
        headers = kwargs.get('headers')
        if not headers:
            kwargs['headers'] = {}
        kwargs['headers']['x-ats-namespace'] = self._namespace

        resp = method(self._base + resource, *args, **kwargs)
        expected = 200
        if method.__name__ == 'post':
            expected = 201
        if resp.status_code != expected:
            try:
                data = resp.json()
            except ValueError:
                data = {'text': resp.text}
            data['ota-source'] = self._base + resource
            abort(make_response(jsonify(data), resp.status_code))
        return resp


class OTACommunityEditionAPI(object):
    def __init__(self, namespace):
        self.director = _Server(namespace, DIRECTOR_URL)
        self.registry = _Server(namespace, REGISTRY_URL)
        self.repo = _Server(namespace, REPO_URL)

    def tuf_targets(self):
        r = self.repo.get('/api/v1/user_repo/targets.json')
        return r.json()['signed']['targets']

    def device_list(self, regex=None):
        params = {'offset': 0, 'limit': 100, 'regex': regex}
        while True:
            d = self.registry.get('/api/v1/devices', params=params).json()
            for device in d['values']:
                yield device

            params['offset'] = params['limit'] + params['offset']
            if params['offset'] >= d['total']:
                break

    def device_get(self, name):
        params = {'deviceId': name}
        data = self.registry.get('/api/v1/devices', params=params).json()
        if data:
            return data[0]

    def device_image(self, device):
        if device['deviceStatus'] == 'NotSeen':
            return None
        r = self.director.get('/api/v1/admin/devices/' + device['uuid'])
        return r.json()[0]

    def device_hardware(self, device):
        resource = '/api/v1/devices/' + device['uuid'] + '/system_info'
        try:
            return self.registry.get(resource).json()[0]
        except KeyError:
            # device hasn't yet registerd
            return {}

    def device_network(self, device):
        resource = '/api/v1/devices/' + device['uuid'] + '/system_info/network'
        try:
            return self.registry.get(resource).json()
        except KeyError:
            # device hasn't yet registered
            return {}
        except HTTPException as e:
            if e.response.status_code == 404:
                # device hasn't reported network info yet
                return {}

    def device_packages(self, device, offset, limit):
        params = {'offset': offset, 'limit': limit}
        resource = '/api/v1/devices/' + device['uuid'] + '/packages'
        return self.registry.get(resource, params=params).json()

    def device_status(self, device):
        if device['deviceStatus'] != 'Outdated':
            return device['deviceStatus']

        r = self.director.get(
            '/api/v1/admin/devices/' + device['uuid'] + '/queue')
        q = r.json()
        if len(q) == 0:
            # race condition, we need to probe our status again to be safe
            # i'm cheating for now
            return 'OK/TODO'
        for k, v in q[0]['targets'].items():
            return 'Updating to ' + v['image']['filepath']

    def device_updates(self, device):
        targets = self.tuf_targets()
        image = self.device_image(device)
        if not image:
            # The device has yet to be seen
            return
        image_hash = image['image']['hash']['sha256']
        for target in targets.values():
            if image['hardwareId'] in target['custom']['hardwareIds']:
                if image_hash == target['hashes']['sha256']:
                    target['active'] = True
                yield target

    def device_update(self, device, image_hash):
        """Looks at targets.json for an image that matches the search key and
           value. The key can bey either by "hash" or "name".
        """
        targets = self.tuf_targets()
        cur_image = self.device_image(device)
        hwid = cur_image['hardwareId']
        for target_name, data in targets.items():
            if data['hashes']['sha256'] == image_hash:
                break
        else:
            message = 'Could not find image with hash=%s' % image_hash
            abort(make_response(jsonify(message=message), 404))

        mtu = {
            'targets': {
                hwid: {
                    'to': {
                        'target': target_name,
                        'checksum': {
                            'method': 'sha256',
                            'hash': data['hashes']['sha256'],
                        },
                        'targetLength': data['length'],
                    },
                    'targetFormat': data['custom']['targetFormat'],
                    'generateDiff': False,
                }
            },
        }

        r = self.director.post('/api/v1/multi_target_updates', json=mtu)
        update = r.json()

        self.director.put(
            '/api/v1/admin/devices/%s/multi_target_update/%s' % (
                device['uuid'], update))
        return {'cur-image': cur_image, 'target-image': data}

    def device_delete(self, device):
        self.registry.delete('/api/v1/devices/' + device['uuid'])

    def device_create(self, name, uuid, client_pem):
        data = {
            'deviceUuid': uuid,
            'deviceId': name,
            'deviceName': name,
            'deviceType': 'Other',
            'credentials': client_pem,
        }
        self.registry.post('/api/v1/devices', json=data)

    def device_rename(self, device, new_name):
        data = {
            'deviceName': new_name,
            'deviceId': new_name,
            'deviceType': 'Other'
        }
        return self.registry.put(
            '/api/v1/devices/' + device['uuid'], json=data).json()

    def device_autoupdates_enabled(self, device, ecu):
        r = '/api/v1/admin/devices/%s/ecus/%s/auto_update' % (
            device['uuid'], ecu)
        r = self.director.get(r)
        return bool(r.json())

    def device_autoupdates_set(self, device, enabled):
        image = self.device_image(device)
        r = '/api/v1/admin/devices/%s/ecus/%s/auto_update' % (
            device['uuid'], image['id'])
        if not enabled:
            return self.director.delete(r).json()

        image_hash = image['image']['hash']['sha256']
        for t in self.tuf_targets().values():
            if image_hash == t['hashes']['sha256']:
                return self.director.put(r + '/' + t['custom']['name']).json()

        message = 'Could not find target to suscribe to.'
        abort(make_response(jsonify(message=message), 401))

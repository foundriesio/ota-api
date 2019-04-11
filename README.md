This project serves as an extensible example for adding a user facing REST
API to an [OTA Community Edition](https://github.com/advancedtelematic/ota-community-edition)
deployment. Its somewhat designed to follow on from the deployment described
in the Foundrie.io [OTA blog series](https://foundries.io/blog/2018/07/12/ota-part-4/).
However, it should be able to work with any OTA Community Edition deployment.

## Before You Begin
By using `kubectl proxy` you can actually develop this code locally within
a Python3 virtual environment.  If you've followed the steps in the blog
series, then you've been working with gcloud tools inside a Docker container.
`kubectl proxy` needs to run on the host OS, you'll first need to
[install it locally](https://kubernetes.io/docs/tasks/tools/install-kubectl/).
Once installed, you'll need to pull down your credentials with:
~~~
  gcloud container clusters get-credentials ota-ce
  # verify it works with:
  kubectl get pods
~~~

## Local Development
Local development is really easy. In one terminal run:
~~~
  kubectl proxy
~~~

In another terminal run:
~~~
  ./run-local.sh
~~~

This will run the code inside a virtual environment. You can then test the
API with commands like:
~~~
  # List all devices:
  curl -H "OTA-TOKEN: foo" http://localhost:5000/devices/

  # Get the details of a single device:
  curl -H "OTA-TOKEN: foo" http://localhost:5000/devices/<DEVICE>/

  # List packages installed on a device:
  curl -H "OTA-TOKEN: foo" http://localhost:5000/devices/<DEVICE>/packages/

  # List updates available to a device:
  curl -H "OTA-TOKEN: foo" http://localhost:5000/devices/<DEVICE>/updates/

  # List install history of device
  curl -H "OTA-TOKEN: foo" http://localhost:5000/devices/<DEVICE>/history/

  # Get the details of an install
  curl -H "OTA-TOKEN: foo" http://localhost:5000/devices/<DEVICE>/history/<correlationId>/

  # Delete a device:
  curl -H "OTA-TOKEN: foo" -X DELETE http://localhost:5000/devices/<DEVICE>/

  # Rename a device:
  curl -H "OTA-TOKEN: foo" -X PATCH -H "Content-type: application/json" \
    -d '{"name": "NEW_NAME"}' http://localhost:5000/devices/<DEVICE>/

  # Enable auto-updates:
  curl -H "OTA-TOKEN: foo" -X PATCH -H "Content-type: application/json" \
    -d '{"auto-updates": true}' http://localhost:5000/devices/<DEVICE>/

  # Trigger an update:
  curl -H "OTA-TOKEN: foo" -X PUT -H "Content-type: application/json" \
    -d '{"image": {"hash": "<HASH OF IMAGE>"}}' \
    http://localhost:5000/devices/DEVICE/
~~~

## Customize

The code base was designed so that you can provide your own `OTAUser`
implementation. Start with a simple template implementation like:
~~~
# put this file somwhere on your PYTHONPATH

from flask import abort, jsonify, make_response, request
from ota_api.ota_user import OTAUserBase

class CustomUser(OTAUserBase):
    USERS = ('custom')

    def __init__(self):
        # This is where you'd want to implement your own security by looking
	# at the request headers and figuring out if you know the user or not
        key = request.headers.get('OTA-TOKEN', None)
        if not key or key not in self.USERS:
            abort(make_response(
                jsonify(message='Authorization required'), 401))

    @property
    def max_devices(self):
        # This could be anything, -1 means there's no limit
        return 5

    def device_delete(self, name):
        # An example of overriding the base class. Lets remove the ability
	# to delete a device:
        abort(make_response(
            jsonify(message='Devices cannot be deleted'), 403))
~~~

This user module can then be used by running:
~~~
  # USER_MODULE='<module path>:<class name>' ./run-local.sh
  # eg:
  USER_MODULE='ota_api.custom_user:CustomUser' ./run-local.sh
~~~

#!/bin/sh -ex

HERE=$(dirname $(readlink -f $0))
cd $HERE

VENV="${VENV=/tmp/ota-api-venv}"
if [ ! -d $VENV ] ; then
	echo "Creating venv at: $VENV"
	python3 -m venv $VENV
	$VENV/bin/pip3 install flask requests
fi

NAMESPACE="${NAMESPACE-default}"

PROXY="http://localhost:8001/api/v1/namespaces/$NAMESPACE/services"
export DIRECTOR_URL="$PROXY/director/proxy"
export REGISTRY_URL="$PROXY/device-registry/proxy"
export REPO_URL="$PROXY/tuf-reposerver/proxy"

PYTHONPATH=./ FLASK_DEBUG=1 FLASK_APP=ota_api.app $VENV/bin/flask run

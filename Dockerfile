FROM alpine

ENV FLASK_APP=ota_api.app

COPY ./ota_api /srv/ota-api/ota_api
COPY ./docker_run.sh /

ENV PYTHONPATH=/srv/ota-api

RUN apk --no-cache add py3-flask py3-gunicorn py3-requests

EXPOSE 8000

CMD ["/docker_run.sh"]

FROM alpine

ENV FLASK_APP=ota_api.app

COPY ./ota_api /srv/ota-api/ota_api
COPY ./docker_run.sh /

ENV PYTHONPATH=/srv/ota-api

RUN apk --no-cache add py3-flask py3-gunicorn py3-requests py3-pip && \
	pip3 install pymysql==0.9.3

EXPOSE 8000

CMD ["/docker_run.sh"]

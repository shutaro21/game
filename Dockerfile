FROM nginx/unit:1.19.0-python3.7
COPY unit_config.json /docker-entrypoint.d/
COPY mysite /home/django/mysite/
COPY settings /home/django/settings/
RUN apt-get update                                                             \
    && apt-get install -y python3.7 python3-pip libmariadb-dev                 \
    && pip3 install -r /home/django/mysite/requirements.txt                    \
    && python3.7 /home/django/mysite/manage.py collectstatic                   \
    && rm -Rf /home/django/settings/

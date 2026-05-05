FROM python:3.11.3-alpine
LABEL owner="AFT"
LABEL environnement="dev"

ENV PYTHONUNBUFFERED=1

COPY ./mainapp /bourse/mainapp
COPY ./core /bourse/core
COPY ./scripts /bourse/scripts
COPY ./manage.py /bourse/manage.py
COPY ./requirements.txt /bourse/requirements.txt

WORKDIR bourse

EXPOSE 8004

RUN apk add --no-cache --virtual .build-deps gcc musl-dev graphviz graphviz-dev

RUN python3.11 -m venv /py && \
    /py/bin/pip install --upgrade pip setuptools wheel && \
    apk add --update --no-cache postgresql-client && \
    apk add --update --no-cache --virtual .temp-deps \
    build-base postgresql-dev musl-dev linux-headers cairo-dev && \
    /py/bin/pip install -r /bourse/requirements.txt && \
    adduser --disabled-password --no-create-home admin && \
    chmod -R +x /bourse/scripts

ENV PATH="/bourse/scripts:/py/bin:$PATH"

USER admin

CMD ["/bourse/scripts/run.sh"]
FROM python:3.6
MAINTAINER "remirampin@gmail.com"

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python && /root/.poetry/bin/poetry config virtualenvs.create false

WORKDIR /usr/src/app
COPY pyproject.toml poetry.lock manage.py ./
COPY call_your_mom call_your_mom
COPY website website
RUN /root/.poetry/bin/poetry install

CMD sh -c "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"

EXPOSE 8000

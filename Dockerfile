FROM python:3.6
MAINTAINER "remirampin@gmail.com"

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR /usr/src/app
RUN pip install pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install --deploy
COPY manage.py manage.py
COPY website website
COPY call_your_mom call_your_mom

CMD pipenv run sh -c "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"

EXPOSE 8000

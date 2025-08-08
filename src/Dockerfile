# pull official base image
FROM python:3.12-slim

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy requirements file
COPY ./requirements.txt /usr/src/app/requirements.txt

# install dependencies
RUN pip install -r /usr/src/app/requirements.txt

# copy alembic config and migrations
COPY ./alembic.ini /usr/src/app/alembic.ini
COPY ./alembic /usr/src/app/alembic

# copy project
COPY . /usr/src/app/

# (Optional) Entrypoint for running migrations before starting app
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
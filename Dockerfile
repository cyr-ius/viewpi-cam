# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-alpine

# set version label
ARG BUILD_DATE
ARG VERSION
LABEL build_version="version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL org.opencontainers.image.source="https://github.com/cyr-ius/viewpi-cam"
LABEL org.opencontainers.image.description="ViewPI Cam (inspired Rpi Cam Interface)"
LABEL org.opencontainers.image.licenses="MIT"
LABEL maintainer="cyr-ius"

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN apk add --no-cache libstdc++ py3-virtualenv
RUN apk add --no-cache --virtual build build-base python3-dev gcc linux-headers ninja

RUN python3 -m venv --system-site-packages /env 

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt && rm -rf requirements.txt

# clean content
RUN apk del build

COPY ./dockerfiles/docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Create folders
RUN mkdir -p /app/media /app/h264 /app/macros /app/system /app/static/css

COPY ./dockerfiles/etc /etc
COPY ./dockerfiles/bin/raspimjpeg /usr/local/bin/raspimjpeg
COPY ./dockerfiles/macros /app/macros

WORKDIR /app

COPY ./app ./app

VOLUME /app/static
VOLUME /app/macros
VOLUME /app/media
VOLUME /app/h264
VOLUME /app/system

EXPOSE 8000
ENTRYPOINT ["/docker-entrypoint.sh"]
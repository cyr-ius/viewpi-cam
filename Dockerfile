FROM python:3.11-alpine

# set version label
ARG BUILD_DATE
ARG VERSION
ARG TARGETPLATFORM
LABEL build_version="version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL org.opencontainers.image.source https://github.com/cyr-ius/viewpi-cam
LABEL org.opencontainers.image.description ViewPI Cam (inspired Rpi Cam Interface)
LABEL org.opencontainers.image.licenses MIT
LABEL maintainer="cyr-ius"

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN apk add --no-cache libstdc++
RUN apk add --no-cache --virtual build build-base python3-dev make gcc linux-headers ninja raspberrypi-dev git cmake bash

WORKDIR /tmp

# Build raspimjpeg
RUN git clone https://github.com/roberttidey/userland.git /tmp/raspimjpeg

RUN sed -i 's/sudo//g' raspimjpeg/buildme
RUN cd raspimjpeg;/bin/bash -c ./buildme /usr/bin

#Add library path
RUN echo "/lib:/usr/lib:/opt/vc/lib" > /etc/ld-musl-armhf.path

#Add binary path
RUN export PATH="${PATH}:/op/vc/bin"

# Install pip requirements
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt

# clean content
RUN apk del build

COPY ./dockerfiles/docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

# Create folders
RUN mkdir -p /app/media /app/h264 /app/macros /app/system /app/static/css

COPY ./dockerfiles/raspimjpeg /etc/raspimjpeg
COPY ./dockerfiles/macros /app/macros
RUN chmod -R +x /app/macros

WORKDIR /app

COPY ./app ./app

VOLUME /app/static
VOLUME /app/macros
VOLUME /app/media
VOLUME /app/h264
VOLUME /app/system

EXPOSE 8000
ENTRYPOINT ["/docker-entrypoint.sh"]
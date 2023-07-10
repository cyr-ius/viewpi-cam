# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-alpine

# set version label
ARG BUILD_DATE
ARG VERSION
LABEL build_version="version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL org.opencontainers.image.description="ViewPI Cam (inspired Rpi Cam Interface)"
LABEL maintainer="cyr-ius"

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN apk add --no-cache libstdc++
RUN apk add --no-cache --virtual build build-base python3-dev gcc linux-headers ninja


# Install pip requirements
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# clean content
RUN apk del build

COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Copy App
COPY ./app /app
COPY ./etc /etc
COPY ./bin/raspimjpeg /bin/raspimjpeg

RUN ["ln", "-sf", "/etc/raspimjpeg/raspimjpeg", "/app/raspimjpeg"]

RUN mkdir -p /app/media
RUN mkdir -p /app/h264
RUN mkfifo /app/FIFO
RUN mkfifo /app/FIFO1
RUN mkfifo /app/FIFO9

EXPOSE 8000
ENTRYPOINT ["/docker-entrypoint.sh"]
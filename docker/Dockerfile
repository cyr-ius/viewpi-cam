FROM alpine:3.18 AS builder

WORKDIR /app

RUN apk update && apk add --no-cache build-base git cmake bash make linux-headers
RUN git clone https://github.com/gpac/gpac.git gpac-master

WORKDIR /app/gpac-master

RUN ./configure --static-bin --use-zlib=no --prefix=/usr/bin
RUN make -j`nproc`

WORKDIR /app

RUN git clone --branch 5.10.3 https://github.com/cyr-ius/userland.git userland

WORKDIR /app/userland
RUN sed -i 's/sudo//g' buildme
RUN /bin/bash -c ./buildme

FROM python:3.11-alpine
WORKDIR /app

# Add binaries
COPY --from=builder /app/gpac-master/bin/gcc/MP4Box /usr/bin
COPY --from=builder /app/gpac-master/bin/gcc/gpac /usr/bin
COPY --from=builder /app/userland/build/bin /usr/bin
COPY --from=builder /app/userland/build/lib /usr/lib

# set version label
LABEL org.opencontainers.image.source https://github.com/cyr-ius/viewpi-cam
LABEL org.opencontainers.image.description ViewPI Cam (inspired by Rpi Cam Interface)
LABEL org.opencontainers.image.licenses MIT
LABEL maintainer="cyr-ius"

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN apk add --no-cache libstdc++
RUN apk add --no-cache --virtual build build-base python3-dev cmake make gcc linux-headers ninja git rust cargo libressl-dev

# Venv python
RUN python3 -m venv --system-site-packages --upgrade-deps /env
ENV VIRTUAL_ENV /env
ENV PATH $PATH:/env/bin

# Install pip requirements
ADD requirements.txt /tmp/
RUN /env/bin/pip3 install --upgrade pip wheel
RUN /env/bin/pip3 install --no-cache-dir --verbose -r /tmp/requirements.txt && rm -f /tmp/requirements.txt

# clean content
RUN apk del build

# Create folders
RUN mkdir -p /app/media /app/h264 /app/macros /app/system /app/static/css

ADD docker/raspimjpeg /etc/
ADD --chmod=744 docker/macros/* /app/macros/
ADD --chmod=744 docker/docker-entrypoint.sh /
ADD app ./app/

VOLUME /app/static
VOLUME /app/macros
VOLUME /app/media
VOLUME /app/h264
VOLUME /app/system

EXPOSE 8000/tcp
HEALTHCHECK CMD ["wget","--output-document=-","--quiet","--tries=1","http://127.0.0.1/"]
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn","app:create_app()"]

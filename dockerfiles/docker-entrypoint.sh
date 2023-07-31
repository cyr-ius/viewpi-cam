#!/bin/sh
echo /opt/vc/lib > /etc/ld.so.conf
ldconfig

# Raspimjpeg
cp /bin/raspimjpeg /opt/vc/bin/
chmod 755 /opt/vc/bin/raspimjpeg
if [ ! -e /usr/bin/raspimjpeg ]; then
   ln -s /opt/vc/bin/raspimjpeg /usr/bin/raspimjpeg
fi

# SHM
mkdir -p /dev/shm/mjpeg
touch /dev/shm/mjpeg/status_mjpeg.txt && chmod 766 /dev/shm/mjpeg/status_mjpeg.txt

# FIFO
mkdir -p /dev/raspimjpeg && chmod 766 /dev/raspimjpeg
mkfifo /dev/raspimjpeg/FIFO && chmod 766 /dev/raspimjpeg/FIFO
mkfifo /dev/raspimjpeg/FIFO1 && chmod 766 /dev/raspimjpeg/FIFO
mkfifo /dev/raspimjpeg/FIFO9 && chmod 766 /dev/raspimjpeg/FIFO

# Start Raspimjpeg
raspimjpeg > /dev/null 2>&1 &

# Static folder
cp -Rv ./app/ressources/css/fonts /app/static/css
cp -Rv ./app/ressources/extrastyles /app/static

# Assets
flask assets build

#Run scheduler
flask scheduler >/dev/null 2&>1 &

exec gunicorn --bind 0.0.0.0:8000 --workers 2 'app:create_app()' "$@"



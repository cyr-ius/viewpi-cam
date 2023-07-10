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
touch /dev/shm/mjpeg/status_mjpeg.txt
ln -sf /dev/shm/mjpeg/status_mjpeg.txt /app/status_mjpeg.txt

# Start Raspimjpeg
raspimjpeg > /dev/null 2>&1 &

# Static folder
mkdir -p /app/static/css
cp -Rv /app/ressources/css/fonts /app/static/css
cp -Rv /app/ressources/extrastyles /app/static

# Assets
flask assets build

#Run scheduler
python -m flask scheduler >/dev/null &

exec gunicorn --bind 0.0.0.0:8000 --workers 2 'app:create_app()' "$@"



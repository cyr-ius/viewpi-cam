#!/bin/sh
echo /opt/vc/lib > /etc/ld.so.conf
ldconfig

# Raspimjpeg
cp /bin/raspimjpeg /opt/vc/bin/
chmod 755 /opt/vc/bin/raspimjpeg
if [ ! -e /usr/bin/raspimjpeg ]; then
   ln -s /opt/vc/bin/raspimjpeg /usr/bin/raspimjpeg
fi

# Static folder
cp -Rv ./app/ressources/css/fonts /app/static/css
cp -Rv ./app/ressources/img /app/static

# Assets
flask assets build

#Run scheduler
# flask scheduler >/dev/null 2&>1 &

exec gunicorn --bind 0.0.0.0:8000 --workers 2 'app:create_app()' "$@"



pybabel extract -F babel.cfg -k lazy_gettext --project=viewpicam  -o app/messages.pot . && pybabel update -i app/messages.pot -d app/translations && pybabel compile -d app/translations

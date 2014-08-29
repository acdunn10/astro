source ~/venv/astro/bin/activate
django-admin.py startproject djastro --template=~/github/djprojects/project_template/
DJANGO_SETTINGS_MODULE=settings.local python djastro/manage.py runserver

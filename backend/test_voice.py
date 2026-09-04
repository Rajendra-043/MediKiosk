import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from voice.services import listen_and_ask

listen_and_ask()
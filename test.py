import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from ai.services import ask_ai


answer = ask_ai("Hello, I have a headache.")

print(answer)
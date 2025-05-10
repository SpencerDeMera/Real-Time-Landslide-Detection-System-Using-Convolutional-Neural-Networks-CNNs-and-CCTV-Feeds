import sys, os

print("PYTHON:", sys.executable)
print("PYTHONHOME:", os.environ.get("PYTHONHOME"))
print("PYTHONPATH:", os.environ.get("PYTHONPATH"))


os.chdir(os.path.join(os.path.dirname(__file__), 'DjangoProject'))
sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DjangoProject.realtime.settings")

from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000'])


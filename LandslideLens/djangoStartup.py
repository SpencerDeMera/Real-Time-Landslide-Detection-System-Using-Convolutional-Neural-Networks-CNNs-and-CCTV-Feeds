import os
import sys
import django
import shutil
from django.core.management import call_command

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DJANGO_DIR = os.path.join(BASE_DIR, "DjangoProject")
UPLOADS_DIR = os.path.join(DJANGO_DIR, "media", "uploads")
DB_PATH = os.path.join(DJANGO_DIR, "db.sqlite3")

# Add DjangoProject root to sys.path so submodule is importable
sys.path.insert(0, DJANGO_DIR)

# Set the correct Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DjangoProject.realtime.settings")
os.chdir(DJANGO_DIR)

# Setup Django
django.setup()

# Drop and recreate DB (if it's not in use)
if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
        print("Existing DB deleted.")
    except PermissionError:
        print("⚠️ Could not delete db.sqlite3 — file is in use. Skipping DB reset.")

# Run migrations regardless
print("Creating/migrating DB...")
call_command("migrate")

# Clear uploads folder
if os.path.exists(UPLOADS_DIR):
    for item in os.listdir(UPLOADS_DIR):
        item_path = os.path.join(UPLOADS_DIR, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)
    print("uploads folder cleaned.")
else:
    os.makedirs(UPLOADS_DIR)
    print("uploads folder created.")

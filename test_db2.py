import sys
import os
import django
sys.path.append(os.path.abspath('app/src/main/python'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from guilda_manager.models import Upgrade, GuildUpgrade
print("Upgrade count:", Upgrade.objects.count())
print("GuildUpgrade count:", GuildUpgrade.objects.count())

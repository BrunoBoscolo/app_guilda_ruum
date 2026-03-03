import urllib.request
import threading
import time
import os
import sys

# Start server in background
def run_server():
    os.system("cd app/src/main/python && python3 manage.py runserver 8000 > /dev/null 2>&1")

thread = threading.Thread(target=run_server)
thread.daemon = True
thread.start()

time.sleep(3) # wait for server to start

try:
    # Need to create a guild first, since views redirect to entry portal if no guild exists
    os.system("cd app/src/main/python && python3 manage.py shell -c \"from guilda_manager.models import Guild; Guild.objects.create(name='Test Guild', funds=10000)\"")

    # Now check the page
    req = urllib.request.Request('http://127.0.0.1:8000/construcoes/upgrades/')
    with urllib.request.urlopen(req) as response:
        html = response.read().decode()
        if 'id="buildings-data"' in html and 'id="upgrades-data"' in html:
            print("SUCCESS: upgrades page rendered properly with context data")
            sys.exit(0)
        else:
            print("FAILURE: missing context data elements")
            sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

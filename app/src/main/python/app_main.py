import os
import sys
import django
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from waitress import serve

def start_server():
    # 1. Configura o path para garantir que o Python ache seus módulos
    path = os.path.dirname(__file__)
    if path not in sys.path:
        sys.path.append(path)

    # 2. Aponta para o settings do seu projeto
    # IMPORTANTE: Verifique se a pasta 'config' é mesmo onde está seu settings.py
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    # 3. Setup Django and run migrations
    django.setup()
    try:
        call_command('migrate')
    except Exception as e:
        print(f"Error running migrations: {e}")

    # 4. Inicia a aplicação WSGI
    application = get_wsgi_application()

    print("--- INICIANDO SERVIDOR DJANGO NO ANDROID ---")

    # 5. Roda o servidor bloqueando a thread (o Kotlin cuida de rodar isso em background)
    serve(application, host='0.0.0.0', port=8000)
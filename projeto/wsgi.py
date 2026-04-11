import os
from django.core.wsgi import get_wsgi_application

# Certifique-se de que 'projeto.settings' é o caminho correto para o seu settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projeto.settings')

application = get_wsgi_application()
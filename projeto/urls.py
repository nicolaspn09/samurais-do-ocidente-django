from django.contrib import admin
from django.urls import path, include, re_path # Adicione re_path aqui
from django.conf import settings
from django.views.static import serve # Importe isso

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')), # Ou como estiver configurado o seu app
]

# ESTA É A CORREÇÃO: Força o servidor a entregar as imagens em produção
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Rotas Públicas
    path('', views.home, name='home'),
    path('afiliar/', views.afiliar, name='afiliar'),
    path('academias/', views.academias_list, name='academias'),
    path('atletas/', views.atletas_list, name='atletas'),
    
    # Rota de Exportação Admin
    path('exportar-atletas/', views.exportar_atletas_excel, name='exportar_atletas'),
    
    # ROTAS DO PORTAL DO ALUNO (Autenticação e Perfil)
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('perfil/', views.perfil_atleta, name='perfil'),
    path('perfil/inativar/', views.inativar_atleta, name='inativar_atleta'),
]
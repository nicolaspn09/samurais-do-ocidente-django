from django.db import models
from django.contrib import admin
from .models import Modalidade, Academia, Faixa, Atleta, HistoricoGraduacao, Midia, Noticia, PedidoAfiliacaoAtleta, PedidoAfiliacaoAcademia, Evento

@admin.register(Faixa)
class FaixaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ordem', 'is_preta', 'cor_hex')
    list_editable = ('is_preta',)
    ordering = ('ordem',)

@admin.register(Modalidade)
class ModalidadeAdmin(admin.ModelAdmin):
    list_display = ('nome',)

@admin.register(Academia)
class AcademiaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'nome_responsavel', 'endereco', 'ativo')
    list_filter = ('ativo', 'modalidades')
    filter_horizontal = ('professores', 'modalidades')
    
    # Filtra para o Professor ver apenas a própria academia
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(models.Q(responsavel=request.user) | models.Q(professores=request.user)).distinct()

class HistoricoGraduacaoInline(admin.TabularInline):
    model = HistoricoGraduacao
    fields = ('faixa', 'dan', 'data_graduacao', 'examinador')
    extra = 1
    # Apenas o Presidente pode adicionar/mudar histórico de faixa
    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(Atleta)
class AtletaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'academia', 'faixa_atual', 'dan_atual', 'ativo')
    list_filter = ('ativo', 'academia', 'faixa_atual', 'modalidades')
    inlines = [HistoricoGraduacaoInline]

    def get_readonly_fields(self, request, obj=None):
        # Bloqueia a alteração de faixa para quem não é o Presidente
        if not request.user.is_superuser:
            return ('faixa_atual', 'dan_atual')
        return ()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Professores só veem e editam os Atletas da própria academia
        return qs.filter(academia__responsavel=request.user)

@admin.register(Midia)
class MidiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'modalidade', 'academia_autora', 'data_postagem')
    
    def save_model(self, request, obj, form, change):
        # Preenche automaticamente a academia baseada no usuário logado (Professor)
        if not request.user.is_superuser and not change:
            if hasattr(request.user, 'academia'):
                obj.academia_autora = request.user.academia
        super().save_model(request, obj, form, change)

@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data_publicacao', 'ativa')
    list_filter = ('ativa', 'data_publicacao')
    search_fields = ('titulo', 'conteudo')

@admin.register(PedidoAfiliacaoAtleta)
class PedidoAtletaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'academia_desejada', 'status', 'data_pedido')
    list_filter = ('status', 'academia_desejada')
    search_fields = ('nome', 'cpf', 'email')
    readonly_fields = ('data_pedido', 'termo_lgpd')

@admin.register(PedidoAfiliacaoAcademia)
class PedidoAcademiaAdmin(admin.ModelAdmin):
    list_display = ('nome_academia', 'nome_responsavel', 'status', 'data_pedido')
    list_filter = ('status',)
    search_fields = ('nome_academia', 'nome_responsavel', 'cpf_responsavel')
    readonly_fields = ('data_pedido', 'termo_lgpd')

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data_evento', 'local')
    list_filter = ('data_evento',)
    search_fields = ('titulo', 'local', 'descricao')
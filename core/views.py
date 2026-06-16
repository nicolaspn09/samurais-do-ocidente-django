from django.db import models
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from .models import Modalidade, Academia, Atleta, Faixa, Noticia, PedidoAfiliacaoAtleta, PedidoAfiliacaoAcademia, Evento
import openpyxl
from django.http import HttpResponse
from datetime import datetime
from .forms import FormAfiliacaoAtleta, FormAfiliacaoAcademia, FormAtualizarPerfil

def home(request):
    eventos = Evento.objects.all().order_by('-data_evento')[:8]
    context = {
        'noticias': Noticia.objects.filter(ativa=True)[:3],
        'eventos': eventos,
    }
    return render(request, 'core/home.html', context)

def afiliar(request):
    form_atleta = FormAfiliacaoAtleta()
    form_academia = FormAfiliacaoAcademia()

    if request.method == 'POST':
        tipo = request.POST.get('tipo_pedido')
        
        if tipo == 'atleta':
            form = FormAfiliacaoAtleta(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, 'Pedido enviado! Aguarde a aprovação da diretoria.')
                return redirect('afiliar')
            else:
                messages.error(request, 'Erro no formulário. Verifique os campos e o CPF.')

        elif tipo == 'academia':
            form = FormAfiliacaoAcademia(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Pedido de Academia enviado com sucesso!')
                return redirect('afiliar')
            else:
                messages.error(request, 'Erro no formulário de Academia. Verifique os dados.')

    return render(request, 'core/afiliacao.html', {
        'form_atleta': form_atleta, 
        'form_academia': form_academia,
        'academias': Academia.objects.filter(ativo=True),
        'modalidades': Modalidade.objects.all()
    })

def academias_list(request):
    academias = Academia.objects.filter(ativo=True).prefetch_related('professores', 'modalidades').order_by('nome')
    return render(request, 'core/academias.html', {'academias': academias})

def atletas_list(request):
    # Filtros da URL
    modalidade_id = request.GET.get('modalidade')
    academia_id = request.GET.get('academia')

    # Busca apenas atletas ativos
    atletas_ativos = Atleta.objects.filter(ativo=True).select_related('academia', 'faixa_atual').prefetch_related('historico_faixas')
    
    # Aplica filtros se existirem
    if modalidade_id:
        atletas_ativos = atletas_ativos.filter(modalidades__id=modalidade_id)
    if academia_id:
        atletas_ativos = atletas_ativos.filter(academia__id=academia_id)

    # Agrupar por nome e pegar o registro com a graduação "mais alta"
    atletas_unicos_dict = {} # nome_norm -> (atleta_obj, score)
    
    data_minima = datetime(1900, 1, 1).date()

    for atleta in atletas_ativos:
        # Normalização agressiva para evitar duplicatas por erro de digitação (. no início, espaços extras)
        nome_norm = atleta.nome.strip('. ').upper()
        
        # Pega a maior data do histórico deste registro
        ultima_grad = atleta.historico_faixas.aggregate(models.Max('data_graduacao'))['data_graduacao__max'] or data_minima
        
        # Score de importância para decidir qual registro mostrar do mesmo atleta
        ordem_faixa = atleta.faixa_atual.ordem if atleta.faixa_atual else 0
        dan_val = atleta.dan_atual or 0
        
        score = (ultima_grad, ordem_faixa, dan_val, atleta.id)
        
        if nome_norm not in atletas_unicos_dict or score > atletas_unicos_dict[nome_norm][1]:
            atletas_unicos_dict[nome_norm] = (atleta, score)
                    
    atletas_unicos = [item[0] for item in atletas_unicos_dict.values()]
            
    # Re-agrupar por faixa para o template
    faixas = Faixa.objects.all().order_by('ordem')
    for faixa in faixas:
        if faixa.is_preta:
            # Para faixa preta, vamos agrupar por Dan internamente
            atletas_da_faixa = [a for a in atletas_unicos if a.faixa_atual == faixa]
            dans_dict = {} # dan -> list of athletes
            
            for a in atletas_da_faixa:
                dan = a.dan_atual or 0
                if dan not in dans_dict:
                    dans_dict[dan] = []
                dans_dict[dan].append(a)
            
            # Ordenar os Dans: Dan 0 (Sem Dan) primeiro, depois 1, 2, 3...
            sorted_dans = sorted(dans_dict.keys())
            
            faixa.dans_agrupados = []
            for dan in sorted_dans:
                if dan == 0:
                    nome_dan = "Somente Faixa Preta"
                else:
                    nome_dan = f"{dan}º DAN"
                    
                faixa.dans_agrupados.append({
                    'numero': dan,
                    'nome': nome_dan,
                    'atletas': sorted(dans_dict[dan], key=lambda x: x.nome)
                })
        else:
            faixa.atletas_filtrados = sorted(
                [a for a in atletas_unicos if a.faixa_atual == faixa],
                key=lambda x: x.nome
            )
    
    # Filtra faixas que não tem atletas depois do filtro
    faixas_com_atletas = [f for f in faixas if (hasattr(f, 'atletas_filtrados') and f.atletas_filtrados) or (hasattr(f, 'dans_agrupados') and f.dans_agrupados)]

    context = {
        'faixas': faixas_com_atletas,
        'modalidades': Modalidade.objects.all(),
        'academias': Academia.objects.filter(ativo=True),
        'modalidade_selecionada': int(modalidade_id) if modalidade_id else None,
        'academia_selecionada': int(academia_id) if academia_id else None,
    }

    return render(request, 'core/atletas.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def exportar_atletas_excel(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="samurais_graduacao_{datetime.now().strftime("%Y%m%d")}.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Atletas e Graduações"

    cabecalhos = ['Nome do Atleta', 'Academia', 'Faixa Atual', 'Data da Última Graduação']
    ws.append(cabecalhos)

    atletas = Atleta.objects.filter(ativo=True).select_related('academia', 'faixa_atual').prefetch_related('historico_faixas').all()
    
    for atleta in atletas:
        ultima_graduacao = atleta.historico_faixas.first()
        data_formatada = ultima_graduacao.data_graduacao.strftime('%d/%m/%Y') if ultima_graduacao else 'Sem data'
        
        ws.append([
            atleta.nome, 
            atleta.academia.nome if atleta.academia else 'N/A', 
            atleta.faixa_atual.nome if atleta.faixa_atual else 'N/A', 
            data_formatada
        ])

    wb.save(response)
    return response

@login_required
def perfil_atleta(request):
    try:
        atleta = request.user.perfil_atleta
    except ObjectDoesNotExist:
        messages.error(request, 'Sua conta ainda não possui uma carteirinha de atleta vinculada. Fale com seu Mestre.')
        return redirect('home')

    if request.method == 'POST':
        form = FormAtualizarPerfil(request.POST, request.FILES, instance=atleta, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('perfil')
    else:
        form = FormAtualizarPerfil(instance=atleta, user=request.user)

    return render(request, 'core/perfil.html', {
        'atleta': atleta, 
        'form': form
    })

@login_required
def inativar_atleta(request):
    try:
        atleta = request.user.perfil_atleta
        atleta.ativo = False
        atleta.save()
        from django.contrib.auth import logout
        logout(request)
        messages.success(request, 'Sua conta foi inativada com sucesso.')
    except ObjectDoesNotExist:
        messages.error(request, 'Atleta não encontrado.')
    
    return redirect('home')
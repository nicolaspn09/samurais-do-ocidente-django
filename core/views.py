from django.db import models
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from .models import Modalidade, Academia, Atleta, Faixa, Noticia, PedidoAfiliacaoAtleta, PedidoAfiliacaoAcademia, Evento, Graduacao
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

    # Busca as graduações (cada graduação vincula um atleta a uma modalidade e faixa)
    graduacoes = Graduacao.objects.filter(atleta__ativo=True).select_related('atleta', 'atleta__academia', 'faixa', 'modalidade')
    
    # Aplica filtros se existirem
    if modalidade_id:
        graduacoes = graduacoes.filter(modalidade_id=modalidade_id)
    if academia_id:
        graduacoes = graduacoes.filter(atleta__academia_id=academia_id)

    # Re-agrupar por faixa para o template
    if modalidade_id:
        faixas = Faixa.objects.filter(modalidades__id=modalidade_id).order_by('ordem')
    else:
        faixas = Faixa.objects.all().order_by('ordem')
    faixas_com_atletas = []

    for faixa in faixas:
        graduacoes_da_faixa = [g for g in graduacoes if g.faixa == faixa]
        
        if not graduacoes_da_faixa:
            continue

        if faixa.is_preta:
            # Para faixa preta, agrupar por Dan
            dans_dict = {} # dan -> list of "atleta objects"
            
            for g in graduacoes_da_faixa:
                dan = g.dan or 0
                if dan not in dans_dict:
                    dans_dict[dan] = []
                
                atleta_display = g.atleta
                atleta_display.uid = g.id # Unique ID for modals
                atleta_display.faixa_atual = g.faixa 
                atleta_display.dan_atual = g.dan
                atleta_display.modalidade_display = g.modalidade.nome
                
                dans_dict[dan].append(atleta_display)
            
            sorted_dans = sorted(dans_dict.keys())
            faixa.dans_agrupados = []
            for dan in sorted_dans:
                nome_dan = "Somente Faixa Preta" if dan == 0 else f"{dan}º DAN"
                faixa.dans_agrupados.append({
                    'numero': dan,
                    'nome': nome_dan,
                    'atletas': sorted(dans_dict[dan], key=lambda x: x.nome)
                })
        else:
            atletas_list_display = []
            for g in graduacoes_da_faixa:
                atleta_display = g.atleta
                atleta_display.uid = g.id
                atleta_display.faixa_atual = g.faixa
                atleta_display.dan_atual = g.dan
                atleta_display.modalidade_display = g.modalidade.nome
                atletas_list_display.append(atleta_display)
                
            faixa.atletas_filtrados = sorted(atletas_list_display, key=lambda x: x.nome)
        
        faixas_com_atletas.append(faixa)

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

    cabecalhos = ['Nome do Atleta', 'Academia', 'Modalidade', 'Faixa Atual', 'Dan', 'Data da Graduação']
    ws.append(cabecalhos)

    graduacoes = Graduacao.objects.filter(atleta__ativo=True).select_related('atleta', 'atleta__academia', 'faixa', 'modalidade').order_by('atleta__nome', 'modalidade__nome')
    
    for g in graduacoes:
        ws.append([
            g.atleta.nome, 
            g.atleta.academia.nome if g.atleta.academia else 'N/A', 
            g.modalidade.nome,
            g.faixa.nome,
            g.dan if g.dan else '',
            g.data_graduacao.strftime('%d/%m/%Y')
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
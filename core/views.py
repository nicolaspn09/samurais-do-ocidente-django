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
    eventos_futuros = Evento.objects.filter(data_evento__gte=timezone.now())[:4]
    context = {
        'noticias': Noticia.objects.filter(ativa=True)[:3],
        'eventos': eventos_futuros,
    }
    return render(request, 'core/home.html', context)

def afiliar(request):
    form_atleta = FormAfiliacaoAtleta()
    form_academia = FormAfiliacaoAcademia()

    if request.method == 'POST':
        tipo = request.POST.get('tipo_pedido')
        
        if tipo == 'atleta':
            form = FormAfiliacaoAtleta(request.POST, request.FILES) # request.FILES ADICIONADO AQUI
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
        'academias': Academia.objects.all(),
        'modalidades': Modalidade.objects.all()
    })

def academias_list(request):
    academias = Academia.objects.all()
    return render(request, 'core/academias.html', {'academias': academias})

def atletas_list(request):
    faixas = Faixa.objects.prefetch_related(
        'atletas_atuais__academia', 
        'atletas_atuais__historico_faixas__faixa'
    ).all()
    return render(request, 'core/atletas.html', {'faixas': faixas})

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

    atletas = Atleta.objects.select_related('academia', 'faixa_atual').prefetch_related('historico_faixas').all()
    
    for atleta in atletas:
        ultima_graduacao = atleta.historico_faixas.first()
        data_formatada = ultima_graduacao.data_graduacao.strftime('%d/%m/%Y') if ultima_graduacao else 'Sem data'
        
        ws.append([
            atleta.nome, 
            atleta.academia.nome, 
            atleta.faixa_atual.nome, 
            data_formatada
        ])

    wb.save(response)
    return response

@login_required
def perfil_atleta(request):
    try:
        # Tenta buscar o perfil do atleta conectado a este usuário
        atleta = request.user.perfil_atleta
    except ObjectDoesNotExist:
        # AGORA SIM! Se o usuário não tiver atleta vinculado, ele é devolvido pra Home sem dar Erro 500
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
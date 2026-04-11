import openpyxl
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Atleta
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Cria usuários para os atletas e gera Excel com as senhas'

    def handle(self, *args, **kwargs):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Acessos Atletas"
        ws.append(['Nome Atleta', 'Usuário', 'Senha'])

        # Pega apenas quem não tem usuário
        atletas = Atleta.objects.filter(usuario__isnull=True)

        for atleta in atletas:
            base_username = slugify(atleta.nome)
            username = base_username
            senha = str(random.randint(1000, 9999)) # Senha aleatória de 4 dígitos

            # Garante username único
            contador = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{contador}"
                contador += 1

            # Cria e vincula
            user = User.objects.create_user(username=username, password=senha)
            atleta.usuario = user
            atleta.save()

            ws.append([atleta.nome, username, senha])
            self.stdout.write(f"Criado: {atleta.nome} | User: {username}")

        # SALVA NA RAIZ DO PROJETO
        wb.save('acessos_samurais.xlsx')
        self.stdout.write(self.style.SUCCESS("Excel 'acessos_samurais.xlsx' gerado na raiz com sucesso!"))
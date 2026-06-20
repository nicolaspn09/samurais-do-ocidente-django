from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator

class Modalidade(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    faixas = models.ManyToManyField('Faixa', related_name='modalidades', blank=True)

    def __str__(self):
        return self.nome

class Academia(models.Model):
    responsavel = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, related_name='academia_antiga')
    nome_responsavel = models.CharField(max_length=200, blank=True, help_text="Nome do Mestre Responsável")
    professores = models.ManyToManyField(User, related_name='academias_professor', blank=True)
    modalidades = models.ManyToManyField(Modalidade, related_name='academias', blank=True)
    nome = models.CharField(max_length=200)
    endereco = models.CharField(max_length=255)
    link_google_maps = models.URLField(blank=True)
    logo = models.ImageField(upload_to='logos_academias/', blank=True, null=True)
    ativo = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if self.nome:
            self.nome = self.nome.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    nome_professor = models.CharField(max_length=255, blank=True, help_text="Nome formatado do professor")

    def __str__(self):
        return self.nome_professor or self.user.username

    def formatar_nome_pelo_username(self):
        if self.user.username:
            partes = self.user.username.split('-')
            self.nome_professor = " ".join([p.capitalize() for p in partes])
            self.save()

# Signals para criar perfil automaticamente
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def criar_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        perfil = PerfilUsuario.objects.create(user=instance)
        perfil.formatar_nome_pelo_username()

class Faixa(models.Model):
    nome = models.CharField(max_length=50)
    ordem = models.IntegerField(help_text="Define a hierarquia da faixa para ordenação na tela")
    cor_hex = models.CharField(max_length=7, default="#FFFFFF", help_text="Cor da faixa em hexadecimal (ex: #000000)")
    is_preta = models.BooleanField(default=False, verbose_name="É Faixa Preta?")

    class Meta:
        ordering = ['ordem']

    def __str__(self):
        return self.nome

class Atleta(models.Model):
    nome = models.CharField(max_length=200)
    foto = models.ImageField(
        upload_to='fotos_atletas/', 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='perfil_atleta')
    
    # CORREÇÕES CRÍTICAS ABAIXO:
    # SET_NULL: Se apagar a academia, o atleta não é deletado, o campo dele apenas fica em branco (null).
    academia = models.ForeignKey(Academia, on_delete=models.SET_NULL, null=True, blank=True, related_name='atletas')
    
    # blank=True permite salvar o atleta sem modalidades marcadas
    modalidades = models.ManyToManyField(Modalidade, blank=True, related_name='atletas')
    
    # null=True e blank=True permitem que o atleta exista sem uma faixa registrada
    faixa_atual = models.ForeignKey(Faixa, on_delete=models.RESTRICT, null=True, blank=True, related_name='atletas_atuais', help_text="Faixa Principal (LEGACY)")
    dan_atual = models.IntegerField(null=True, blank=True, verbose_name="Dan (Se faixa preta)", help_text="Dan Principal (LEGACY)")
    ativo = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        # Limpa o nome removendo espaços e pontos no início/fim
        if self.nome:
            self.nome = self.nome.strip('. ')
        
        # Lógica de Faixa Preta: Se for preta e Dan for 0 ou nulo, coloca 1
        if self.faixa_atual and self.faixa_atual.is_preta:
            if not self.dan_atual or self.dan_atual == 0:
                self.dan_atual = 1
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

class Graduacao(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='graduacoes')
    modalidade = models.ForeignKey(Modalidade, on_delete=models.CASCADE)
    faixa = models.ForeignKey(Faixa, on_delete=models.RESTRICT)
    dan = models.IntegerField(null=True, blank=True, verbose_name="Dan (Se faixa preta)")
    data_graduacao = models.DateField(default=timezone.now)

    class Meta:
        verbose_name = "Graduação"
        verbose_name_plural = "Graduações"
        unique_together = ('atleta', 'modalidade')

    def __str__(self):
        return f"{self.atleta.nome} - {self.modalidade.nome} ({self.faixa.nome})"

class HistoricoGraduacao(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='historico_faixas') 
    modalidade = models.ForeignKey(Modalidade, on_delete=models.CASCADE, null=True, blank=True)
    faixa = models.ForeignKey(Faixa, on_delete=models.RESTRICT)
    dan = models.IntegerField(null=True, blank=True, verbose_name="Dan")
    data_graduacao = models.DateField()
    examinador = models.CharField(max_length=100, help_text="Quem aplicou o exame")

    class Meta:
        ordering = ['-data_graduacao']

    def __str__(self):
        mod_nome = f" [{self.modalidade.nome}]" if self.modalidade else ""
        if self.dan:
            return f"{self.atleta.nome}{mod_nome} - {self.faixa.nome} {self.dan}º Dan em {self.data_graduacao}"
        return f"{self.atleta.nome}{mod_nome} - {self.faixa.nome} em {self.data_graduacao}"

class Midia(models.Model):
    titulo = models.CharField(max_length=200)
    arquivo = models.FileField(upload_to='midias_galeria/')
    modalidade = models.ForeignKey(Modalidade, on_delete=models.CASCADE)
    academia_autora = models.ForeignKey(Academia, on_delete=models.CASCADE)
    data_postagem = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

class Noticia(models.Model):
    titulo = models.CharField(max_length=200)
    resumo = models.CharField(max_length=300, help_text="Texto curto para a página inicial")
    conteudo = models.TextField()
    imagem = models.ImageField(upload_to='noticias/', blank=True, null=True)
    data_publicacao = models.DateTimeField(default=timezone.now)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ['-data_publicacao']

    def __str__(self):
        return self.titulo

class PedidoAfiliacaoAtleta(models.Model):
    STATUS_CHOICES = [('P', 'Pendente'), ('A', 'Aprovado'), ('R', 'Recusado')]
    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14)
    email = models.EmailField()
    whatsapp = models.CharField(max_length=20)
    academia_desejada = models.ForeignKey(Academia, on_delete=models.SET_NULL, null=True)
    modalidade = models.ForeignKey(Modalidade, on_delete=models.SET_NULL, null=True)
    termo_lgpd = models.BooleanField(default=False, help_text="Aceitou os termos de uso dos dados")
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    data_pedido = models.DateTimeField(auto_now_add=True)
    observacoes_admin = models.TextField(blank=True, help_text="Anotações internas da diretoria")
    foto = models.ImageField(upload_to='pedidos_fotos/', null=True, blank=True)

    def __str__(self):
        return f"Pedido Atleta: {self.nome} - {self.get_status_display()}"

class PedidoAfiliacaoAcademia(models.Model):
    STATUS_CHOICES = [('P', 'Pendente'), ('A', 'Aprovado'), ('R', 'Recusado')]
    nome_academia = models.CharField(max_length=200)
    nome_responsavel = models.CharField(max_length=200)
    cpf_responsavel = models.CharField(max_length=14)
    email = models.EmailField()
    whatsapp = models.CharField(max_length=20)
    endereco = models.CharField(max_length=255)
    termo_lgpd = models.BooleanField(default=False)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    data_pedido = models.DateTimeField(auto_now_add=True)
    observacoes_admin = models.TextField(blank=True)

    def __str__(self):
        return f"Pedido Academia: {self.nome_academia} - {self.get_status_display()}"

class Evento(models.Model):
    titulo = models.CharField(max_length=200)
    data_evento = models.DateTimeField()
    local = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    imagem_destaque = models.ImageField(upload_to='eventos/', blank=True, null=True)

    @property
    def encerrado(self):
        return self.data_evento < timezone.now()

    class Meta:
        ordering = ['data_evento']

    def __str__(self):
        return f"{self.titulo} - {self.data_evento.strftime('%d/%m/%Y')}"
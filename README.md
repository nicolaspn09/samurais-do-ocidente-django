# Associação de artes marciais samurais do ocidente

Este repositório contém o **site institucional e o portal dos atletas** da **Associação de artes marciais samurais do ocidente**. O objetivo é divulgar a entidade, listar academias e atletas, receber pedidos de filiação e permitir que cada atleta (quando vinculado) acesse e atualize o próprio perfil.

---

## Para quem não é da área de tecnologia

### O que é isso, na prática?

É um **programa que roda em um servidor na internet** e que as pessoas acessam pelo navegador (Chrome, Edge, Firefox, etc.), como qualquer outro site. Por trás das páginas há um sistema que:

- guarda informações em um **banco de dados** (cadastros, notícias, eventos, pedidos de filiação);
- mostra essas informações nas telas públicas;
- permite que a **diretoria e os professores** cadastrem e alterem dados em uma área administrativa protegida por senha.

Você **não precisa instalar nada no seu computador** para **usar** o site já publicado: basta o endereço (URL) fornecido pela hospedagem.

### O que o visitante vê no site?

| Área | O que faz |
|------|-----------|
| **Página inicial** | Destaques: notícias ativas e próximos eventos. |
| **Atletas** | Lista de atletas organizada por **faixa** (graduação). |
| **Academias** | Lista das academias filiadas, com dados de localização. |
| **Afiliação** | Formulários para **pedido de filiação** como atleta ou como nova academia (com aceite de termos de uso dos dados). |
| **Portal do aluno** | Login; após entrar, o atleta pode ir em **Meu Perfil** se existir um cadastro de atleta ligado à conta dele. |

### O que a diretoria / equipe faz no “bastidor”?

Há uma área chamada **Administração do Django** (caminho `/admin/` no site), acessível com usuário e senha criados no sistema. Lá é possível, entre outras coisas:

- cadastrar e editar **modalidades**, **faixas**, **academias**, **atletas**, **notícias**, **eventos** e **mídias** da galeria;
- acompanhar **pedidos de filiação** (atleta e academia) e alterar status (pendente, aprovado, recusado);
- registrar **histórico de graduação** dos atletas (quem pode fazer isso depende do tipo de usuário — ver abaixo).

**Permissões resumidas:**

- **Presidente / superusuário**: acesso amplo; pode alterar faixa atual e histórico de graduação; pode **exportar uma planilha Excel** com atletas e graduações (rota protegida no sistema).
- **Professor vinculado a uma academia**: no admin, enxerga e edita principalmente **a própria academia** e **os atletas dessa academia**; a **faixa atual** do atleta fica bloqueada para edição por esse perfil (só o superusuário altera).
- **Atleta comum** (usuário com perfil ligado): usa o site para **login** e **atualização do próprio perfil** na página “Meu Perfil”, sem precisar entrar no painel administrativo completo.

Se alguém entrar no Portal do aluno mas **não tiver atleta vinculado** à conta, o sistema avisa para falar com o mestre — isso evita erro e deixa claro o próximo passo.

---

## Para desenvolvedores

### Stack

| Componente | Uso |
|------------|-----|
| **Python / Django 5.2** | Framework web, ORM, admin, autenticação. |
| **PostgreSQL** | Banco de dados em produção (via variáveis de ambiente). |
| **WhiteNoise** | Servir arquivos estáticos em produção. |
| **Gunicorn** | Servidor WSGI típico em deploy Linux. |
| **Pillow** | Imagens (`ImageField`). |
| **openpyxl** | Geração do arquivo `.xlsx` na exportação de atletas. |
| **python-dotenv** | Carregar `.env` no desenvolvimento. |

Front-end das páginas principais: **HTML + Tailwind CSS** (via CDN no template base).

### Estrutura principal do código

```
Códigos/
├── manage.py              # CLI do Django
├── requirements.txt       # Dependências Python
├── projeto/               # Configuração do projeto (settings, urls, wsgi)
├── core/                  # App principal: models, views, forms, admin, urls
├── templates/core/        # Templates HTML
├── static/                # Arquivos estáticos de desenvolvimento (ex.: logo)
├── media/                 # Uploads em runtime (não versionar em produção local típica)
└── staticfiles/           # Coletados com collectstatic (gerado; costuma estar no .gitignore)
```

### Modelos principais (`core.models`)

- `Modalidade`, `Faixa`, `Academia`, `Atleta`, `HistoricoGraduacao`
- `Noticia`, `Evento`, `Midia`
- `PedidoAfiliacaoAtleta`, `PedidoAfiliacaoAcademia`

### Rotas (`core.urls`)

| URL | View | Observação |
|-----|------|------------|
| `/` | `home` | Notícias + eventos futuros |
| `/afiliar/` | `afiliar` | POST com `tipo_pedido` = `atleta` ou `academia` |
| `/academias/` | `academias_list` | |
| `/atletas/` | `atletas_list` | Faixas com prefetch |
| `/login/`, `/logout/` | auth views | Templates em `core/login.html` |
| `/perfil/` | `perfil_atleta` | `@login_required` |
| `/exportar-atletas/` | `exportar_atletas_excel` | `@login_required` + `@user_passes_test(superuser)` |

Mídia em produção: `projeto/urls.py` inclui servir `MEDIA_ROOT` sob `/media/...` (ajustar estratégia se usar storage externo, ex. S3).

### Configuração (`projeto/settings.py`)

- `SECRET_KEY`, `DEBUG` e credenciais do banco vêm de **variáveis de ambiente** (com fallbacks de desenvolvimento para a chave).
- `CSRF_TRUSTED_ORIGINS` inclui domínios HTTPS usados no deploy (ex.: Easypanel / `samuraisdoocidente.com.br` — revisar antes de publicar).
- `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL` apontam para `login`, `perfil` e `home`.

### Como rodar em desenvolvimento

1. **Python 3.10+** recomendado. Crie e ative um ambiente virtual.
2. Instale dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Crie um arquivo **`.env`** na raiz do projeto `Códigos` (o `settings` usa `find_dotenv()`). Exemplo mínimo para testar com PostgreSQL:

   ```env
   DJANGO_SECRET_KEY=sua-chave-secreta-local
   DEBUG=True
   DB_NAME=nome_do_banco
   DB_USER=usuario
   DB_PASSWORD=senha
   DB_HOST=localhost
   DB_PORT=5432
   ```

   > **Nota:** O `settings` está configurado para **PostgreSQL**. Para usar SQLite seria necessário alterar `DATABASES` em `projeto/settings.py` (não está no repositório como padrão).

4. Aplique migrações e crie um superusuário:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. Suba o servidor de desenvolvimento:

   ```bash
   python manage.py runserver
   ```

6. Acesse `http://127.0.0.1:8000/` e o admin em `http://127.0.0.1:8000/admin/`.

Para arquivos estáticos em produção, use `collectstatic` conforme a documentação do Django + WhiteNoise.

### Deploy (visão geral)

O código comenta uso de **Easypanel**, **HTTPS** atrás de proxy (`SECURE_PROXY_SSL_HEADER`) e **Gunicorn**. Em produção:

- defina `DEBUG=False` e uma `DJANGO_SECRET_KEY` forte;
- configure `ALLOWED_HOSTS` de forma restritiva (hoje está `['*']` no MVP — endurecer quando o domínio for fixo);
- garanta banco PostgreSQL e variáveis `DB_*`;
- rode migrações e `collectstatic` no pipeline ou no servidor.

---

## Licença e créditos

Projeto desenvolvido no contexto da associação **Samurais do Ocidente** (Nexus Systems / demanda Taciano). Ajuste esta seção se houver licença específica ou contatos oficiais.

---

*Última atualização do README: abril de 2026.*

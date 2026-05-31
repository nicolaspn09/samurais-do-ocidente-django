# Como evitar a perda de imagens no Easypanel

O Easypanel roda sua aplicação dentro de um container Docker. Sempre que você faz um novo "Deploy" (atualização), o container antigo é destruído e um novo é criado a partir do zero.
Isso significa que todas as imagens enviadas pelos usuários (fotos de perfil, logos de academias) salvas na pasta `/app/media` serão apagadas.

Para resolver isso, você precisa criar um **Volume** no Easypanel para a pasta de mídia:

1. Acesse o painel do seu projeto no **Easypanel**.
2. Vá até a aba **Advanced** (Avançado) ou **Mounts** (Montagens) do seu serviço.
3. Adicione uma nova montagem de volume (Volume Mount):
   - **Type**: `Volume`
   - **Volume Name**: `samurais_media` (ou qualquer nome que preferir)
   - **Mount Path**: `/app/media`
4. Salve as alterações e faça o **Deploy** novamente.

A partir de agora, o Easypanel vai salvar as imagens fora do container temporário e elas nunca mais serão perdidas nas próximas atualizações.
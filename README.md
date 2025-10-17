<<<<<<< HEAD
# Bot - LOUCOS POR PVE

Instruções rápidas para rodar e fazer deploy no Discloud.

## Dependências
Dependências principais (já incluídas em `requirements.txt`):

- discord.py>=2.0.0
- aiofiles>=23.1.0
- aiohttp>=3.8.1
- openpyxl>=3.0.10
- pytz>=2023.3

## Rodando localmente (Windows PowerShell)

1. Criar e ativar venv (uma vez):

```powershell
py -3 -m venv .venv
. .\.venv\Scripts\Activate.ps1
```

2. Instalar dependências:

```powershell
pip install -r requirements.txt
```

3. Rodar o bot:

```powershell
python bot.py
```

## Deploy no Discloud

1. Certifique-se de que `discloud.config` contém `MAIN=bot.py` e que `requirements.txt` está na raiz do repositório.

2. Faça commit e push do repositório que está ligado ao Discloud.

3. No painel do Discloud, faça redeploy/start da instância.

4. Verifique os logs. Se houver erro `ModuleNotFoundError`, confirme que o Discloud conseguiu instalar as dependências (procure por mensagens de `pip install -r requirements.txt` nos logs).

## Troubleshooting comum

- `ModuleNotFoundError: No module named 'aiofiles'` → `requirements.txt` ausente ou não instalado. Certifique-se que o arquivo existe e que o Discloud rodou `pip install -r requirements.txt` sem erro.
- Falha na instalação de pacotes (erros de compilação) → verifique logs de build. As bibliotecas usadas aqui são puramente Python e normalmente não precisam de compiladores.
- `MAIN` incorreto no `discloud.config` → deve apontar para `bot.py`.

Se quiser, eu posso ajustar versões específicas ou adicionar instruções extras para variáveis de ambiente (token) e segurança.
=======
🤖 Albion Points Bot

Um bot desenvolvido para gerenciar pontuações de jogadores do Albion Online dentro do Discord.
Ideal para guildas que querem manter o controle de pontos, organizar recompensas e dividir lucros com facilidade.

💡 Descrição

O Albion Points Bot é um sistema simples, eficiente e totalmente integrado a um banco de dados local (JSON).
Ele permite que administradores e membros autorizados adicionem, removam ou editem os pontos dos integrantes da guilda diretamente pelo Discord.

Além disso, o bot conta com funções auxiliares para o dia a dia da guilda, como:

💰 Divisão de lucro automática (Split) — calcula quanto cada jogador deve receber.

🧮 Cálculos rápidos e precisos — útil para gerenciar recompensas e pagamentos.

📊 Ranking e consultas — veja o top da guilda em tempo real.

⚙️ Principais Recursos

✅ Banco de dados local em JSON
✅ Sistema de pontuação por jogador
✅ Comandos de adicionar, remover e editar pontos
✅ Sistema de ranking e top players
✅ Divisão automática de lucros (split)
✅ Interface simples e amigável via comandos Discord

_______________________________________________________________________
🧑‍💻 Tecnologias Utilizadas

Python 3.x

discord.py

JSON (para persistência de dados)

dotenv (para variáveis de ambiente)
________________________________________________________________________

🏰 Feito para os Loucos por PVE

Este bot foi desenvolvido com carinho para a guilda LOUCOS POR PVE,
com o objetivo de tornar o sistema de pontuação mais justo, rápido e automatizado.
>>>>>>> 1ace2a85cf82c19cba162a6b339515da4d0b3319

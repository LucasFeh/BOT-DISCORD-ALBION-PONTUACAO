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

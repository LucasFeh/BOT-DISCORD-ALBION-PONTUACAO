import discord
from discord.ext import commands

# Dicionário de pontuação por conteúdo
PONTOS_POR_CONTEUDO = {
    "DG": 20,
    "AVALON": 30,
    "ARANHA": 50,
    # você pode adicionar mais tipos depois
}

# Guardará temporariamente os dados antes de finalizar
conteudo_em_aberto = None

# Intents (necessárias para ver mensagens)
intents = discord.Intents.default() # Habilita intents padrão
intents.message_content = True # Habilita o acesso ao conteúdo das mensagens

# Criação do bot
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user}')

@bot.command()
async def conteudo(ctx, caller, tipo, *integrantes):
    global conteudo_em_aberto

    tipo = tipo.upper()
    if tipo not in PONTOS_POR_CONTEUDO:
        await ctx.send(f"❌ Tipo de conteúdo inválido: `{tipo}`")
        return

    pontos = PONTOS_POR_CONTEUDO[tipo]
    membros = list(integrantes)
    membros.insert(0, caller)  # Adiciona o caller também na pontuação

    conteudo_em_aberto = {
        "caller": caller,
        "tipo": tipo,
        "pontos": pontos,
        "membros": membros,
    }

    tabela = "\n".join([f"- {m}: {pontos} pts" for m in membros])
    await ctx.send(f"📊 **Prévia de Pontuação - {tipo}**\n{tabela}\n\nUse `!finalizar` para salvar.")

@bot.command()
async def finalizar(ctx):
    global conteudo_em_aberto

    if not conteudo_em_aberto:
        await ctx.send("❌ Nenhum conteúdo em aberto para finalizar.")
        return

    # Aqui você salvaria no banco de dados real
    # Por enquanto só mostra e limpa
    tipo = conteudo_em_aberto["tipo"]
    membros = conteudo_em_aberto["membros"]

    await ctx.send(f"✅ Conteúdo **{tipo}** finalizado e registrado para: {', '.join(membros)}")

    conteudo_em_aberto = None



bot.run("MTQyMDQxNzA2MDY0Njk0OTAwNQ.GQNVUm.njRh09n8aqcNSBWnGzJeTAnREJHQTZDwuiTJ3o")

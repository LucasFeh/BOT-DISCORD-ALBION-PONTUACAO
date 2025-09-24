import discord
from discord.ext import commands

# Dicionário de pontuação por conteúdo
PONTOS_POR_CONTEUDO = {
    "DG": 20,
    "AVALON": 30,
    "COMUNIATARIO-BAIXO-RISCO": 75,
    "COMUNIATARIO-ALTO-RISCO": 100,
    "ARANHA DE CRISTAL": 25,
    "CAMPEONATO": 50,
    "DOACAO": 100,
    # você pode adicionar mais tipos depois
}
   # Mapear ícones para cada tipo de conteúdo
icones = {
    "DG": "⚔️",
    "AVALON": "🏰",
    "COMUNIATARIO-BAIXO-RISCO": "🛡️",
    "COMUNIATARIO-ALTO-RISCO": "⚠️",
    "ARANHA DE CRISTAL": "💎",
    "CAMPEONATO": "🏆",
    "DOACAO": "💰"
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
async def Pontuacao(ctx):
    # Criar um embed para uma tabela bonita
    embed = discord.Embed(
        title="📊 TABELA DE PONTOS - Paladinos Sagrados",
        description="Sistema de pontuação por conteúdo",
        color=0x00ff00  # Verde
    )
    
    # Criar cabeçalhos da tabela
    embed.add_field(name="📋 **CONTEÚDO**", value="━━━━━━━━━━━━━━━━━━━━━━━━━", inline=True)
    embed.add_field(name="🎯 **PONTOS**", value="━━━━━━━━━━━━━━━━━━━━━━━━━", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)  # Campo vazio para quebra de linha
    
    # Adicionar cada linha da tabela
    for tipo, pontos in PONTOS_POR_CONTEUDO.items():
        icone = icones.get(tipo, "📋")
        nome_formatado = f"{icone} {tipo.replace('-', ' ').title()}"
        
        # Coluna 1: Nome do conteúdo
        embed.add_field(name="\u200b", value=nome_formatado, inline=True)
        
        # Coluna 2: Pontos em verde
        embed.add_field(name="\u200b", value=f"```ansi\n\u001b[36m{pontos} pts\u001b[0m\n```", inline=True)
        
        # Coluna 3: Espaço vazio para quebrar linha
        embed.add_field(name="\u200b", value="\u200b", inline=True)
    
    # Adicionar informações extras
    embed.set_footer(text="Use !conteudo <caller> <tipo> <participantes> para registrar")
    
    await ctx.send(embed=embed) 

@bot.command()
async def conteudo(ctx, caller, tipo, *integrantes):
    global conteudo_em_aberto

    tipo = tipo.upper()
    if tipo not in PONTOS_POR_CONTEUDO:
        # Embed para erro
        embed_erro = discord.Embed(
            title="❌ Erro",
            description=f"Tipo de conteúdo inválido: `{tipo}`",
            color=0xff0000  # Vermelho
        )
        embed_erro.add_field(
            name="💡 Tipos válidos:",
            value=", ".join([f"`{t}`" for t in PONTOS_POR_CONTEUDO.keys()]),
            inline=False
        )
        await ctx.send(embed=embed_erro)
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

    # Criar embed para prévia
    icone = icones.get(tipo, "📋")
    embed = discord.Embed(
        title=f"📊 PRÉVIA DE PONTUAÇÃO",
        description=f"{icone} **{tipo.replace('-', ' ').title()}** - {pontos} pts por pessoa",
        color=0xffa500  # Laranja para prévia
    )

    participantes_lista = []
    for i, membro in enumerate(membros):
        if i == 0:  # O primeiro é sempre o caller
            participantes_lista.append(f"👑 **{membro}** `CALLER` → {pontos} pts")
        else:
            participantes_lista.append(f"- **{membro}** → {pontos} pts")
    embed.add_field(
        name="👥 Participantes",
        value="\n".join(participantes_lista),
        inline=False
    )
    # # Adicionar participantes
    # participantes_lista = "\n".join([f"🟡 **{m}** → {pontos} pts" for m in membros])
    # embed.add_field(
    #     name="� Participantes",
    #     value=participantes_lista,
    #     inline=False
    # )

    embed.set_footer(text="Use !finalizar para confirmar e salvar a pontuação")
    
    await ctx.send(embed=embed)

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

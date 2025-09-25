import discord
from discord.ext import commands
import aiohttp
import asyncio


# ID fixo da guilda Paladinos Sagrados
GUILD_ID = "JqtF-_HzQq20YAHK0_Ifig"

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

# Função para converter valores abreviados (17M, 5K, etc) em números
def converter_valor_abreviado(valor_str):
    valor_str = valor_str.upper().strip()
    
    # Se já é um número normal, retorna diretamente
    try:
        return float(valor_str)
    except ValueError:
        pass
    
    # Mapear sufixos para multiplicadores
    sufixos = {
        'K': 1_000,
        'M': 1_000_000,
        'B': 1_000_000_000,
        'T': 1_000_000_000_000
    }
    
    # Verificar se termina com sufixo conhecido
    for sufixo, multiplicador in sufixos.items():
        if valor_str.endswith(sufixo):
            numero_str = valor_str[:-1]  # Remove o sufixo
            try:
                numero = float(numero_str)
                return numero * multiplicador
            except ValueError:
                raise ValueError(f"Formato inválido: {valor_str}")
    
    raise ValueError(f"Formato não reconhecido: {valor_str}")

# Função para formatar números grandes em formato abreviado
def formatar_valor_abreviado(valor):
    if valor >= 1_000_000_000_000:
        return f"{valor / 1_000_000_000_000:.1f}T"
    elif valor >= 1_000_000_000:
        return f"{valor / 1_000_000_000:.1f}B"
    elif valor >= 1_000_000:
        return f"{valor / 1_000_000:.1f}M"
    elif valor >= 1_000:
        return f"{valor / 1_000:.1f}K"
    else:
        return f"{valor:.f}"


# Funções para API do Albion Online
async def buscar_guilda_por_nome(nome_guilda):
    """Busca informações da guilda Paladinos Sagrados usando o ID fixo"""
    # Se for a guilda Paladinos Sagrados, usar o ID fixo
    if nome_guilda.lower() in ["paladinos sagrados", "paladinos"]:
        return await buscar_guilda_por_id(GUILD_ID)
    
    # Para outras guildas, tentar buscar na API oficial
    return await buscar_guilda_api_oficial(nome_guilda)

async def buscar_guilda_por_id(guild_id):
    """Busca informações da guilda pelo ID na API oficial"""
    url = f"https://gameinfo.albiononline.com/api/gameinfo/guilds/{guild_id}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'id': data.get('Id'),
                        'name': data.get('Name'),
                        'founder': data.get('FounderName'),
                        'founded': data.get('Founded'),
                        'alliance_tag': data.get('AllianceTag'),
                        'alliance_name': data.get('AllianceName'),
                        'kill_fame': data.get('killFame'),
                        'death_fame': data.get('DeathFame'),
                        'member_count': data.get('MemberCount'),
                        'source': 'official'
                    }
                return None
        except Exception as e:
            print(f"Erro ao buscar guilda por ID: {e}")
            return None

async def buscar_guilda_api_oficial(nome_guilda):
    """Busca guilda na API oficial (método menos confiável)"""
    # A API oficial não tem endpoint de busca por nome
    # Este é um fallback que pode não funcionar para todas as guildas
    print(f"Tentando buscar guilda '{nome_guilda}' na API oficial (limitado)")
    return None

async def buscar_membros_guilda(guild_info):
    """Busca os membros de uma guilda usando a API oficial"""
    if not guild_info:
        return []
    
    guild_id = guild_info.get('id')
    if not guild_id:
        return []
    
    # Usar o endpoint correto para membros da guilda
    url = f"https://gameinfo.albiononline.com/api/gameinfo/guilds/{guild_id}/members"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data if isinstance(data, list) else []
                return []
        except Exception as e:
            print(f"Erro ao buscar membros da guilda: {e}")
            return []

async def buscar_membro_por_nome(nome_membro):
    """Busca informações detalhadas de um membro específico da guilda"""
    url = f"https://gameinfo.albiononline.com/api/gameinfo/guilds/{GUILD_ID}/members"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    membros = await response.json()
                    # Buscar o membro pelo nome (case insensitive)
                    for membro in membros:
                        if membro.get('Name', '').lower() == nome_membro.lower():
                            return membro
                return None
        except Exception as e:
            print(f"Erro ao buscar membro: {e}")
            return None

# Intents (necessárias para ver mensagens)
intents = discord.Intents.default() # Habilita intents padrão
intents.message_content = True # Habilita o acesso ao conteúdo das mensagens

# Criação do bot
bot = commands.Bot(command_prefix='!', intents=intents)
@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user}')

@bot.command()
async def pontuacao(ctx):
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

@bot.command()
async def split(ctx, valor, quantidade: int):
    try:
        # Converter valor abreviado para número
        valor_original = valor  # Guardar o valor original para exibir
        valor_numerico = converter_valor_abreviado(valor)
        
        if quantidade <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")

        valor_por_pessoa = valor_numerico / quantidade

        # Formatar valores para exibição
        valor_formatado = formatar_valor_abreviado(valor_numerico)
        valor_pessoa_formatado = formatar_valor_abreviado(valor_por_pessoa)

        embed = discord.Embed(
            title=f"💰 SPLIT DE VALOR",
            description=f"💰 **{valor_formatado}** dividido por **{quantidade}** pessoas",
            color=0xffa500  # Laranja para prévia
        )

        # Campo com resumo
        embed.add_field(
            name="Resumo",
            value=f"**Valor por pessoa**: {valor_pessoa_formatado}\n**Valor total**: {valor_formatado}",
            inline=False
        )

        embed.set_footer(text="Valores em formato abreviado (K=mil, M=milhão, B=bilhão) cada pessoa deve receber o valor indicado")
        
        await ctx.send(embed=embed)

    except ValueError as e:
        embed_erro = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao processar o comando: {e}\n\n💡 **Formatos aceitos:**\n`17M` (17 milhões)\n`500K` (500 mil)\n`2.5B` (2.5 bilhões)\n`1000` (número normal)",
            color=0xff0000
        )
        await ctx.send(embed=embed_erro)

@bot.command()
async def guilda(ctx):
    """Mostra informações da guilda Paladinos Sagrados"""
    
    # Embed de carregamento
    embed_loading = discord.Embed(
        title="🔍 Buscando informações da guilda...",
        description="Consultando API do Albion Online",
        color=0xffa500
    )
    loading_msg = await ctx.send(embed=embed_loading)
    
    try:
        # Buscar informações da guilda
        guilda_info = await buscar_guilda_por_id(GUILD_ID)
        
        if not guilda_info:
            embed_erro = discord.Embed(
                title="❌ Erro ao carregar dados",
                description="Não foi possível carregar as informações da guilda",
                color=0xff0000
            )
            await loading_msg.edit(embed=embed_erro)
            return
        
        # Criar embed com informações da guilda
        embed = discord.Embed(
            title="🏰 PALADINOS SAGRADOS",
            description=f"Informações da guilda",
            color=0x00ff00
        )
        
        # Informações básicas
        embed.add_field(
            name="📋 Informações Gerais",
            value=f"**Nome:** {guilda_info['name']}\n"
                  f"**Fundador:** {guilda_info['founder']}\n"
                  f"**Membros:** {guilda_info['member_count']}\n"
                  f"**Aliança:** {guilda_info['alliance_tag'] or 'Nenhuma'}",
            inline=False
        )
        
        # Estatísticas de fame
        kill_fame_formatado = formatar_valor_abreviado(guilda_info['kill_fame'])
        death_fame_formatado = formatar_valor_abreviado(guilda_info['death_fame'])
        
        embed.add_field(
            name="⚔️ Estatísticas de Combate",
            value=f"**Kill Fame:** {kill_fame_formatado}\n"
                  f"**Death Fame:** {death_fame_formatado}",
            inline=True
        )
        
        # Data de fundação
        founded_date = guilda_info['founded'][:10]  # Pegar só a data
        embed.add_field(
            name="📅 Fundação",
            value=founded_date,
            inline=True
        )
        
        embed.set_footer(text="Dados da API oficial do Albion Online")
        
        await loading_msg.edit(embed=embed)
        
    except Exception as e:
        embed_erro = discord.Embed(
            title="❌ Erro interno",
            description=f"Ocorreu um erro: {str(e)}",
            color=0xff0000
        )
        await loading_msg.edit(embed=embed_erro)

@bot.command()
async def membros(ctx):
    """Lista todos os membros da guilda Paladinos Sagrados"""
    
    # Embed de carregamento
    embed_loading = discord.Embed(
        title="🔍 Buscando membros da guilda...",
        description="Consultando API do Albion Online",
        color=0xffa500
    )
    loading_msg = await ctx.send(embed=embed_loading)
    
    try:
        # Buscar informações da guilda
        guilda_info = await buscar_guilda_por_id(GUILD_ID)
        
        if not guilda_info:
            embed_erro = discord.Embed(
                title="❌ Erro ao carregar dados",
                description="Não foi possível carregar as informações da guilda",
                color=0xff0000
            )
            await loading_msg.edit(embed=embed_erro)
            return
        
        # Buscar membros da guilda
        membros = await buscar_membros_guilda(guilda_info)
        
        if not membros:
            embed_erro = discord.Embed(
                title="❌ Erro ao buscar membros",
                description="Não foi possível carregar os membros da guilda. A API pode estar indisponível.",
                color=0xff0000
            )
            await loading_msg.edit(embed=embed_erro)
            return
        
        # Criar embed com os membros
        embed = discord.Embed(
            title="👥 MEMBROS DA GUILDA",
            description=f"🏰 **Paladinos Sagrados** ({len(membros)} membros)\n📊 Fonte: API Oficial Albion",
            color=0x00ff00
        )
        
        # Organizar membros por rank
        membros_por_rank = {}
        for membro in membros:
            # Campos da API oficial do Albion
            rank = membro.get('Role', 'Member')
            nome = membro.get('Name', 'Desconhecido')
            
            if rank not in membros_por_rank:
                membros_por_rank[rank] = []
            membros_por_rank[rank].append(nome)
        
        # Ícones por rank (mais abrangente)
        rank_icons = {
            'GuildMaster': '👑',
            'guildmaster': '👑',
            'leader': '👑',
            'Officer': '⭐',
            'officer': '⭐', 
            'Member': '🔹',
            'member': '🔹',
            'Membro': '🔹',
            'Recruit': '🔸',
            'recruit': '🔸'
        }
        
        # Adicionar cada rank como campo
        for rank, nomes in membros_por_rank.items():
            icone = rank_icons.get(rank, '🔸')
            nomes_ordenados = sorted(nomes)
            nomes_formatados = '\n'.join([f"• {nome}" for nome in nomes_ordenados])
            
            # Dividir em múltiplos campos se muito grande
            if len(nomes_formatados) > 1024:
                # Dividir lista em pedaços menores
                chunk_size = 15
                for i in range(0, len(nomes_ordenados), chunk_size):
                    chunk = nomes_ordenados[i:i + chunk_size]
                    chunk_formatado = '\n'.join([f"• {nome}" for nome in chunk])
                    part_num = (i // chunk_size) + 1
                    
                    embed.add_field(
                        name=f"{icone} {rank} - Parte {part_num}" if part_num > 1 else f"{icone} {rank} ({len(nomes)})",
                        value=chunk_formatado,
                        inline=True
                    )
            else:
                embed.add_field(
                    name=f"{icone} {rank} ({len(nomes)})",
                    value=nomes_formatados,
                    inline=True
                )
        
        # Informações extras
        embed.set_footer(text="Dados da API oficial do Albion Online • Use !membros para atualizar")
        
        await loading_msg.edit(embed=embed)
        
    except Exception as e:
        embed_erro = discord.Embed(
            title="❌ Erro interno",
            description=f"Ocorreu um erro: {str(e)}",
            color=0xff0000
        )
        await loading_msg.edit(embed=embed_erro)

@bot.command()
async def membro(ctx, *, nome_membro):
    """Mostra informações detalhadas de um membro da guilda"""
    
    # Embed de carregamento
    embed_loading = discord.Embed(
        title="🔍 Buscando informações do membro...",
        description=f"Procurando por: **{nome_membro}**",
        color=0xffa500
    )
    loading_msg = await ctx.send(embed=embed_loading)
    
    try:
        # Buscar informações do membro
        membro_info = await buscar_membro_por_nome(nome_membro)
        
        if not membro_info:
            embed_erro = discord.Embed(
                title="❌ Membro não encontrado",
                description=f"Não foi possível encontrar o membro **{nome_membro}** na guilda Paladinos Sagrados",
                color=0xff0000
            )
            embed_erro.add_field(
                name="💡 Dica",
                value="Verifique se o nome está correto (sem espaços extras) ou use !membros para ver a lista completa",
                inline=False
            )
            await loading_msg.edit(embed=embed_erro)
            return
        
        # Extrair dados do membro
        nome = membro_info.get('Name', 'Desconhecido')
        kill_fame = membro_info.get('KillFame', 0)
        death_fame = membro_info.get('DeathFame', 0)
        fame_ratio = membro_info.get('FameRatio', 0)
        
        # Estatísticas de PvE
        lifetime_stats = membro_info.get('LifetimeStatistics', {})
        pve_stats = lifetime_stats.get('PvE', {})
        pve_total = pve_stats.get('Total', 0)
        
        # Estatísticas de coleta
        gathering_stats = lifetime_stats.get('Gathering', {})
        fiber_total = gathering_stats.get('Fiber', {}).get('Total', 0)
        hide_total = gathering_stats.get('Hide', {}).get('Total', 0)
        ore_total = gathering_stats.get('Ore', {}).get('Total', 0)
        rock_total = gathering_stats.get('Rock', {}).get('Total', 0)
        wood_total = gathering_stats.get('Wood', {}).get('Total', 0)
        gathering_total = gathering_stats.get('All', {}).get('Total', 0)
        
        # Outras estatísticas
        crafting_total = lifetime_stats.get('Crafting', {}).get('Total', 0)
        fishing_fame = lifetime_stats.get('FishingFame', 0)
        farming_fame = lifetime_stats.get('FarmingFame', 0)
        
        # Criar embed com informações do membro
        embed = discord.Embed(
            title=f"👤 {nome}",
            description="📊 **Estatísticas Detalhadas**",
            color=0x00ff00
        )
        
        # Informações de PvP
        embed.add_field(
            name="⚔️ **PvP Stats**",
            value=f"**Kill Fame:** {formatar_valor_abreviado(kill_fame)}\n"
                  f"**Death Fame:** {formatar_valor_abreviado(death_fame)}\n"
                  f"**Fame Ratio:** {fame_ratio:.2f}",
            inline=True
        )
        
        # Informações de PvE
        embed.add_field(
            name="🏰 **PvE Stats**",
            value=f"**Total Fame:** {formatar_valor_abreviado(pve_total)}\n"
                  f"**Crafting:** {formatar_valor_abreviado(crafting_total)}\n"
                  f"**Fishing:** {formatar_valor_abreviado(fishing_fame)}\n"
                  f"**Farming:** {formatar_valor_abreviado(farming_fame)}",
            inline=True
        )
        
        # Adicionar campo vazio para quebra de linha
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        
        # Estatísticas de coleta
        embed.add_field(
            name="🌿 **Gathering Stats**",
            value=f"**Total Gathering:** {formatar_valor_abreviado(gathering_total)}\n"
                  f"🌾 **Fiber:** {formatar_valor_abreviado(fiber_total)}\n"
                  f"🦌 **Hide:** {formatar_valor_abreviado(hide_total)}\n"
                  f"⛏️ **Ore:** {formatar_valor_abreviado(ore_total)}\n"
                  f"🪨 **Rock:** {formatar_valor_abreviado(rock_total)}\n"
                  f"🪵 **Wood:** {formatar_valor_abreviado(wood_total)}",
            inline=True
        )
        
        # Informações da guilda
        embed.add_field(
            name="🏰 **Guild Info**",
            value=f"**Guilda:** {membro_info.get('GuildName', 'N/A')}\n"
                  f"**Aliança:** {membro_info.get('AllianceName', 'Nenhuma')}",
            inline=True
        )

        embed.set_footer(text="Dados da API oficial do Albion Online. Desenvolvido por: @Klartz")

        await loading_msg.edit(embed=embed)
        
    except Exception as e:
        embed_erro = discord.Embed(
            title="❌ Erro interno",
            description=f"Ocorreu um erro: {str(e)}",
            color=0xff0000
        )
        await loading_msg.edit(embed=embed_erro)

@bot.command()
async def comandos(ctx):
    embed = discord.Embed(
        title="📜Comandos Disponíveis",
        description="Aqui estão os comandos que você pode usar:",
        color=0x00ff00  # Verde
    )
    embed.add_field(name="!pontuacao", value="Mostra a tabela de pontuação", inline=False)
    embed.add_field(name="!conteudo <caller> <tipo> <participantes>", value="Registra um conteúdo (ex: !conteudo Lucas DG Ana Joao)", inline=False)
    embed.add_field(name="!finalizar", value="Finaliza e salva o conteúdo em aberto", inline=False)
    embed.add_field(name="!split <valor> <quantidade>", value="Divide um valor entre uma quantidade de pessoas (ex: !split 17M 4)", inline=False)
    embed.add_field(name="!guilda", value="Mostra informações da guilda Paladinos Sagrados", inline=False)
    embed.add_field(name="!membros", value="Lista todos os membros da guilda", inline=False)
    embed.add_field(name="!membro <nome>", value="Mostra estatísticas detalhadas de um membro específico", inline=False)
    embed.add_field(name="!botinfo", value="Mostra informações sobre o bot", inline=False)
    embed.add_field(name="!comandos", value="Mostra esta lista de comandos", inline=False)
    embed.set_footer(text="Desenvolvido por:  Lucas (Klartz)")

    await ctx.send(embed=embed)

@bot.command()
async def botinfo(ctx):

    embed = discord.Embed(
        title="🤖 Informações do Bot",
        description="Detalhes sobre o bot de pontuação",
        color=0x00ff00  # Verde
    )

    embed.add_field(name="Nome", value=bot.user.name, inline=True)
    embed.add_field(name="ID", value=bot.user.id, inline=True)
    embed.add_field(name="Criador", value="Lucas (Klartz)", inline=True)
    embed.add_field(name="Comandos Disponíveis", value="!pontuacao, !conteudo, !finalizar, !split, !guilda, !membros, !membro, !botinfo, !comandos", inline=False)
    embed.add_field(name="Versão", value="1.0.0", inline=True)
    embed.set_footer(text="Para mais comandos, use: !comandos. Desenvolvido por: Lucas (Klartz)")
    
    await ctx.send(embed=embed)


bot.run("MTQyMDQxNzA2MDY0Njk0OTAwNQ.GQNVUm.njRh09n8aqcNSBWnGzJeTAnREJHQTZDwuiTJ3o")

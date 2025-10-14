import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # <-- Adicione esta linha!
bot = commands.Bot(command_prefix='!', intents=intents)

# ID fixo da guilda LOUCOS POR PVE
GUILD_ID = "QDufxXRfSiydcD58_Lo9KA"

# Dicionário de pontuação por conteúdo
PONTOS_POR_CONTEUDO = {
    "DG BENEFICIENTE": 10,
    "MONTARIA - (600k)": 20,
    "RE-GEAR (4M)": 30,
    "ARMA 4.4": 50,
    "MONTARIA (1.5M)": 60,
    "MONTARIA (4M)": 80,
    "PRATA (5M)": 90,
    "ARMA 8.3": 250,
    "MAMUTE": 4000
    # você pode adicionar mais tipos depois
}
   # Mapear ícones para cada tipo de conteúdo
icones = {
    "MONTARIA - (600k)": "🐎",
    "RE-GEAR (4M)": "🛡️",
    "ARMA 4.4": "🗡️",
    "MONTARIA (1.5M)": "🐎",
    "MONTARIA (4M)": "🐎",
    "PRATA (5M)": "💰",
    "ARMA 8.3": "🗡️",
    "MAMUTE": "🐘",
    "SORTEIO": "🎲",
    "PATROCIONADOR": "🎁",
    "PONTUAÇÃO": "🏆",
    "RECRUTADOR": "🤝"
}

TIPOS_DE_DG = {
    "SORTEIO",
    "PATROCIONADOR",
    "PONTUAÇÃO",
    "RECRUTADOR"
}
    

# Arquivo JSON para armazenar a pontuação (no mesmo diretório do bot.py)
ARQUIVO_PONTUACAO = "pontuacao_membros.json"

def carregar_pontuacao():
    """Carrega a pontuação dos membros do arquivo JSON"""
    if os.path.exists(ARQUIVO_PONTUACAO):
        try:
            with open(ARQUIVO_PONTUACAO, 'r', encoding='utf-8') as arquivo:
                return json.load(arquivo)
        except (json.JSONDecodeError, FileNotFoundError):
            print("❌ Erro ao carregar arquivo de pontuação. Criando novo arquivo...")
            return {}
    return {}

def salvar_pontuacao(pontuacao_dict):
    """Salva a pontuação dos membros no arquivo JSON"""
    try:
        with open(ARQUIVO_PONTUACAO, 'w', encoding='utf-8') as arquivo:
            json.dump(pontuacao_dict, arquivo, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar pontuação: {e}")
        return False

def adicionar_pontos(nome_membro, pontos):
    """Adiciona pontos a um membro específico"""
    pontuacao = carregar_pontuacao()
    
    # Se o membro já existe, soma os pontos; senão, cria entrada nova
    if nome_membro in pontuacao:
        pontuacao[nome_membro] += pontos
    else:
        pontuacao[nome_membro] = pontos
    
    # Salvar no arquivo
    if salvar_pontuacao(pontuacao):
        return pontuacao[nome_membro]  # Retorna a pontuação total atual
    return None

def remover_pontos(nome_membro, pontos):
    """Remove pontos de um membro específico"""
    pontuacao = carregar_pontuacao()
    
    # Se o membro já existe, subtrai os pontos; senão, cria entrada nova
    if nome_membro in pontuacao:
        pontuacao[nome_membro] -= pontos
    # Salvar no arquivo
    if salvar_pontuacao(pontuacao):
        return pontuacao[nome_membro]  # Retorna a pontuação total atual
    return None

def obter_pontuacao(nome_membro):
    """Obtém a pontuação atual de um membro específico"""
    pontuacao = carregar_pontuacao()
    return pontuacao.get(nome_membro, 0)

def obter_ranking():
    """Obtém o ranking completo ordenado por pontuação"""
    pontuacao = carregar_pontuacao()
    # Ordenar por pontuação (maior para menor)
    ranking = sorted(pontuacao.items(), key=lambda x: x[1], reverse=True)
    return ranking

def remover_membro(nome_membro):
    """Remove um membro da lista de pontuação"""
    pontuacao = carregar_pontuacao()
    if nome_membro in pontuacao:
        del pontuacao[nome_membro]
        salvar_pontuacao(pontuacao)
        return True
    return False

def resetar_pontuacao():
    """Reseta toda a pontuação (cuidado!)"""
    return salvar_pontuacao({})


# Guardará temporariamente os dados antes de finalizar
conteudo_em_aberto = None
class FuncoesEquipeView(discord.ui.View):
    def __init__(self, membros, interaction_user):
        super().__init__(timeout=120)
        self.membros = membros
        self.roles = {m: "DPS" for m in membros}
        self.interaction_user = interaction_user
        self.tank_set = False
        self.healer_set = False
        self.interaction = None

        for membro in membros:
            self.add_item(FuncoesEquipeButton(membro, self))
        
        # Adicionar botão de finalizar
        self.add_item(FinalizarButton())

    async def update_embed(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📊 PRÉVIA DE PONTUAÇÃO",
            description="Clique nos botões abaixo para definir Tank e Healer.\nQuando terminar, clique em **Finalizar**.",
            color=0xffa500
        )
        for membro in self.membros:
            funcao = self.roles[membro]
            emoji = "🛡️" if funcao == "TANK" else "💚" if funcao == "HEALER" else "⚔️"
            embed.add_field(
                name=f"{emoji} {membro}",
                value=f"Função: **{funcao}**",
                inline=False
            )
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except discord.InteractionResponded:
            await interaction.edit_original_response(embed=embed, view=self)

class FinalizarButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="✅ Finalizar", style=discord.ButtonStyle.success, row=4)

    async def callback(self, interaction: discord.Interaction):
        global conteudo_em_aberto

        if interaction.user != self.view.interaction_user:
            await interaction.response.send_message(
                "❌ Apenas quem usou o comando pode finalizar.", ephemeral=True
            )
            return

        # Calcular pontuação
        pontuacao = {}
        caller_nome = conteudo_em_aberto["caller"]
        tipo_conteudo = conteudo_em_aberto["tipo"]  # NOVO: pegar o tipo do conteúdo
        # CORRIGIDO: Filtrar membros para excluir o caller

        membros_sem_caller = [m for m in self.view.membros if m != caller_nome]

        for membro in membros_sem_caller:
            funcao = self.view.roles[membro]
            if funcao in ["TANK", "HEALER"]:
                pontos = 2
            else:  # DPS
                pontos = 1
            pontuacao[membro] = {"funcao": funcao, "pontos": pontos}

        # NOVO: Verificar se o tipo é "PONTUAÇÃO" e penalizar o caller
        if tipo_conteudo == "PONTUAÇÃO":
            remover_pontos(caller_nome, 10)  # Caller perde 10 pontos
            penalidade_texto = f"**Caller:** 👑 {caller_nome} *(perdeu 10 pontos por ser tipo PONTUAÇÃO)*"
        else:
            penalidade_texto = f"**Caller:** 👑 {caller_nome} *(não recebe pontos)*"

        # Criar embed final formatado
        embed_final = discord.Embed(
            title="✅ DG BENEFICIENTE FINALIZADA",
            description=f"*{penalidade_texto}*",
            color=0x00ff00
        )

        # Separar por função para melhor organização
        tank_info = ""
        healer_info = ""
        dps_info = ""

        for membro, info in pontuacao.items():
            funcao = info["funcao"]
            pontos = info["pontos"]
            
            if funcao == "TANK":
                tank_info = f"🛡️ **{membro}** → +{pontos} pts"
                adicionar_pontos(membro, pontos)
            elif funcao == "HEALER":
                healer_info = f"💚 **{membro}** → +{pontos} pts"
                adicionar_pontos(membro, pontos)
            else:  # DPS
                if dps_info:
                    dps_info += f"\n⚔️ **{membro}** → +{pontos} pts"
                    adicionar_pontos(membro, pontos)
                else:
                    dps_info = f"⚔️ **{membro}** → +{pontos} pts"
                    adicionar_pontos(membro, pontos)

        # Adicionar campos organizados
        participantes_texto = ""
        if tank_info:
            participantes_texto += tank_info + "\n"
        if healer_info:
            participantes_texto += healer_info + "\n"
        if dps_info:
            participantes_texto += dps_info

        embed_final.add_field(
            name="👥 Participantes e Pontuação",
            value=participantes_texto,
            inline=False
        )

        # Resumo
        total_pontos = sum(info["pontos"] for info in pontuacao.values())
        total_participantes = len(pontuacao)  # Não conta o caller
        resumo_texto = f"**Total de pontos distribuídos:** {total_pontos}\n"
        resumo_texto += f"**Participantes que receberam pontos:** {total_participantes}\n"
        resumo_texto += f"**Tank/Healer:** 2 pts cada | **DPS:** 1 pt cada\n"
        
        if tipo_conteudo == "PONTUAÇÃO":
            resumo_texto += f"**Caller:** Perdeu 10 pontos (tipo PONTUAÇÃO) 📉"
        else:
            resumo_texto += f"**Caller:** Não recebe pontos"
        
        embed_final.add_field(
            name="📊 Resumo",
            value=resumo_texto,
            inline=False
        )

        embed_final.set_footer(text="Pontuação registrada no sistema! 🎉")

        # Enviar embed final e remover view da mensagem original
        await interaction.response.send_message(embed=embed_final)
        
        # Desabilitar todos os botões da mensagem original
        for item in self.view.children:
            item.disabled = True
        
        embed_concluido = discord.Embed(
            title="✅ PONTUAÇÃO CONCLUÍDA",
            description="As funções foram definidas e a pontuação foi registrada.",
            color=0x888888
        )
        
        await self.view.interaction.edit_original_response(embed=embed_concluido, view=self.view)
        
        # Limpar conteúdo em aberto
        conteudo_em_aberto = None

class FuncoesEquipeButton(discord.ui.Button):
    def __init__(self, membro, view):
        super().__init__(label=membro, style=discord.ButtonStyle.secondary)
        self.membro = membro

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view.interaction_user:
            await interaction.response.send_message(
                "Apenas quem usou o comando pode definir as funções.", ephemeral=True
            )
            return

        # Menu para escolher função
        options = []
        if not self.view.tank_set or self.view.roles[self.membro] == "TANK":
            options.append(discord.SelectOption(label="TANK", emoji="🛡️"))
        if not self.view.healer_set or self.view.roles[self.membro] == "HEALER":
            options.append(discord.SelectOption(label="HEALER", emoji="💚"))
        options.append(discord.SelectOption(label="DPS", emoji="⚔️"))

        select = FuncoesEquipeSelect(self.membro, self.view, options)
        await interaction.response.send_message(
            f"Selecione a função para **{self.membro}**:",
            view=select,
            ephemeral=True
        )


class FuncoesEquipeSelect(discord.ui.View):
    def __init__(self, membro, parent_view, options):
        super().__init__(timeout=30)
        self.add_item(FuncoesEquipeSelectMenu(membro, parent_view, options))


class FuncoesEquipeSelectMenu(discord.ui.Select):
    def __init__(self, membro, parent_view, options):
        super().__init__(placeholder="Escolha a função...", options=options)
        self.membro = membro
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        escolha = self.values[0]
        # Atualiza funções
        if escolha == "TANK":
            for m in self.parent_view.membros:
                if self.parent_view.roles[m] == "TANK":
                    self.parent_view.roles[m] = "DPS"
                if self.parent_view.roles[m] == "HEALER" and m == self.membro:
                    self.parent_view.roles[m] = "TANK"
                    self.parent_view.healer_set = False
            self.parent_view.roles[self.membro] = "TANK"
            self.parent_view.tank_set = True
        elif escolha == "HEALER":
            for m in self.parent_view.membros:
                if self.parent_view.roles[m] == "HEALER":
                    self.parent_view.roles[m] = "DPS"
                if self.parent_view.roles[m] == "TANK" and m == self.membro:
                    self.parent_view.roles[m] = "HEALER"
                    self.parent_view.tank_set = False
            self.parent_view.roles[self.membro] = "HEALER"
            self.parent_view.healer_set = True
        elif escolha == "DPS":
            if self.parent_view.roles[self.membro] == "TANK":
                self.parent_view.roles[self.membro] = "DPS"
                self.parent_view.tank_set = False
            elif self.parent_view.roles[self.membro] == "HEALER":
                self.parent_view.roles[self.membro] = "DPS"
                self.parent_view.healer_set = False
        else:
            self.parent_view.roles[self.membro] = "DPS"

        # ⚡ Aqui: usar a interação do select para atualizar embed
        await self.parent_view.update_embed(interaction)

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
    """Busca informações da guilda LOUCOS POR PVE usando o ID fixo"""
    # Se for a guilda LOUCOS POR PVE, usar o ID fixo
    if nome_guilda.lower() in ["LOUCOS POR PVE", "paladinos"]:
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
    try:
        synced = await bot.tree.sync()
        print(f"🔗 {len(synced)} comandos sincronizados (Slash Commands).")
    except Exception as e:
        print(f"❌ Erro ao sincronizar comandos: {e}")

@bot.tree.command(name="pontuacao", description="Mostra a tabela de pontuação")
async def pontuacao(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 TABELA DE PONTOS - LOUCOS POR PVE [PVE]",
        description="Sistema de pontuação",
        color=0x00ff00
    )

    for tipo, pontos in PONTOS_POR_CONTEUDO.items():
        icone = icones.get(tipo, "📋")
        nome_formatado = f"{icone} {tipo.replace('-', ' ').title()}"
        
        # Cada linha é 1 field com nome e pontos
        embed.add_field(
            name=nome_formatado,
            value=f"```ansi\n\u001b[36m{pontos} pts\u001b[0m```",
            inline=False  # inline=False faz cada linha ocupar toda a largura do embed
        )

    embed.set_footer(text="Use !conteudo <caller> <tipo> <participantes> para registrar")
    await interaction.response.send_message(embed=embed)

# cria as opções automaticamente a partir do dicionário
TIPOS_CHOICES = [
    app_commands.Choice(name=nome, value=nome)
    for nome in TIPOS_DE_DG
]

@bot.tree.command(name="conteudo", description="Registra um novo conteúdo para pontuação")
@app_commands.describe(
    caller="De quem foi a DG Beneficiente?",
    tipo="Tipo da Beneficiente",
    integrantes="Lista de integrantes separados por espaço"
)
@app_commands.choices(tipo=[
    app_commands.Choice(name=f"{icones.get(key, '📋')} {key.replace('-', ' ').title()}", value=key)
    for key in TIPOS_DE_DG
])
async def conteudo(
    interaction: discord.Interaction,
    caller: str,
    tipo: app_commands.Choice[str],
    integrantes: str = ""
):
    global conteudo_em_aberto

    # NOVA VERIFICAÇÃO CORRIGIDA: Tratar mentions do caller
    usuario_comando = interaction.user.display_name  # Nome/apelido de quem executou o comando
    
    # Limpar o caller se for um mention
    caller_limpo = caller
    if caller.startswith("<@") and caller.endswith(">"):
        user_id = caller.replace("<@", "").replace("!", "").replace(">", "")
        try:
            user = interaction.guild.get_member(int(user_id))
            if not user:
                user = await interaction.guild.fetch_member(int(user_id))
            if user:
                caller_limpo = user.display_name
        except Exception:
            # Se não conseguir converter o mention, manter o caller original
            pass
    
    # Verificar se o caller (limpo) corresponde ao usuário que executou o comando
    if caller_limpo.lower() != usuario_comando.lower():
        # Aplicar "punição" de -5 pontos (brincadeira, mas funcional)
        adicionar_pontos(usuario_comando, -5)
        
        embed_safado = discord.Embed(
            title="🚨 EI SAFADO! 🚨",
            description=f"**{usuario_comando}**, esse não é você! Tá querendo roubar os pontos dos outros?\n\n**-5 pontos** para você! 😡",
            color=0xff0000
        )
        embed_safado.add_field(
            name="😂 Brincadeira...",
            value="Mas não faz isso de novo, é sério! 😠",
            inline=False
        )
        embed_safado.add_field(
            name="🔍 Detalhes da verificação:",
            value=f"**Você:** {usuario_comando}\n**Caller informado:** {caller_limpo}",
            inline=False
        )
        embed_safado.set_footer(text="Sistema anti-trapaça ativado! Use seu próprio nome como caller.")
        
        await interaction.response.send_message(embed=embed_safado)
        return  # Interrompe a execução do comando

    tipo_valor = tipo.value
    
    # Verificar se o tipo existe no dicionário
    if tipo_valor not in TIPOS_DE_DG:
        embed_erro = discord.Embed(
            title="❌ Tipo inválido",
            description=f"O tipo **{tipo_valor}** não foi encontrado no sistema.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed_erro, ephemeral=True)
        return

    # Usar o caller limpo (nome real) em vez do mention
    membros = [caller_limpo]  # CORRIGIDO: usar caller_limpo
    if integrantes:
        for parte in integrantes.split():
            if parte.startswith("<@") and parte.endswith(">"):
                user_id = parte.replace("<@", "").replace("!", "").replace(">", "")
                try:
                    user = interaction.guild.get_member(int(user_id))
                    if not user:
                        user = await interaction.guild.fetch_member(int(user_id))
                    if user:
                        membros.append(user.display_name)
                    else:
                        membros.append(parte)
                except Exception:
                    membros.append(parte)
            else:
                membros.append(parte)

    conteudo_em_aberto = {
        "caller": caller_limpo,  # CORRIGIDO: usar caller_limpo
        "tipo": tipo_valor,
        "membros": membros,
    }

    # Embed inicial
    icone = icones.get(tipo_valor, "📋")
    embed = discord.Embed(
        title=f"📊 PRÉVIA DE PONTUAÇÃO",
        description=f"{icone} **{tipo.name}**\n\nClique nos botões abaixo para definir Tank e Healer.\nQuando terminar, clique em **Finalizar**.",
        color=0xffa500
    )
    
    for membro in membros:
        embed.add_field(
            name=f"⚔️ {membro}",
            value="Função: **DPS**",
            inline=False
        )
    
    view = FuncoesEquipeView(membros, interaction.user)
    view.interaction = interaction
    await interaction.response.send_message(embed=embed, view=view)


# @bot.command()
# async def finalizar(ctx):
#     global conteudo_em_aberto

#     if not conteudo_em_aberto:
#         await ctx.send("❌ Nenhum conteúdo em aberto para finalizar.")
#         return

#     # Aqui você salvaria no banco de dados real
#     # Por enquanto só mostra e limpa
#     tipo_valor = conteudo_em_aberto["tipo"]
#     membros = conteudo_em_aberto["membros"]

#     await ctx.send(f"✅ Conteúdo **{tipo_valor}** finalizado e registrado para: {', '.join(membros)}")

#     conteudo_em_aberto = None

@bot.tree.command(name="split", description="Divide um valor entre várias pessoas")
@app_commands.describe(
    valor="Valor total (ex: 17M, 500K, 2.5B)",
    quantidade_de_membros="Número de pessoas para dividir"
)
async def split(interaction: discord.Interaction, valor: str, quantidade_de_membros: int):
    try:
        # Converter valor abreviado para número
        valor_original = valor  # Guardar o valor original para exibir
        valor_numerico = converter_valor_abreviado(valor)
        
        if quantidade_de_membros <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")

        valor_por_pessoa = valor_numerico / quantidade_de_membros

        # Formatar valores para exibição
        valor_formatado = formatar_valor_abreviado(valor_numerico)
        valor_pessoa_formatado = formatar_valor_abreviado(valor_por_pessoa)

        embed = discord.Embed(
            title=f"💰 SPLIT DE VALOR",
            description=f"💰 **{valor_formatado}** dividido por **{quantidade_de_membros}** pessoas",
            color=0xffa500  # Laranja para prévia
        )

        # Campo com resumo
        embed.add_field(
            name="Resumo",
            value=f"**Valor por pessoa**: {valor_pessoa_formatado}",
            inline=False
        )

        embed.set_footer(text="Valores em formato abreviado (K=mil, M=milhão, B=bilhão) cada pessoa deve receber o valor indicado")
        
        await interaction.response.send_message(embed=embed)

    except ValueError as e:
        embed_erro = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao processar o comando: {e}\n\n💡 **Formatos aceitos:**\n`17M` (17 milhões)\n`500K` (500 mil)\n`2.5B` (2.5 bilhões)\n`1000` (número normal)",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed_erro)

@bot.tree.command(name="guilda", description="Mostra informações da guilda LOUCOS POR PVE")
async def guilda(interaction: discord.Interaction):
    embed_loading = discord.Embed(
        title="🔍 Buscando informações da guilda...",
        description="Consultando API do Albion Online",
        color=0xffa500
    )
    await interaction.response.send_message(embed=embed_loading)
    
    try:
        guilda_info = await buscar_guilda_por_id(GUILD_ID)
        if not guilda_info:
            embed_erro = discord.Embed(
                title="❌ Erro ao carregar dados",
                description="Não foi possível carregar as informações da guilda",
                color=0xff0000
            )
            await interaction.edit_original_response(embed=embed_erro)
            return

        embed = discord.Embed(
            title="🏰 LOUCOS POR PVE",
            description=f"Informações da guilda",
            color=0x00ff00
        )
        embed.add_field(
            name="📋 Informações Gerais",
            value=f"**Nome:** {guilda_info['name']}\n"
                  f"**Fundador:** {guilda_info['founder']}\n"
                  f"**Membros:** {guilda_info['member_count']}\n"
                  f"**Aliança:** {guilda_info['alliance_tag'] or 'Nenhuma'}",
            inline=False
        )
        kill_fame_formatado = formatar_valor_abreviado(guilda_info['kill_fame'])
        death_fame_formatado = formatar_valor_abreviado(guilda_info['death_fame'])
        embed.add_field(
            name="⚔️ Estatísticas de Combate",
            value=f"**Kill Fame:** {kill_fame_formatado}\n"
                  f"**Death Fame:** {death_fame_formatado}",
            inline=True
        )
        founded_date = guilda_info['founded'][:10]
        embed.add_field(
            name="📅 Fundação",
            value=founded_date,
            inline=True
        )
        embed.set_footer(text="Dados da API oficial do Albion Online")
        await interaction.edit_original_response(embed=embed)
    except Exception as e:
        embed_erro = discord.Embed(
            title="❌ Erro interno",
            description=f"Ocorreu um erro: {str(e)}",
            color=0xff0000
        )
        await interaction.edit_original_response(embed=embed_erro)


@bot.tree.command(name="membros", description="Lista todos os membros da guilda LOUCOS POR PVE")
async def membros(interaction: discord.Interaction):
    embed_loading = discord.Embed(
        title="🔍 Buscando membros da guilda...",
        description="Consultando API do Albion Online",
        color=0xffa500
    )
    await interaction.response.send_message(embed=embed_loading)

    try:
        guilda_info = await buscar_guilda_por_id(GUILD_ID)
        if not guilda_info:
            embed_erro = discord.Embed(
                title="❌ Erro ao carregar dados",
                description="Não foi possível carregar as informações da guilda",
                color=0xff0000
            )
            await interaction.edit_original_response(embed=embed_erro)
            return  # <-- IMPORTANTE

        membros = await buscar_membros_guilda(guilda_info)
        if not membros:
            embed_erro = discord.Embed(
                title="❌ Erro ao buscar membros",
                description="Não foi possível carregar os membros da guilda. A API pode estar indisponível.",
                color=0xff0000
            )
            await interaction.edit_original_response(embed=embed_erro)
            return  # <-- IMPORTANTE

        # Montar embed com a lista de membros
        embed = discord.Embed(
            title="👥 MEMBROS DA GUILDA",
            description=f"Total: {len(membros)} membros",
            color=0x00ff00
        )

        nomes = [m.get('Name', 'Desconhecido') for m in membros]
        nomes.sort()
        # Discord limita fields a 1024 caracteres, então pode ser necessário dividir em partes
        chunk_size = 40
        for i in range(0, len(nomes), chunk_size):
            chunk = nomes[i:i+chunk_size]
            embed.add_field(
                name=f"Membros {i+1} - {i+len(chunk)}",
                value="\n".join(chunk),
                inline=False
            )

        embed.set_footer(text="Dados da API oficial do Albion Online")
        await interaction.edit_original_response(embed=embed)

    except Exception as e:
        embed_erro = discord.Embed(
            title="❌ Erro interno",
            description=f"Ocorreu um erro: {str(e)}",
            color=0xff0000
        )
        await interaction.edit_original_response(embed=embed_erro)

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
                description=f"Não foi possível encontrar o membro **{nome_membro}** na guilda LOUCOS POR PVE",
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

@bot.tree.command(name="addpontos", description="Adiciona pontos a um membro")
@app_commands.describe(
    membro="Nome do membro",
    pontos="Quantidade de pontos para adicionar"
)
async def addpontos(interaction: discord.Interaction, membro: str, pontos: int):
    try:
        nova_pontuacao = adicionar_pontos(membro, pontos)
        
        if nova_pontuacao is not None:
            embed = discord.Embed(
                title="✅ Pontos Adicionados",
                description=f"**{pontos}** pontos adicionados para **{membro}**",
                color=0x00ff00
            )
            embed.add_field(
                name="📊 Pontuação Atual",
                value=f"**{membro}**: {nova_pontuacao} pontos",
                inline=False
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed_erro = discord.Embed(
                title="❌ Erro",
                description="Não foi possível salvar os pontos.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed_erro)
            
    except Exception as e:
        embed_erro = discord.Embed(
            title="❌ Erro",
            description=f"Ocorreu um erro: {str(e)}",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed_erro)

@bot.tree.command(name="pontos", description="Consulta a pontuação de um membro")
@app_commands.describe(membro="Nome do membro para consultar")
async def pontos(interaction: discord.Interaction, membro: str):
    pontuacao_atual = obter_pontuacao(membro)
    
    embed = discord.Embed(
        title="📊 Consulta de Pontuação",
        color=0x0099ff
    )
    
    if pontuacao_atual > 0:
        embed.add_field(
            name=f"🏆 {membro}",
            value=f"**{pontuacao_atual}** pontos",
            inline=False
        )
    else:
        embed.add_field(
            name=f"❌ {membro}",
            value="Nenhum ponto registrado",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ranking", description="Mostra o ranking completo de pontuação")
async def ranking(interaction: discord.Interaction):
    ranking_completo = obter_ranking()
    
    if not ranking_completo:
        embed = discord.Embed(
            title="📊 Ranking de Pontuação",
            description="Nenhum membro possui pontos ainda.",
            color=0xff9900
        )
        await interaction.response.send_message(embed=embed)
        return
    
    embed = discord.Embed(
        title="🏆 RANKING DE PONTUAÇÃO - LOUCOS POR PVE",
        description="Top membros por pontuação",
        color=0xffd700
    )
    
    # Mostrar top 10 (ou todos se menos de 10)
    top_membros = ranking_completo[:10]
    
    ranking_texto = ""
    for i, (nome, pontos) in enumerate(top_membros, 1):
        if i == 1:
            emoji = "🥇"
        elif i == 2:
            emoji = "🥈"
        elif i == 3:
            emoji = "🥉"
        else:
            emoji = f"{i}."
            
        ranking_texto += f"{emoji} **{nome}** - {pontos} pts\n"
    
    embed.add_field(
        name="🏆 Top Membros",
        value=ranking_texto,
        inline=False
    )
    
    if len(ranking_completo) > 10:
        embed.set_footer(text=f"Mostrando top 10 de {len(ranking_completo)} membros")
    else:
        embed.set_footer(text=f"Total: {len(ranking_completo)} membros")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="removerpontos", description="Remove pontos de um membro")
@app_commands.describe(
    membro="Nome do membro",
    pontos="Quantidade de pontos para remover"
)
async def removerpontos(interaction: discord.Interaction, membro: str, pontos: int):
    try:
        # Remover pontos (adicionar pontos negativos)
        nova_pontuacao = adicionar_pontos(membro, -pontos)
        
        if nova_pontuacao is not None:
            embed = discord.Embed(
                title="✅ Pontos Removidos",
                description=f"**{pontos}** pontos removidos de **{membro}**",
                color=0xff9900
            )
            embed.add_field(
                name="📊 Pontuação Atual",
                value=f"**{membro}**: {nova_pontuacao} pontos",
                inline=False
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed_erro = discord.Embed(
                title="❌ Erro",
                description="Não foi possível remover os pontos.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed_erro)
            
    except Exception as e:
        embed_erro = discord.Embed(
            title="❌ Erro",
            description=f"Ocorreu um erro: {str(e)}",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed_erro)




bot.run("MTQyMDQxNzA2MDY0Njk0OTAwNQ.GQNVUm.njRh09n8aqcNSBWnGzJeTAnREJHQTZDwuiTJ3o")


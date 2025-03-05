import os 
from dotenv import load_dotenv 
import asyncio
from keep_alive import keep_alive
import time 
import discord
from discord.ext import commands

load_dotenv() 

intents = discord.Intents.default() 
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True  # Permet de récupérer les membres

import os
import discord
from flask import Flask
import threading
from keep_alive import keep_alive

client = discord.Client()

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

# Démarrer Flask dans un thread séparé
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()


bot = commands.Bot(command_prefix="!", intents=intents)
@bot.command()
async def salut(ctx):
    await ctx.send(f"Salut toi {ctx.author.mention} !")

@bot.command()
async def ping(ctx):
    await ctx.send(f"pong!")


@bot.command()
async def role(ctx):
    # Demande à l'utilisateur de mentionner les rôles à associer aux emojis
    await ctx.send("Veuillez mentionner les rôles à associer aux emojis. Vous pouvez en mentionner plusieurs.")

    # Attends la réponse de l'utilisateur
    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        # Récupère les rôles mentionnés par l'utilisateur
        role_message = await bot.wait_for('message', check=check, timeout=60)
        roles = [role.strip('<>@&') for role in role_message.content.split()]

        # Crée une liste pour stocker les rôles et leurs emojis
        role_emoji_map = {}

        for role_id in roles:
            role = discord.utils.get(ctx.guild.roles, id=int(role_id))  # Obtient le rôle par ID
            if role:
                # Demande à l'utilisateur quel emoji associer à ce rôle
                await ctx.send(f"Quel emoji voulez-vous associer au rôle **{role.name}** ?")
                emoji_message = await bot.wait_for('message', check=check, timeout=60)
                emoji = emoji_message.content
                role_emoji_map[role] = emoji

        # Envoie un message avec les rôles et les emojis associés
        panel_message = await ctx.send("Réagissez avec les emojis pour obtenir vos rôles !")

        for role, emoji in role_emoji_map.items():
            # Ajoute une réaction avec l'emoji
            await panel_message.add_reaction(emoji)

        # Gère les réactions
        def check_reaction(reaction, user):
            return user != bot and reaction.message.id == panel_message.id

        # Attendre que les utilisateurs réagissent
        while True:
            reaction, user = await bot.wait_for('reaction_add', check=check_reaction)

            # Vérifie quel emoji a été utilisé
            for role, emoji in role_emoji_map.items():
                if reaction.emoji == emoji:
                    member = ctx.guild.get_member(user.id)
                    if member:
                        # Ajoute le rôle à l'utilisateur
                        await member.add_roles(role)
                        await ctx.send(f"{user.mention} a obtenu le rôle **{role.name}** !")

                        # Confirmation à l'utilisateur (message privé ou dans le canal)
                        try:
                            await user.send(f"Tu as maintenant le rôle **{role.name}** ! :tada:")
                        except discord.Forbidden:
                            pass  # Si l'utilisateur a désactivé les messages privés du bot, on ignore

                    break

    except asyncio.TimeoutError:
        await ctx.send("Le délai est écoulé. Veuillez recommencer.")
# Dictionnaire emoji -> rôle (à adapter à ton serveur)
role_emoji_map = {
    "🌸": "Fille", 
    "🚀": "Garçon", 
}

@bot.event
async def role(reaction, user):
    if user.bot:  # Ignore les bots
        return

    guild = reaction.message.guild  # Récupère le serveur
    member = guild.get_member(user.id)  # Récupère l'utilisateur

    if member is None:
        print("❌ Impossible de trouver l'utilisateur.")
        return

    # Vérifier si l'emoji correspond à un rôle
    role_name = role_emoji_map.get(str(reaction.emoji))
    if role_name is None:
        print("❌ Emoji non attribué à un rôle.")
        return

    # Chercher le rôle sur le serveur
    role = discord.utils.get(guild.roles, name=role_name)
    if role is None:
        print(f"❌ Rôle '{role_name}' introuvable sur le serveur.")
        return

    # Ajouter le rôle à l'utilisateur
    try:
        await member.add_roles(role)
        print(f"✅ Rôle '{role.name}' ajouté à {member.name} !")
        await reaction.message.channel.send(f"{user.mention} a obtenu le rôle **{role.name}** !")
    except discord.Forbidden:
        print("❌ Le bot n'a pas la permission d'ajouter ce rôle.")
    except Exception as e:
        print(f"⚠️ Erreur : {e}")

@bot.command()
@commands.has_permissions(administrator=True)  # 👈 Seuls les admins peuvent exécuter la commande
async def créer_reglement(ctx):
    """Commande pour créer un règlement interactif"""

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    # Étape 1 : Demander le titre du règlement
    await ctx.send("📝 Quel est le **titre** de votre règlement ?")
    try:
        titre_msg = await bot.wait_for("message", check=check, timeout=60)
        titre = titre_msg.content
    except:
        await ctx.send("⏳ Temps écoulé, commande annulée.")
        return

    # Étape 2 : Demander le contenu du règlement
    await ctx.send("📜 Que voulez-vous dire dans le règlement ?")
    try:
        reglement_msg = await bot.wait_for("message", check=check, timeout=300)
        reglement = reglement_msg.content
    except:
        await ctx.send("⏳ Temps écoulé, commande annulée.")
        return

    # Étape 3 : Envoyer le message formaté
    embed = discord.Embed(title=f"📜 {titre}", description=reglement, color=discord.Color.blue())
    embed.set_footer(text="Réagissez avec ✅ pour accepter le règlement et obtenir le rôle Membre.")

    reglement_message = await ctx.send(embed=embed)
    await reglement_message.add_reaction("✅")

    # Sauvegarde du message pour l'event on_raw_reaction_add
    bot.reglement_message_id = reglement_message.id

@créer_reglement.error
async def créer_reglement_error(ctx, error):
    """Gère l'erreur si un utilisateur sans permissions essaie d'utiliser la commande"""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("⛔ Désolé, seule l'administration peut utiliser cette commande.")

@bot.event
async def on_raw_reaction_add(payload):
    """Ajoute le rôle Membre quand quelqu'un clique sur ✅"""
    if payload.message_id == getattr(bot, "reglement_message_id", None):
        guild = discord.utils.get(bot.guilds, id=payload.guild_id)
        if guild:
            member = guild.get_member(payload.user_id)
            role = discord.utils.get(guild.roles, name="membre")
            if member and role:
                await member.add_roles(role)
                print(f"✅ {member} a accepté le règlement et a reçu le rôle Membre !")

@bot.command()
async def clear(ctx, amount: int):
    """Efface un certain nombre de messages dans un salon"""
    # Vérifie que l'utilisateur a les permissions nécessaires
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("🚫 Tu n'as pas la permission d'utiliser cette commande.")
        return

    # Vérifie que le nombre de messages à supprimer est valide
    if amount <= 0:
        await ctx.send("❌ Le nombre de messages à supprimer doit être supérieur à zéro.")
        return

    # Supprime les messages dans le canal
    deleted = await ctx.channel.purge(limit=amount)
    await ctx.send(f"🧹 {len(deleted)} messages ont été supprimés !", delete_after=5)

message_timestamps = {}
cooldowns = {}  # Dictionnaire pour gérer le cooldown de chaque utilisateur

@bot.event
async def on_message(message):
    """Gère les messages pour limiter le spam"""
    if message.author == bot.user:
        return  # Ignore les messages du bot lui-même

    user_id = message.author.id
    current_time = time.time()  # On récupère le timestamp actuel

    # Vérifier si l'utilisateur est en cooldown
    if user_id in cooldowns and current_time - cooldowns[user_id] < 10:
        # Si l'utilisateur est en cooldown, on ignore son message et on lui envoie un avertissement
        await message.delete()  # Optionnel, supprimer le message
        await message.channel.send(f"🚫 {message.author.mention}, tu dois attendre 10 secondes avant de pouvoir envoyer un autre message.")
        return

    # Initialiser la liste de timestamps pour l'utilisateur si elle n'existe pas encore
    if user_id not in message_timestamps:
        message_timestamps[user_id] = []

    # Ajouter le timestamp actuel à la liste
    message_timestamps[user_id].append(current_time)

    # Supprimer les anciens messages dans la liste (plus de 1 seconde)
    message_timestamps[user_id] = [t for t in message_timestamps[user_id] if current_time - t <= 1]

    # Si l'utilisateur a envoyé plus de 3 messages dans la dernière seconde
    if len(message_timestamps[user_id]) > 3:
        # Mettre l'utilisateur en cooldown de 10 secondes
        cooldowns[user_id] = current_time
        await message.delete()  # On peut supprimer le message pour éviter qu'il spamme
        await message.channel.send(f"🚫 {message.author.mention}, tu envoies trop de messages rapidement. Tu es en cooldown pendant 10 secondes.")
        return  # On stoppe ici le traitement de ce message

    # Si le message est valide, le bot peut continuer à traiter les commandes
    await bot.process_commands(message)


bad_words = ["connard", "ta gueule", "tg", "conasse", "pute", "salope", "enculé"]
@bot.event
async def on_message(message):
    """Vérifie et supprime les messages contenant des mots interdits et applique un cooldown de 10 secondes"""
    if message.author == bot.user:
        return  # Ignore les messages du bot lui-même

    # Convertir le message en minuscule pour une vérification insensible à la casse
    message_content = message.content.lower()

    # Vérifie si un mot interdit est dans le message
    for bad_word in bad_words:
        if bad_word in message_content:
            # Si l'utilisateur est en cooldown, on ne traite pas son message
            if message.author.id in cooldowns and time.time() - cooldowns[message.author.id] < 10:
                await message.delete()  # Optionnel, on peut aussi supprimer son message
                await message.channel.send(f"🚫 {message.author.mention}, tu es en cooldown. Attends encore {10 - (time.time() - cooldowns[message.author.id]):.1f} secondes.")
                return

            await message.delete()  # Supprimer le message contenant un mot interdit
            await message.channel.send(f"🚫 {message.author.mention}, ton message a été supprimé car il contient un mot interdit.")

            # Ajouter un cooldown de 10 secondes pour l'utilisateur
            cooldowns[message.author.id] = time.time()
            return  # On arrête le traitement du message ici

    # Si le message est valide, on continue à traiter les commandes du bot
    await bot.process_commands(message)



token = os.environ['TOKEN']
keep_alive()
bot.run(token)

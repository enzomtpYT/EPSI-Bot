import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import json
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
bot = commands.Bot(command_prefix=None, intents=intents)

# Global users dictionary
users = {}

def load_users():
    global users
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf-8') as f:
                loaded_users = json.load(f)
                # Validate that loaded_users is a dictionary
                if isinstance(loaded_users, dict):
                    users = loaded_users
                else:
                    print("Warning: users.json contains invalid data. Starting with empty users dictionary.")
                    users = {}
        else:
            print("No users.json file found. Creating new one.")
            users = {}
            save_users()
    except json.JSONDecodeError:
        print("Error: users.json is corrupted. Starting with empty users dictionary.")
        users = {}
        # Backup the corrupted file
        if os.path.exists('users.json'):
            backup_name = f'users_backup_{int(datetime.now().timestamp())}.json'
            os.rename('users.json', backup_name)
        save_users()
    except Exception as e:
        print(f"Unexpected error loading users: {e}")
        users = {}
        save_users()

def save_users():
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)

# Load users when bot starts
load_users()

async def fetch_schedule(user, start_time=None, end_time=None):
    url = f"https://epsi.enzomtp.party/?user={user}"
    if start_time and end_time:
        url += f"&begin={start_time}&end={end_time}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                # Flatten the nested array and filter out empty days
                flattened_data = []
                for day in data:
                    if day and any(course.get('name') for course in day):
                        flattened_data.extend(day)
                return flattened_data
            return []

def create_schedule_embed(schedule):
    embed = discord.Embed(
        title="📚 Emploi du temps EPSI",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    if not schedule:
        embed.description = "Aucun cours trouvé pour la période spécifiée."
        return embed
    
    # Group classes by date
    classes_by_date = {}
    for class_info in schedule:
        date = class_info['date']
        if date not in classes_by_date:
            classes_by_date[date] = []
        classes_by_date[date].append(class_info)
    
    # Add each date's classes to the embed
    for date, classes in sorted(classes_by_date.items()):
        date_str = datetime.strptime(date, "%Y-%m-%d").strftime("%A %d %B %Y")
        class_list = []
        
        for class_info in classes:
            if not class_info.get('name'):  # Skip empty classes
                continue
                
            time_str = f"{class_info['start_time']} - {class_info['end_time']}"
            room_str = f"Salle : {class_info['room']}" if class_info['room'] else "Aucune salle spécifiée"
            teacher_str = f"Professeur : {class_info['teacher']}" if class_info['teacher'] else "Aucun professeur spécifié"
            
            class_str = f"**{class_info['name']}**\n{time_str}\n{room_str}\n{teacher_str}\n"
            class_list.append(class_str)
        
        if class_list:  # Only add the field if there are classes
            embed.add_field(
                name=date_str,
                value="\n".join(class_list),
                inline=False
            )
    
    return embed

@bot.event
async def on_ready():
    print(f'Bot prêt ! Connecté en tant que {bot.user.name} ({bot.user.id})')
    print(f'Utilisateurs enregistrés : {len(users)}')
    try:
        synced = await bot.tree.sync()
        print(f"Synchronisation de {len(synced)} commande(s)")
    except Exception as e:
        print(f"Échec de la synchronisation des commandes : {e}")

@bot.tree.command(
    name="edt",
    description="Obtenir votre emploi du temps EPSI"
)
@app_commands.describe(
    username="Nom d'utilisateur EPSI (optionnel si vous êtes enregistré)",
    start_time="Date de début au format JJ/MM/AAAA (optionnel)",
    end_time="Date de fin au format JJ/MM/AAAA (optionnel)"
)
@app_commands.user_install()
async def schedule(
    interaction: discord.Interaction, 
    username: str = None, 
    start_time: str = None, 
    end_time: str = None
):
    await interaction.response.defer()

    # If no username provided, check if user is registered
    if username is None:
        if not str(interaction.user.id) in users:
            await interaction.followup.send("Merci d'enregistrer votre nom d'utilisateur avec la commande `/register` ou de spécifier un nom d'utilisateur directement.", ephemeral=True)
            return
        username = users[str(interaction.user.id)]
    
    schedule_data = await fetch_schedule(username, start_time, end_time)
    embed = create_schedule_embed(schedule_data)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(
    name="register",
    description="Enregistrer votre nom d'utilisateur EPSI"
)
@app_commands.describe(username="Votre nom d'utilisateur EPSI")
async def register(interaction: discord.Interaction, username: str):
    await interaction.response.defer(ephemeral=True)
    
    # Check if user is already registered
    if str(interaction.user.id) in users:
        await interaction.followup.send("Vous êtes déjà enregistré. Pour changer votre nom d'utilisateur, utilisez la commande `/unregister` d'abord.", ephemeral=True)
        return
    
    # Save the username to users dictionary
    users[str(interaction.user.id)] = username
    
    # Save to file
    save_users()
    
    await interaction.followup.send(f"Votre nom d'utilisateur a été enregistré avec succès : {username}", ephemeral=True)

# Get the token from environment variables
bot.run(os.getenv('DISCORD_TOKEN'))

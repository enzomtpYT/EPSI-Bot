import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import json
from datetime import datetime
from dotenv import load_dotenv
import os
from PIL import Image, ImageDraw, ImageFont
import io
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# French date mapping
FRENCH_DAYS = {
    'Monday': 'Lundi',
    'Tuesday': 'Mardi',
    'Wednesday': 'Mercredi',
    'Thursday': 'Jeudi',
    'Friday': 'Vendredi',
    'Saturday': 'Samedi',
    'Sunday': 'Dimanche'
}

FRENCH_MONTHS = {
    'January': 'Janvier',
    'February': 'Février',
    'March': 'Mars',
    'April': 'Avril',
    'May': 'Mai',
    'June': 'Juin',
    'July': 'Juillet',
    'August': 'Août',
    'September': 'Septembre',
    'October': 'Octobre',
    'November': 'Novembre',
    'December': 'Décembre'
}

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
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        date_str = f"{FRENCH_DAYS[date_obj.strftime('%A')]} {date_obj.day} {FRENCH_MONTHS[date_obj.strftime('%B')]} {date_obj.year}"
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

def create_schedule_image(schedule):
    # Create a new image with white background
    padding = 20  # Padding between columns
    
    # Try to load a font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Calculate optimal column width based on content
    def get_text_width(text):
        return int(draw.textlength(text, font=font))  # Convert to integer
    
    # Create a temporary image to measure text
    temp_image = Image.new('RGB', (1, 1), 'white')
    draw = ImageDraw.Draw(temp_image)
    
    # Calculate maximum width needed for a single column
    max_width = 0
    if schedule:
        for class_info in schedule:
            if not class_info.get('name'):
                continue
                
            time_str = f"{class_info['start_time']} - {class_info['end_time']}"
            room_str = f"Salle : {class_info['room']}" if class_info['room'] else "Aucune salle spécifiée"
            teacher_str = f"Professeur : {class_info['teacher']}" if class_info['teacher'] else "Aucun professeur spécifié"
            
            # Measure each line
            max_width = max(max_width, get_text_width(class_info['name']))
            max_width = max(max_width, get_text_width(time_str))
            max_width = max(max_width, get_text_width(room_str))
            max_width = max(max_width, get_text_width(teacher_str))
    
    # Add padding and ensure minimum width
    column_width = max(max_width + 40, 300)  # 40 for padding, 300 as minimum width
    
    # Calculate total width based on number of days
    if schedule:
        unique_dates = len(set(class_info['date'] for class_info in schedule))
        total_width = int((column_width * unique_dates) + (padding * (unique_dates - 1)))  # Convert to integer
    else:
        total_width = column_width
    
    # Calculate maximum height needed for any column
    max_height = 0
    if schedule:
        # Group classes by date
        classes_by_date = {}
        for class_info in schedule:
            date = class_info['date']
            if date not in classes_by_date:
                classes_by_date[date] = []
            classes_by_date[date].append(class_info)
        
        # Calculate height for each day's content
        for date, classes in sorted(classes_by_date.items()):
            current_height = 80  # Start with header space
            for class_info in classes:
                if not class_info.get('name'):
                    continue
                current_height += 100  # Space for class content
                current_height += 10   # Space for separator
            max_height = max(max_height, current_height)
    
    # Add padding to height and ensure minimum height
    total_height = max(max_height + 40, 200)  # 40 for padding, 200 as minimum height
    
    # Create the actual image
    image = Image.new('RGB', (total_width, total_height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Title (without emoji)
    draw.text((10, 10), "Emploi du temps EPSI", font=font, fill='black')
    
    if not schedule:
        draw.text((10, 50), "Aucun cours trouvé pour la période spécifiée.", font=font, fill='black')
        return [image]
    
    # Draw each day's content in its own column
    x_position = 10
    for date, classes in sorted(classes_by_date.items()):
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        date_str = f"{FRENCH_DAYS[date_obj.strftime('%A')]} {date_obj.day} {FRENCH_MONTHS[date_obj.strftime('%B')]} {date_obj.year}"
        
        # Draw date header
        draw.text((x_position, 50), date_str, font=font, fill='blue')
        
        y_position = 80
        for class_info in classes:
            if not class_info.get('name'):
                continue
                
            time_str = f"{class_info['start_time']} - {class_info['end_time']}"
            room_str = f"Salle : {class_info['room']}" if class_info['room'] else "Aucune salle spécifiée"
            teacher_str = f"Professeur : {class_info['teacher']}" if class_info['teacher'] else "Aucun professeur spécifié"
            
            class_str = f"{class_info['name']}\n{time_str}\n{room_str}\n{teacher_str}"
            draw.text((x_position + 10, y_position), class_str, font=font, fill='black')
            y_position += 100
            
            # Add a line separator
            draw.line([(x_position, y_position), (x_position + column_width - 20, y_position)], fill='gray')
            y_position += 10
        
        x_position += column_width + padding
    
    return [image]

@bot.event
async def on_ready():
    logging.info(f'Bot prêt ! Connecté en tant que {bot.user.name} ({bot.user.id})')
    logging.info(f'Utilisateurs enregistrés : {len(users)}')
    try:
        synced = await bot.tree.sync()
        logging.info(f"Synchronisation de {len(synced)} commande(s)")
    except Exception as e:
        logging.error(f"Échec de la synchronisation des commandes : {e}")

@bot.tree.command(
    name="edt",
    description="Obtenir votre emploi du temps EPSI"
)
@app_commands.describe(
    username="Nom d'utilisateur EPSI (optionnel si vous êtes enregistré)",
    start_time="Date de début au format JJ/MM/AAAA (optionnel)",
    end_time="Date de fin au format JJ/MM/AAAA (optionnel)",
    image="Si activé, envoie l'emploi du temps sous forme d'image"
)
@app_commands.user_install()
async def schedule(
    interaction: discord.Interaction, 
    username: str = None, 
    start_time: str = None, 
    end_time: str = None,
    image: bool = False
):
    logging.info(f"Commande /edt exécutée par {interaction.user.name} (ID: {interaction.user.id})")
    logging.info(f"Paramètres: username={username}, start_time={start_time}, end_time={end_time}, image={image}")
    
    await interaction.response.defer()

    # If no username provided, check if user is registered
    if username is None:
        if not str(interaction.user.id) in users:
            logging.warning(f"Utilisateur {interaction.user.name} (ID: {interaction.user.id}) non enregistré")
            await interaction.followup.send("Merci d'enregistrer votre nom d'utilisateur avec la commande `/register` ou de spécifier un nom d'utilisateur directement.", ephemeral=True)
            return
        username = users[str(interaction.user.id)]
        logging.info(f"Utilisation du nom d'utilisateur enregistré: {username}")
    
    schedule_data = await fetch_schedule(username, start_time, end_time)
    logging.info(f"Nombre de cours trouvés: {len(schedule_data)}")
    
    if image:
        # Generate and send images
        images = create_schedule_image(schedule_data)
        files = []
        for i, img in enumerate(images):
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Create discord file
            file = discord.File(img_byte_arr, filename=f'schedule_page_{i+1}.png')
            files.append(file)
        
        await interaction.followup.send(files=files, ephemeral=True)
        logging.info(f"Image(s) envoyée(s) à {interaction.user.name}")
    else:
        # Send embed as before
        embed = create_schedule_embed(schedule_data)
        await interaction.followup.send(embed=embed, ephemeral=True)
        logging.info(f"Embed envoyé à {interaction.user.name}")

@bot.tree.command(
    name="register",
    description="Enregistrer votre nom d'utilisateur EPSI"
)
@app_commands.describe(username="Votre nom d'utilisateur EPSI")
async def register(interaction: discord.Interaction, username: str):
    logging.info(f"Commande /register exécutée par {interaction.user.name} (ID: {interaction.user.id})")
    logging.info(f"Nom d'utilisateur à enregistrer: {username}")
    
    await interaction.response.defer(ephemeral=True)
    
    # Check if user is already registered
    if str(interaction.user.id) in users:
        logging.warning(f"Tentative de réenregistrement par {interaction.user.name} (ID: {interaction.user.id})")
        await interaction.followup.send("Vous êtes déjà enregistré. Pour changer votre nom d'utilisateur, utilisez la commande `/unregister` d'abord.", ephemeral=True)
        return
    
    # Save the username to users dictionary
    users[str(interaction.user.id)] = username
    
    # Save to file
    save_users()
    
    await interaction.followup.send(f"Votre nom d'utilisateur a été enregistré avec succès : {username}", ephemeral=True)
    logging.info(f"Utilisateur {interaction.user.name} (ID: {interaction.user.id}) enregistré avec le nom d'utilisateur: {username}")

# Get the token from environment variables
bot.run(os.getenv('DISCORD_TOKEN'))

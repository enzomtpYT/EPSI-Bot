import discord
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io

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
    # Create a new image with dark background
    padding = 20  # Padding between columns
    
    text_size = 14
    date_text_size = 18
    class_text_size = 16

    # Load fonts
    font = ImageFont.truetype("Assets/Helvetica.ttf", text_size)
    date_font = ImageFont.truetype("Assets/Helvetica-Bold.ttf", date_text_size)  # Larger and bold font for dates
    
    # Calculate optimal column width based on content
    def get_text_width(text):
        return int(draw.textlength(text, font=font))  # Convert to integer
    
    # Create a temporary image to measure text
    temp_image = Image.new('RGB', (1, 1), '#1a1a1a')  # Dark background
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
            current_height = 10  # Start with header space
            for class_info in classes:
                if not class_info.get('name'):
                    continue
                current_height += 60  # Space for class content
                current_height += 10   # Space for separator
            max_height = max(max_height, current_height)
    
    # Add padding to height and ensure minimum height
    total_height = max(max_height + 40, 200)  # 40 for padding, 200 as minimum height
    
    # Create the actual image with dark background
    image = Image.new('RGB', (total_width, total_height), '#1a1a1a')  # Dark background
    draw = ImageDraw.Draw(image)
    
    if not schedule:
        draw.text((10, 10), "Aucun cours trouvé pour la période spécifiée.", font=font, fill='#ffffff')  # White text
        return [image]
    
    # Draw each day's content in its own column
    x_position = 10
    for date, classes in sorted(classes_by_date.items()):
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        date_str = f"{FRENCH_DAYS[date_obj.strftime('%A')]} {date_obj.day} {FRENCH_MONTHS[date_obj.strftime('%B')]} {date_obj.year}"
        
        y_position = 10

        # Draw date header
        bbox = draw.textbbox((0, 0), date_str, font=date_font)  # Light blue text with larger bold font
        draw.text((x_position-10+column_width/2 - (bbox[2] - bbox[0])/2, 10), date_str, font=date_font, fill='#4a9eff')  # Light blue text with larger bold font
        y_position += date_text_size + 10

        for class_info in classes:
            if not class_info.get('name'):
                continue
                
            time_str = f"{class_info['start_time']} - {class_info['end_time']}"
            room_str = f"Salle : {class_info['room']}" if class_info['room'] else "Aucune salle spécifiée"
            teacher_str = f"Professeur : {class_info['teacher']}" if class_info['teacher'] else "Aucun professeur spécifié"
            
            class_str = f"{class_info['name']}\n{time_str}\n{room_str}\n{teacher_str}"
            draw.text((x_position, y_position), class_str, font=font, fill='#ffffff')  # White text
            y_position += 70
            
            # Add a line separator
            draw.line([(x_position, y_position), (x_position + column_width - 20, y_position)], fill='#333333')  # Dark gray separator
            y_position += 10
        
        x_position += column_width + padding
    
    return [image] 
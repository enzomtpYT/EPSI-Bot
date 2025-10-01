import discord
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import random


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
    
    classes_by_date = {}
    for class_info in schedule:
        date = class_info['date']
        classes_by_date.setdefault(date, []).append(class_info)
    
    for date, classes in sorted(classes_by_date.items()):
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        date_str = f"{FRENCH_DAYS[date_obj.strftime('%A')]} {date_obj.day} {FRENCH_MONTHS[date_obj.strftime('%B')]} {date_obj.year}"
        class_list = []
        
        for class_info in classes:
            if not class_info.get('name'):
                continue
            time_str = f"{class_info['start_time']} - {class_info['end_time']}"
            room_str = f"Salle : {class_info['room']}" if class_info.get('room') else "Aucune salle spécifiée"
            teacher_str = f"Professeur : {class_info['teacher']}" if class_info.get('teacher') else "Aucun professeur spécifié"
            
            class_str = f"**{class_info['name']}**\n{time_str}\n{room_str}\n{teacher_str}\n"
            class_list.append(class_str)
        
        if class_list:
            embed.add_field(
                name=date_str,
                value="\n".join(class_list),
                inline=False
            )
    return embed


def random_pastel_color():
    base = 150
    r = random.randint(base, 255)
    g = random.randint(base, 255)
    b = random.randint(base, 255)
    return (r, g, b)


def text_color_for_bg(bg_color):
    r, g, b = bg_color
    lum = 0.2126 * (r/255) + 0.7152 * (g/255) + 0.0722 * (b/255)
    return (0, 0, 0) if lum > 0.6 else (255, 255, 255)


def draw_rounded_rectangle(draw, coordinates, radius, fill=None, outline=None):
    """Draw a rectangle with rounded corners."""
    x0, y0, x1, y1 = coordinates
    
    # Draw the main rectangles (body of the rounded rectangle)
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill, outline=outline)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill, outline=outline)
    
    # Draw the four corner circles
    draw.ellipse([x0, y0, x0 + 2 * radius, y0 + 2 * radius], fill=fill, outline=outline)  # Top-left
    draw.ellipse([x1 - 2 * radius, y0, x1, y0 + 2 * radius], fill=fill, outline=outline)  # Top-right
    draw.ellipse([x0, y1 - 2 * radius, x0 + 2 * radius, y1], fill=fill, outline=outline)  # Bottom-left
    draw.ellipse([x1 - 2 * radius, y1 - 2 * radius, x1, y1], fill=fill, outline=outline)  # Bottom-right


def create_schedule_image(schedule):
    padding = 20
    text_size = 14
    date_text_size = 18

    font = ImageFont.truetype("Assets/Helvetica.ttf", text_size)
    date_font = ImageFont.truetype("Assets/Helvetica-Bold.ttf", date_text_size)

    temp_image = Image.new('RGB', (1, 1), "#1a1a1a")
    temp_draw = ImageDraw.Draw(temp_image)
    def get_text_width(txt):
        return int(temp_draw.textlength(txt, font=font))

    max_width = 0
    for c in schedule:
        if not c.get('name'):
            continue
        time_str = f"{c['start_time']} - {c['end_time']}"
        room_str = f"Salle : {c['room']}" if c.get('room') else "Aucune salle spécifiée"
        teacher_str = f"Professeur : {c['teacher']}" if c.get('teacher') else "Aucun professeur spécifié"
        max_width = max(max_width, get_text_width(c['name']), get_text_width(time_str),
                        get_text_width(room_str), get_text_width(teacher_str))

    column_width = max(max_width + 40, 300)
    unique_dates = len(set(c['date'] for c in schedule)) if schedule else 1
    total_width = int(unique_dates * column_width + (unique_dates - 1) * padding)

    classes_by_date = {}
    for c in schedule:
        classes_by_date.setdefault(c['date'], []).append(c)

    max_height = 0
    for date, classes in classes_by_date.items():
        h = date_text_size
        for c in sorted(classes, key=lambda x: x.get('start_time', "")):
            if not c.get('name'):
                continue
            st = datetime.strptime(c['start_time'], "%H:%M")
            et = datetime.strptime(c['end_time'], "%H:%M")
            dur_min = (et - st).seconds // 60
            block_h = max(dur_min * 1, 50)  
            h += int(block_h)
            h += 40  
        max_height = max(max_height, h)

    total_height = max(max_height + 40, 400)
    image = Image.new('RGB', (total_width, total_height), "#1a1a1a")
    draw = ImageDraw.Draw(image)

    if not schedule:
        draw.text((10, 10), "Aucun cours trouvé pour la période spécifiée.", font=font, fill=(255, 255, 255))
        return [image]

    x_position = 10

    for date, classes in sorted(classes_by_date.items()):
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        date_str = f"{FRENCH_DAYS[date_obj.strftime('%A')]} {date_obj.day} {FRENCH_MONTHS[date_obj.strftime('%B')]} {date_obj.year}"

        y_position = 10
        bbox = draw.textbbox((0, 0), date_str, font=date_font)
        draw.text(
            (x_position - 10 + column_width / 2 - (bbox[2] - bbox[0]) / 2, 10),
            date_str, font=date_font, fill="#4a9eff"
        )
        y_position += date_text_size + 10

        previous_end_time = None
        previous_block_bottom = y_position

        for c in sorted(classes, key=lambda x: x.get('start_time', "")):
            if not c.get('name'):
                continue
            st = datetime.strptime(c['start_time'], "%H:%M")
            et = datetime.strptime(c['end_time'], "%H:%M")
            dur_min = (et - st).seconds // 60
            size = dur_min / 60 * 64

            if previous_end_time:
                if st > previous_end_time:
                    gap = (st - previous_end_time).seconds // 60
                    gap_size = gap/60 * 4 
                    y_position += int(gap * 1) + gap_size
                else:
                    y_position = previous_block_bottom  

            time_str = f"{c['start_time']} - {c['end_time']}"
            room_str = f"Salle : {c['room']}" if c.get('room') else "Aucune salle spécifiée"
            teacher_str = f"Professeur : {c['teacher']}" if c.get('teacher') else "Aucun professeur spécifié"
            class_str = f"{c['name']}\n{time_str}\n{room_str}\n{teacher_str}"

            tb = draw.multiline_textbbox((0, 0), class_str, font=font)
            text_h = tb[3] - tb[1]

            pad_x = 5
            pad_y = 4
            bg = random_pastel_color()
            txt_color = text_color_for_bg(bg)

            block_h = max(text_h + pad_y * 2, int(size))

            rect_x0 = x_position
            rect_y0 = y_position
            rect_x1 = x_position + column_width - 20
            rect_y1 = y_position + block_h

            # Draw rounded rectangle with 8px radius
            draw_rounded_rectangle(draw, (rect_x0, rect_y0, rect_x1, rect_y1), radius=8, fill=bg)
            draw.multiline_text((x_position + pad_x, y_position + pad_y), class_str, font=font, fill=txt_color)

            previous_end_time = et
            previous_block_bottom = rect_y1

            y_position = rect_y1
            draw.line([(rect_x0, y_position), (rect_x1, y_position)], fill="#333333")
            y_position += 10

        x_position += column_width + padding

    return [image]

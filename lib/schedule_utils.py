import discord, random, cairo, os, colorsys, io
from datetime import datetime


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


def random_pastel_color(name=None):
    """Generate a random pastel color based on a name for consistency"""
    if name:
        seed_value = sum(ord(c) for c in str(name))
        random.seed(seed_value)
    else:
        random.seed(datetime.now().timestamp())
    
    # Generate random hue (0-1), fixed saturation and luminance
    hue = random.random()
    saturation = 0.50
    luminance = 0.75
    
    # Convert HSL to RGB
    r, g, b = colorsys.hls_to_rgb(hue, luminance, saturation)
    
    # Convert to 0-255 range
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)
    
    random.seed()
    
    return (r, g, b)


def text_color_for_bg(bg_color):
    r, g, b = bg_color
    lum = 0.2126 * (r/255) + 0.7152 * (g/255) + 0.0722 * (b/255)
    return (0, 0, 0) if lum > 0.6 else (255, 255, 255)

def draw_rounded_rectangle(ctx, x, y, width, height, radius):
    """Draw a rounded rectangle using Cairo"""
    import math
    
    # Adjust radius if it's larger than half the width or height
    radius = min(radius, width / 2, height / 2)
    
    # Start at top-left corner (but moved right by radius)
    ctx.move_to(x + radius, y)
    
    # Top edge and top-right corner
    ctx.line_to(x + width - radius, y)
    ctx.arc(x + width - radius, y + radius, radius, -math.pi/2, 0)
    
    # Right edge and bottom-right corner
    ctx.line_to(x + width, y + height - radius)
    ctx.arc(x + width - radius, y + height - radius, radius, 0, math.pi/2)
    
    # Bottom edge and bottom-left corner
    ctx.line_to(x + radius, y + height)
    ctx.arc(x + radius, y + height - radius, radius, math.pi/2, math.pi)
    
    # Left edge and top-left corner
    ctx.line_to(x, y + radius)
    ctx.arc(x + radius, y + radius, radius, math.pi, 3*math.pi/2)
    
    ctx.close_path()

def day_schedule_image(schedule):
    """Generate a daily schedule image using Cairo with time-based grid"""
    if not schedule:
        return False, "No schedule data provided"
    
    # Image dimensions - narrower for single day
    WIDTH = 800
    HEIGHT = 900
    MARGIN = 60
    HEADER_HEIGHT = 80
    TIME_COLUMN_WIDTH = 80
    
    # Time configuration (9h to 18h)
    START_HOUR = 9
    END_HOUR = 18
    TOTAL_HOURS = END_HOUR - START_HOUR
    
    # Create Cairo surface and context
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)
    
    # Load custom fonts
    try:
        helvetica_path = os.path.join("Assets", "Helvetica.ttf")
        helvetica_bold_path = os.path.join("Assets", "Helvetica-Bold.ttf")
        
        # Create font face from file
        helvetica_face = cairo.FontFace.create_from_ft_font_file(helvetica_path)
        helvetica_bold_face = cairo.FontFace.create_from_ft_font_file(helvetica_bold_path)
    except:
        helvetica_face = None
        helvetica_bold_face = None
    
    # Background
    ctx.set_source_rgb(1, 1, 1)  # White background
    ctx.paint()
    
    # Get the first date from schedule (assuming all items are from the same day)
    first_item = schedule[0]
    date = first_item['date']
    
    # Calculate grid dimensions - single day takes full width
    day_width = WIDTH - TIME_COLUMN_WIDTH - 2 * MARGIN
    
    # Calculate time grid dimensions
    grid_start_y = HEADER_HEIGHT + 80
    available_height = HEIGHT - grid_start_y - MARGIN
    hour_height = available_height / TOTAL_HOURS
    
    # Draw title
    if helvetica_bold_face:
        ctx.set_font_face(helvetica_bold_face)
    else:
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(28)
    ctx.set_source_rgb(0.2, 0.2, 0.2)
    
    title = "Emploi du temps EPSI"
    text_extents = ctx.text_extents(title)
    title_x = (WIDTH - text_extents.width) / 2
    ctx.move_to(title_x, 40)
    ctx.show_text(title)
    
    # Draw time column
    if helvetica_bold_face:
        ctx.set_font_face(helvetica_bold_face)
    else:
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(14)
    ctx.set_source_rgb(0.1, 0.1, 0.1)  # Much darker for better readability
    
    for hour in range(START_HOUR, END_HOUR + 1):
        y = grid_start_y + (hour - START_HOUR) * hour_height
        time_text = f"{hour:02d}:00"
        text_extents = ctx.text_extents(time_text)
        ctx.move_to(MARGIN + TIME_COLUMN_WIDTH - text_extents.width - 15, y + 6)
        ctx.show_text(time_text)
        
        # Draw horizontal grid line
        ctx.set_source_rgb(0.9, 0.9, 0.9)
        ctx.set_line_width(1)
        ctx.move_to(MARGIN + TIME_COLUMN_WIDTH, y)
        ctx.line_to(WIDTH - MARGIN, y)
        ctx.stroke()
        
        ctx.set_source_rgb(0.1, 0.1, 0.1)
    
    # Draw day header
    x = MARGIN + TIME_COLUMN_WIDTH
    
    # Parse date
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        day_name = FRENCH_DAYS[date_obj.strftime('%A')]
        date_str = f"{day_name}\n{date_obj.day:02d}/{date_obj.month:02d}"
    except (ValueError, KeyError):
        day_name = date
        date_str = date
    
    # Draw day header background
    ctx.set_source_rgb(0.2, 0.4, 0.7)
    ctx.rectangle(x, HEADER_HEIGHT, day_width, 60)
    ctx.fill()
    
    # Draw day header text
    if helvetica_bold_face:
        ctx.set_font_face(helvetica_bold_face)
    else:
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(20)
    ctx.set_source_rgb(1, 1, 1)
    
    lines = date_str.split('\n')
    for j, line in enumerate(lines):
        text_extents = ctx.text_extents(line)
        text_x = x + (day_width - text_extents.width) / 2
        text_y = HEADER_HEIGHT + 25 + j * 22
        ctx.move_to(text_x, text_y)
        ctx.show_text(line)
    
    # Draw courses for this day based on time
    for course in schedule:
        try:
            # Parse start and end times
            start_time = course.get('start_time', '09:00')
            end_time = course.get('end_time', '10:00')
            
            start_hour = float(start_time.split(':')[0]) + float(start_time.split(':')[1]) / 60
            end_hour = float(end_time.split(':')[0]) + float(end_time.split(':')[1]) / 60
            
            # Calculate position and size
            course_start_y = grid_start_y + (start_hour - START_HOUR) * hour_height
            course_height = (end_hour - start_hour) * hour_height
            
            # Skip if course is outside our time range
            if start_hour < START_HOUR or end_hour > END_HOUR:
                continue
            
            # Generate a color for this course
            color = random_pastel_color(course.get('name'))
            bg_r, bg_g, bg_b = [c/255 for c in color]
            
            # Draw course background with rounded corners
            ctx.set_source_rgb(bg_r, bg_g, bg_b)
            draw_rounded_rectangle(ctx, x + 2, course_start_y, day_width - 4, course_height - 2, 16)
            ctx.fill()
            
            # Determine text color based on background
            text_color = text_color_for_bg(color)
            text_r, text_g, text_b = [c/255 for c in text_color]
            ctx.set_source_rgb(text_r, text_g, text_b)
            
            # Draw course text
            if helvetica_bold_face:
                ctx.set_font_face(helvetica_bold_face)
            else:
                ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            
            # Adjust font size and spacing based on course height
            if course_height > 80:
                line_spacing = 18
                font_size = 18
            elif course_height > 40:
                line_spacing = 14
                font_size = 14
            else:
                line_spacing = 12
                font_size = 12
            
            text_x = x + 15
            current_y = course_start_y + 30
            
            # Course name (can be longer since we have more width)
            name = course.get('name', 'Cours')
            max_chars = int((day_width - 30) / 10)  # More space for text
            if len(name) > max_chars:
                name = name[:max_chars-3] + "..."
            
            ctx.set_font_size(font_size)
            ctx.move_to(text_x, current_y)
            ctx.show_text(name)
            current_y += line_spacing
            
            # Time (only if there's space)
            if course_height > 30:
                if helvetica_face:
                    ctx.set_font_face(helvetica_face)
                else:
                    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                ctx.set_font_size(font_size - 2)
                time_str = f"{start_time} - {end_time}"
                ctx.move_to(text_x, current_y)
                ctx.show_text(time_str)
                current_y += line_spacing
            
            # Room (only if there's space)
            if course_height > 50:
                room = course.get('room', '')
                if room:
                    if helvetica_face:
                        ctx.set_font_face(helvetica_face)
                    else:
                        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                    room_text = f"Salle: {room}"
                    if len(room_text) > max_chars:
                        room_text = room_text[:max_chars-3] + "..."
                    ctx.move_to(text_x, current_y)
                    ctx.show_text(room_text)
                    current_y += line_spacing
            
            # Teacher (only if there's space)
            if course_height > 70:
                teacher = course.get('teacher', '')
                if teacher:
                    if helvetica_face:
                        ctx.set_font_face(helvetica_face)
                    else:
                        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                    teacher_text = teacher
                    if len(teacher_text) > max_chars:
                        teacher_text = teacher_text[:max_chars-3] + "..."
                    ctx.set_font_size(font_size - 4)
                    ctx.move_to(text_x, current_y)
                    ctx.show_text(teacher_text)
            
        except (ValueError, IndexError) as e:
            # Skip courses with invalid time format
            continue
    
    # Convert surface to bytes
    try:
        png_buffer = io.BytesIO()
        surface.write_to_png(png_buffer)
        png_buffer.seek(0)
        image_bytes = png_buffer.getvalue()
        return True, image_bytes
    except Exception as e:
        return False, f"Error generating PNG: {str(e)}"
    finally:
        surface.finish()

def week_schedule_image(schedule):
    """Generate a weekly schedule image using Cairo with time-based grid"""
    if not schedule:
        return False, "No schedule data provided"
    
    # Image dimensions
    WIDTH = 1600
    HEIGHT = 900
    MARGIN = 60
    HEADER_HEIGHT = 80
    TIME_COLUMN_WIDTH = 80
    
    # Time configuration (9h to 18h)
    START_HOUR = 9
    END_HOUR = 18
    TOTAL_HOURS = END_HOUR - START_HOUR
    
    # Create Cairo surface and context
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)
    
    # Load custom fonts
    try:
        helvetica_path = os.path.join("Assets", "Helvetica.ttf")
        helvetica_bold_path = os.path.join("Assets", "Helvetica-Bold.ttf")
        
        # Create font face from file
        helvetica_face = cairo.FontFace.create_from_ft_font_file(helvetica_path)
        helvetica_bold_face = cairo.FontFace.create_from_ft_font_file(helvetica_bold_path)
    except:
        helvetica_face = None
        helvetica_bold_face = None
    
    # Background
    ctx.set_source_rgb(1, 1, 1)  # White background
    ctx.paint()
    
    # Organize schedule by date
    schedule_by_date = {}
    for item in schedule:
        date = item['date']
        if date not in schedule_by_date:
            schedule_by_date[date] = []
        schedule_by_date[date].append(item)
    
    # Sort dates
    sorted_dates = sorted(schedule_by_date.keys())
    
    if not sorted_dates:
        return False, "No valid dates in schedule"
    
    # Calculate grid dimensions
    days_count = len(sorted_dates)
    available_width = WIDTH - TIME_COLUMN_WIDTH - 2 * MARGIN
    day_width = available_width / days_count
    
    # Calculate time grid dimensions
    grid_start_y = HEADER_HEIGHT + 80
    available_height = HEIGHT - grid_start_y - MARGIN
    hour_height = available_height / TOTAL_HOURS
    
    # Draw title
    if helvetica_bold_face:
        ctx.set_font_face(helvetica_bold_face)
    else:
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(28)
    ctx.set_source_rgb(0.2, 0.2, 0.2)
    
    title = "Emploi du temps EPSI"
    text_extents = ctx.text_extents(title)
    title_x = (WIDTH - text_extents.width) / 2
    ctx.move_to(title_x, 40)
    ctx.show_text(title)
    
    # Draw time column
    if helvetica_bold_face:
        ctx.set_font_face(helvetica_bold_face)
    else:
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(14)
    ctx.set_source_rgb(0.1, 0.1, 0.1)  # Much darker for better readability
    
    for hour in range(START_HOUR, END_HOUR + 1):
        y = grid_start_y + (hour - START_HOUR) * hour_height
        time_text = f"{hour:02d}:00"
        text_extents = ctx.text_extents(time_text)
        ctx.move_to(MARGIN + TIME_COLUMN_WIDTH - text_extents.width - 15, y + 6)
        ctx.show_text(time_text)
        
        # Draw horizontal grid line
        ctx.set_source_rgb(0.9, 0.9, 0.9)
        ctx.set_line_width(1)
        ctx.move_to(MARGIN + TIME_COLUMN_WIDTH, y)
        ctx.line_to(WIDTH - MARGIN, y)
        ctx.stroke()
        
        ctx.set_source_rgb(0.1, 0.1, 0.1)
    
    # Draw day headers and vertical grid lines
    for i, date in enumerate(sorted_dates):
        x = MARGIN + TIME_COLUMN_WIDTH + i * day_width
        
        # Parse date
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            day_name = FRENCH_DAYS[date_obj.strftime('%A')]
            date_str = f"{day_name}\n{date_obj.day:02d}/{date_obj.month:02d}"
        except (ValueError, KeyError):
            day_name = date
            date_str = date
        
        # Draw day header background
        ctx.set_source_rgb(0.2, 0.4, 0.7)
        ctx.rectangle(x, HEADER_HEIGHT, day_width, 60)
        ctx.fill()
        
        # Draw day header text
        if helvetica_bold_face:
            ctx.set_font_face(helvetica_bold_face)
        else:
            ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(18)
        ctx.set_source_rgb(1, 1, 1)
        
        lines = date_str.split('\n')
        for j, line in enumerate(lines):
            text_extents = ctx.text_extents(line)
            text_x = x + (day_width - text_extents.width) / 2
            text_y = HEADER_HEIGHT + 25 + j * 20
            ctx.move_to(text_x, text_y)
            ctx.show_text(line)
        
        # Draw courses for this day based on time
        courses = schedule_by_date[date]
        
        for course in courses:
            try:
                # Parse start and end times
                start_time = course.get('start_time', '09:00')
                end_time = course.get('end_time', '10:00')
                
                start_hour = float(start_time.split(':')[0]) + float(start_time.split(':')[1]) / 60
                end_hour = float(end_time.split(':')[0]) + float(end_time.split(':')[1]) / 60
                
                # Calculate position and size
                course_start_y = grid_start_y + (start_hour - START_HOUR) * hour_height
                course_height = (end_hour - start_hour) * hour_height
                
                # Skip if course is outside our time range
                if start_hour < START_HOUR or end_hour > END_HOUR:
                    continue
                
                # Generate a color for this course
                color = random_pastel_color(course.get('name'))
                bg_r, bg_g, bg_b = [c/255 for c in color]
                
                # Draw course background with rounded corners
                ctx.set_source_rgb(bg_r, bg_g, bg_b)
                draw_rounded_rectangle(ctx, x + 2, course_start_y, day_width - 4, course_height - 2, 16)
                ctx.fill()
                
                # Determine text color based on background
                text_color = text_color_for_bg(color)
                text_r, text_g, text_b = [c/255 for c in text_color]
                ctx.set_source_rgb(text_r, text_g, text_b)
                
                # Draw course text
                if helvetica_bold_face:
                    ctx.set_font_face(helvetica_bold_face)
                else:
                    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                
                # Adjust font size based on course height
                if course_height > 80:
                    line_spacing = 14
                elif course_height > 40:
                    line_spacing = 12
                else:
                    line_spacing = 10
                
                text_x = x + 11
                current_y = course_start_y + 25
                
                # Course name (truncated if too long)
                name = course.get('name', 'Cours')
                max_chars = int((day_width - 24) / 7)
                if len(name) > max_chars:
                    name = name[:max_chars-3] + "..."
                
                ctx.set_font_size(16)
                ctx.move_to(text_x, current_y)
                ctx.show_text(name)
                current_y += line_spacing
                
                # Time (only if there's space)
                if course_height > 30:
                    if helvetica_face:
                        ctx.set_font_face(helvetica_face)
                    else:
                        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                    ctx.set_font_size(12)
                    time_str = f"{start_time} - {end_time}"
                    ctx.move_to(text_x, current_y)
                    ctx.show_text(time_str)
                    current_y += line_spacing
                
                # Room (only if there's space)
                if course_height > 50:
                    room = course.get('room', '')
                    if room:
                        if helvetica_face:
                            ctx.set_font_face(helvetica_face)
                        else:
                            ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                        room_text = f"Salle: {room}"
                        if len(room_text) > max_chars:
                            room_text = room_text[:max_chars-3] + "..."
                        ctx.move_to(text_x, current_y)
                        ctx.show_text(room_text)
                        current_y += line_spacing
                
                # Teacher (only if there's space)
                if course_height > 70:
                    teacher = course.get('teacher', '')
                    if teacher:
                        if helvetica_face:
                            ctx.set_font_face(helvetica_face)
                        else:
                            ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                        teacher_text = teacher
                        if len(teacher_text) > max_chars:
                            teacher_text = teacher_text[:max_chars-3] + "..."
                        ctx.move_to(text_x, current_y)
                        ctx.show_text(teacher_text)
                
            except (ValueError, IndexError) as e:
                # Skip courses with invalid time format
                continue
    
    # Convert surface to bytes
    try:
        png_buffer = io.BytesIO()
        surface.write_to_png(png_buffer)
        png_buffer.seek(0)
        image_bytes = png_buffer.getvalue()
        return True, image_bytes
    except Exception as e:
        return False, f"Error generating PNG: {str(e)}"
    finally:
        surface.finish()
import asyncio
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from lib.user_manager import users, load_users, get_user
from lib.api import fetch_day_schedule
from lib.schedule_utils import create_schedule_embed


SENT_FILE = './data/sent_notifications.json'


def ensure_data_dir():
    os.makedirs(os.path.dirname(SENT_FILE), exist_ok=True)


def load_sent() -> Dict[str, Any]:
    ensure_data_dir()
    if not os.path.exists(SENT_FILE):
        with open(SENT_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        return {}
    try:
        with open(SENT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        logging.exception('Could not load sent_notifications.json, resetting file')
        with open(SENT_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        return {}


def save_sent(data: Dict[str, Any]):
    ensure_data_dir()
    with open(SENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def parse_course_datetime(course) -> datetime:
    try:
        date_str = course.get('date')
        time_str = course.get('start_time', '00:00')
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        return dt
    except Exception:
        return None


async def notifier_loop(bot, check_interval: int = 60):
    """Background task that checks schedules and sends notifications 10 minutes before class.

    Behavior:
    - Only users with preference `daily` enabled will receive notifications.
    - If `NOTIFY_CHANNEL_ID` env var is set, tries to send notification in that channel mentioning the user.
      Otherwise falls back to DM.
    - Records sent notifications in `./data/sent_notifications.json` to avoid duplicates.
    """
    logging.info('Notifier loop starting')
    load_users()
    sent = load_sent()
    notify_channel_id = os.getenv('NOTIFY_CHANNEL_ID', '1422138739840254039')

    while not bot.is_closed():
        try:
            now = datetime.now()
            for discord_id, info in list(users.items()):
                try:
                    username = info.get('username')
                    if not username:
                        continue

                    schedule = await fetch_day_schedule(username)
                    if not schedule:
                        continue

                    for course in schedule:
                        course_dt = parse_course_datetime(course)
                        if not course_dt:
                            continue
                        notify_time = course_dt - timedelta(minutes=10)

                        if notify_time.date() != now.date():
                            continue

                        if notify_time <= now < notify_time + timedelta(seconds=check_interval):
                            key = f"{discord_id}-{course.get('date')}-{course.get('start_time')}"
                            if sent.get(key):
                                continue

                            embed = create_schedule_embed([course])
                            content = f"Rappel : <@{discord_id}> votre cours commence dans 10 minutes : **{course.get('name', 'Cours')}**"

                            if notify_channel_id:
                                try:
                                    chan_id = int(notify_channel_id)
                                    channel = bot.get_channel(chan_id)
                                    if channel is None:
                                        try:
                                            channel = await bot.fetch_channel(chan_id)
                                        except Exception:
                                            channel = None
                                    if channel is not None:
                                        await channel.send(content=content, embed=embed)
                                        logging.info(f"Sent notification to channel {chan_id} for user {discord_id}")
                                        sent[key] = datetime.now().isoformat()
                                        save_sent(sent)
                                        continue
                                except Exception:
                                    logging.exception('Failed to send notification to configured channel')

                            try:
                                user_obj = await bot.fetch_user(int(discord_id))
                                await user_obj.send(content=content, embed=embed)
                                logging.info(f"Sent DM notification to user {discord_id} for course {course.get('name')}")
                                sent[key] = datetime.now().isoformat()
                                save_sent(sent)
                            except Exception:
                                logging.exception(f"Failed to send DM notification to user {discord_id}")
                except Exception:
                    logging.exception('Error processing user in notifier loop')

            await asyncio.sleep(check_interval)
        except Exception:
            logging.exception('Unexpected error in notifier loop')
            await asyncio.sleep(check_interval)

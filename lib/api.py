import aiohttp
import os
import asyncio
from aiohttp import ClientTimeout
import logging
from datetime import datetime

async def fetch_schedule(user, start_time=None, end_time=None, max_retries=3):
    """Legacy function, kept for backward compatibility"""
    return await fetch_week_schedule(user, start_time, max_retries)

async def fetch_day_schedule(user, date=None, max_retries=3):
    """Fetch schedule for a specific day"""
    logging.info(f"Fetching day schedule for user {user}, date: {date}")
    base_url = os.getenv('API_URL', 'https://epsi.enzomtp.party')
    
    # If no date provided, use current date
    if date is None:
        date_obj = datetime.now()
    else:
        # Parse the date string into a datetime object
        date_obj = datetime.strptime(date, "%d/%m/%Y")
    
    # Format the date as DD-MM-YYYY for the API request
    formatted_date = date_obj.strftime("%d-%m-%Y")
    
    url = f"{base_url}/{formatted_date}?user={user}"
    logging.info(f"Requesting URL: {url}")
    
    timeout = ClientTimeout(total=30)  # 30 seconds timeout
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        logging.error(f"API request failed with status {response.status}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                            continue
                        raise Exception(f"API request failed with status {response.status}")
        except aiohttp.ClientError as e:
            logging.error(f"Network error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                continue
            raise Exception(f"Failed to connect to API after {max_retries} attempts: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
                continue
            raise
    
    raise Exception("Failed to fetch day schedule after all retry attempts")

async def fetch_week_schedule(user, date=None, max_retries=3):
    """Fetch schedule for an entire week"""
    logging.info(f"Fetching week schedule for user {user}, date: {date}")
    base_url = os.getenv('API_URL', 'https://epsi.enzomtp.party')
    
    # If no date provided, use current date
    if date is None:
        date_obj = datetime.now()
    else:
        # Parse the date string into a datetime object
        date_obj = datetime.strptime(date, "%d/%m/%Y")
    
    # Format the date as DD-MM-YYYY for the API request
    formatted_date = date_obj.strftime("%d-%m-%Y")
    
    url = f"{base_url}/week/{formatted_date}?user={user}"
    logging.info(f"Requesting URL: {url}")
    
    timeout = ClientTimeout(total=30)  # 30 seconds timeout
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Flatten the nested array and filter out empty days
                        flattened_data = []
                        for day in data:
                            if day and any(course.get('name') for course in day):
                                flattened_data.extend(day)
                        return flattened_data
                    else:
                        logging.error(f"API request failed with status {response.status}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                            continue
                        raise Exception(f"API request failed with status {response.status}")
        except aiohttp.ClientError as e:
            logging.error(f"Network error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                continue
            raise Exception(f"Failed to connect to API after {max_retries} attempts: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
                continue
            raise
    
    raise Exception("Failed to fetch week schedule after all retry attempts")
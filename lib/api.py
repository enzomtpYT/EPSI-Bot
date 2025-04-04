import aiohttp
import os
import asyncio
from aiohttp import ClientTimeout
import logging

async def fetch_schedule(user, start_time=None, end_time=None, max_retries=3):
    print(f"Fetching schedule for user {user}")
    base_url = os.getenv('API_URL', 'https://epsi.enzomtp.party')
    url = f"{base_url}/?user={user}"
    if start_time and end_time:
        url += f"&begin={start_time}&end={end_time}"
    
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
    
    raise Exception("Failed to fetch schedule after all retry attempts") 
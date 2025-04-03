import aiohttp
import os

async def fetch_schedule(user, start_time=None, end_time=None):
    print(f"Fetching schedule for user {user}")
    base_url = os.getenv('API_URL', 'https://epsi.enzomtp.party')
    url = f"{base_url}/?user={user}"
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
            else:
                print(f"Error fetching schedule for user {user}: {response.status}")
                return [] 
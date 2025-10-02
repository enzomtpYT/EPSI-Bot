import json
import os
from datetime import datetime

# Global users dictionary
users = {}
USERS_FILE = './data/users.json'

def ensure_data_directory():
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)

def load_users():
    global users
    try:
        ensure_data_directory()
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
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
        if os.path.exists(USERS_FILE):
            backup_name = os.path.join(os.path.dirname(USERS_FILE), f'users_backup_{int(datetime.now().timestamp())}.json')
            os.rename(USERS_FILE, backup_name)
        save_users()
    except Exception as e:
        print(f"Unexpected error loading users: {e}")
        users = {}
        save_users()

def save_users():
    ensure_data_directory()
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)

def get_user(user_id):
    return users.get(str(user_id), {}).get("username")

def set_user(user_id, username):
    if str(user_id) not in users:
        users[str(user_id)] = {"username": username, "daily": False, "weekly": False}
    else:
        users[str(user_id)]["username"] = username
    save_users()

def set_user_preference(user_id, preference, value):
    if str(user_id) in users:
        if preference in ["daily", "weekly"]:
            users[str(user_id)][preference] = value
            save_users()
            return True
    return False

def get_user_preference(user_id, preference):
    if str(user_id) in users:
        return users[str(user_id)].get(preference, False)
    return False

def remove_user(user_id):
    if str(user_id) in users:
        del users[str(user_id)]
        save_users()
        return True
    return False 
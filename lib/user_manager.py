import json
import os
from datetime import datetime

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

def get_user(user_id):
    return users.get(str(user_id))

def set_user(user_id, username):
    users[str(user_id)] = username
    save_users()

def remove_user(user_id):
    if str(user_id) in users:
        del users[str(user_id)]
        save_users()
        return True
    return False 
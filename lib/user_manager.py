"""User manager module using PostgreSQL database instead of JSON.

All user operations now interact with the Peewee User model defined in db.py.
"""

from lib.db import db, User, initialize_db
from peewee import DoesNotExist


def load_users():
    """Initialize the database connection and create tables if needed.
    
    This replaces the old JSON file loading. Call this at application startup.
    """
    try:
        initialize_db()
        print(f"Database initialized successfully. User table ready.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise


def save_users():
    """No-op function for backward compatibility.
    
    Database changes are committed immediately, so this is not needed.
    Kept for compatibility with existing code that calls save_users().
    """
    pass


def get_user(user_id):
    """Get a user's username by their Discord ID.
    
    Args:
        user_id: Discord user ID (int or str)
        
    Returns:
        Username string if found, None otherwise
    """
    try:
        user = User.get_by_id(int(user_id))
        return user.username
    except DoesNotExist:
        return None
    except Exception as e:
        print(f"Error getting user {user_id}: {e}")
        return None


def set_user(user_id, username):
    """Create or update a user's username.
    
    Args:
        user_id: Discord user ID (int or str)
        username: User's Discord username
    """
    try:
        user_id = int(user_id)
        user, created = User.get_or_create(
            id=user_id,
            defaults={'username': username, 'daily': False, 'weekly': False}
        )
        if not created:
            # Update username if user already exists
            user.username = username
            user.save()
    except Exception as e:
        print(f"Error setting user {user_id}: {e}")


def set_user_preference(user_id, preference, value):
    """Set a user's preference (daily or weekly reminders).
    
    Args:
        user_id: Discord user ID (int or str)
        preference: Either "daily" or "weekly"
        value: Boolean value for the preference
        
    Returns:
        True if successful, False otherwise
    """
    if preference not in ["daily", "weekly"]:
        return False
    
    try:
        user = User.get_by_id(int(user_id))
        setattr(user, preference, value)
        user.save()
        return True
    except DoesNotExist:
        print(f"User {user_id} not found when setting preference")
        return False
    except Exception as e:
        print(f"Error setting preference for user {user_id}: {e}")
        return False


def get_user_preference(user_id, preference):
    """Get a user's preference (daily or weekly reminders).
    
    Args:
        user_id: Discord user ID (int or str)
        preference: Either "daily" or "weekly"
        
    Returns:
        Boolean value of the preference, or False if user not found
    """
    try:
        user = User.get_by_id(int(user_id))
        return getattr(user, preference, False)
    except DoesNotExist:
        return False
    except Exception as e:
        print(f"Error getting preference for user {user_id}: {e}")
        return False


def remove_user(user_id):
    """Remove a user from the database.
    
    Args:
        user_id: Discord user ID (int or str)
        
    Returns:
        True if user was removed, False otherwise
    """
    try:
        user = User.get_by_id(int(user_id))
        user.delete_instance()
        return True
    except DoesNotExist:
        return False
    except Exception as e:
        print(f"Error removing user {user_id}: {e}")
        return False


def get_all_users():
    """Get all users from the database.
    
    Returns:
        List of User model instances
    """
    try:
        return list(User.select())
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []


def get_users_with_preference(preference):
    """Get all users with a specific preference enabled.
    
    Args:
        preference: Either "daily" or "weekly"
        
    Returns:
        List of User model instances with the preference enabled
    """
    if preference not in ["daily", "weekly"]:
        return []
    
    try:
        query = User.select().where(getattr(User, preference) == True)
        return list(query)
    except Exception as e:
        print(f"Error getting users with preference {preference}: {e}")
        return [] 
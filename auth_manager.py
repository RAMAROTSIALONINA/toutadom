import db_manager

class AuthManager:
    def authenticate_user(self, username, password):
        user_data = db_manager.get_user_by_username(username)
        if user_data:
            user_id, username_db, stored_password_hash, nom, prenom, role = user_data
            if db_manager.verify_password_bcrypt(password, stored_password_hash):
                return user_id, role, nom, prenom, username_db
        return None, None, None, None, None

import mysql.connector
from mysql.connector import Error
import bcrypt
from datetime import datetime, date, timedelta # Importez timedelta pour les calculs de dates
import os # Pour les variables d'environnement, amélioration de la sécurité

# --- Configuration de la base de données ---
# Il est fortement recommandé de ne pas stocker les identifiants sensibles directement dans le code.
# Utilisez des variables d'environnement pour la production.
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'), # Utilisez votre utilisateur MySQL
    'password': os.environ.get('DB_PASSWORD', ''), # Utilisez votre mot de passe MySQL
    'database': os.environ.get('DB_NAME', 'gestion_vehicules_db')
}

# --- Utilisateurs par défaut pour l'initialisation de la base de données ---
# Ces utilisateurs seront créés si la base de données est vide ou s'ils n'existent pas.
# Les mots de passe seront hachés avant d'être stockés.
DEFAULT_USERS = [
    ("admin", "admin123", "Sys", "Admin", "admin"),
    ("responsable", "resppass", "Logistique", "Responsable", "responsable"),
    ("chauffeur", "chaufpass", "Principal", "Chauffeur", "chauffeur")
]

# --- Fonctions utilitaires de la base de données ---
def create_connection():
    """
    Crée et retourne une connexion à la base de données.
    Affiche un message d'erreur si la connexion échoue.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"ERREUR CRITIQUE: Impossible de se connecter à la base de données MySQL: {e}")
        return None

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """
    Exécute une requête SQL et retourne les résultats si nécessaire.
    Gère la connexion, l'exécution et la fermeture du curseur et de la connexion.
    Retourne (True, résultats) en cas de succès, (False, message_erreur) en cas d'échec.
    """
    conn = create_connection()
    if conn is None:
        return False, "Échec de la connexion à la base de données."

    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())

        if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
            conn.commit()
            return True, "Opération réussie."
        elif fetch_one:
            result = cursor.fetchone()
            return True, result
        elif fetch_all:
            result = cursor.fetchall()
            return True, result
        else: # Pour les requêtes DDL (CREATE TABLE, etc.) ou SELECT sans fetch_one/all explicite
            conn.commit() # S'assurer que les DDL sont commises
            return True, "Requête exécutée avec succès."
    except Error as e:
        conn.rollback() # Annuler la transaction en cas d'erreur
        print(f"Erreur d'exécution de la requête '{query}': {e}")
        return False, f"Erreur d'exécution de la requête: {e}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- Fonctions d'initialisation de la base de données ---
def initialize_database():
    """
    Initialise la base de données et crée les tables si elles n'existent pas.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    print("Vérification et initialisation de la base de données...")
    conn = None
    cursor = None
    try:
        # Tenter de se connecter sans spécifier la base de données pour la créer si elle n'existe pas
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()

        # Créer la base de données si elle n'existe pas
        create_db_query = f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        success, msg = execute_query(create_db_query) 
        if not success:
            return False, f"Échec de la création de la base de données: {msg}"
        
        # Reconnecter à la base de données nouvellement créée ou existante pour les opérations de table
        # Il est important de fermer et rouvrir la connexion pour s'assurer que la base de données est bien sélectionnée.
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("Base de données MySQL initialisée avec succès ou déjà existante.")

        # Définitions des tables avec encodage UTF-8 et gestion des clés étrangères
        table_definitions = {
            "users": """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        nom VARCHAR(100) NOT NULL,
        prenom VARCHAR(100) NOT NULL,
        role ENUM('chauffeur', 'responsable', 'admin') NOT NULL,
        must_change_password TINYINT(1) DEFAULT 0
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
""",
'vehicles': """
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    immatriculation VARCHAR(50) UNIQUE NOT NULL,
                    marque VARCHAR(100) NOT NULL,
                    modele VARCHAR(100) NOT NULL,
                    kilometrage_actuel INT DEFAULT 0,
                    date_acquisition DATE,
                    consommation_theorique DECIMAL(5,2),
                    type_vehicule ENUM('voiture', 'moto') NOT NULL,
                    annee_mise_en_circulation INT,
                    date_assurance DATE,
                    date_visite_technique DATE,
                    date_carte_rose DATE,
                    statut ENUM('Disponible', 'En service', 'En maintenance', 'Hors service') DEFAULT 'Disponible',
                    date_derniere_maintenance DATE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """,
            "attributions": """
                CREATE TABLE IF NOT EXISTS attributions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    vehicle_id INT NOT NULL,
                    date_debut DATE NOT NULL,
                    date_fin_prevue DATE, 
                    date_fin_reelle DATE, 
                    kilometrage_depart INT NOT NULL,
                    kilometrage_retour INT,
                    etat_initial_carburant DECIMAL(5,2), 
                    etat_final_carburant DECIMAL(5,2), 
                    notes TEXT,
                    statut ENUM('en cours', 'terminee') DEFAULT 'en cours' NOT NULL, 
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """,
            "maintenances": """
                CREATE TABLE IF NOT EXISTS maintenances (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    vehicle_id INT NOT NULL,
                    type_maintenance VARCHAR(100) NOT NULL,
                    date_maintenance DATE NOT NULL,
                    cout DECIMAL(10, 2),
                    notes TEXT,
                    statut ENUM('Planifiée', 'En Cours', 'Terminée', 'Annulée') DEFAULT 'Planifiée',
                    kilometrage_maintenance INT,
                    date_prochain_entretien DATE,
                    kilometrage_prochain_entretien INT,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """,
            "fuel_entries": """
                CREATE TABLE IF NOT EXISTS fuel_entries (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    vehicle_id INT NOT NULL,
                    date_plein DATE NOT NULL,
                    type_carburant VARCHAR(50) NOT NULL, 
                    quantite_litres DECIMAL(8, 2) NOT NULL,
                    prix_total DECIMAL(10, 2) NOT NULL,
                    kilometrage_depart INT, 
                    kilometrage_releve INT NOT NULL,
                    lieu VARCHAR(255), 
                    notes TEXT, 
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """,
            "incident_reports": """
                CREATE TABLE IF NOT EXISTS incident_reports (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    vehicle_id INT NOT NULL,
                    date_incident DATE NOT NULL,
                    type_probleme VARCHAR(100) NOT NULL,
                    description TEXT,
                    gravite ENUM('Mineure', 'Modérée', 'Majeure', 'Critique') NOT NULL, 
                    kilometrage_incident INT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """,
            "vehicle_inspections": """
                CREATE TABLE IF NOT EXISTS vehicle_inspections (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    vehicle_id INT NOT NULL,
                    date_inspection DATE NOT NULL,
                    etat_general VARCHAR(255),
                    niveau_carburant DECIMAL(5,2),
                    observations TEXT,
                    niveau_huile_ok BOOLEAN,
                    liquide_refroidissement_ok BOOLEAN,
                    feux_ok BOOLEAN,
                    clignotants_ok BOOLEAN,
                    pneus_ok BOOLEAN,
                    carrosserie_ok BOOLEAN,
                    kilometrage INT, -- Ajout de la colonne kilometrage
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """,
            "attendance": """
                CREATE TABLE IF NOT EXISTS attendance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    qr_code_value VARCHAR(255) NOT NULL,
                    type ENUM('entree', 'sortie') NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """
        }

        for table_name, create_sql in table_definitions.items():
            print(f"Création de la table {table_name}...")
            # Exécuter la requête CREATE TABLE
            cursor.execute(create_sql)
            print(f"Table {table_name} créée ou déjà existante.")
        
        conn.commit()
        print("Base de données prête.")
        return True, "Base de données initialisée avec succès."

    except Error as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
        return False, f"Erreur lors de l'initialisation de la base de données: {e}"
    finally:
        if conn and conn.is_connected():
            if cursor:
                cursor.close()
            conn.close()

# --- Fonctions d'authentification et de gestion des utilisateurs ---
def hash_password_bcrypt(password):
    """
    Hache un mot de passe en utilisant bcrypt avec un coût de 12.
    Retourne le hachage encodé en utf-8 ou None en cas d'erreur.
    """
    try:
        # Le coût (cost) de 12 est un bon équilibre entre sécurité et performance
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"Erreur de hachage du mot de passe: {e}")
        return None

def verify_password_bcrypt(plain_password, hashed_password):
    """
    Vérifie si un mot de passe en clair correspond à un hachage bcrypt.
    Retourne True si la correspondance est réussie, False sinon.
    """
    try:
        if not hashed_password:
            print("Erreur: Le hachage stocké est vide ou invalide.")
            return False
        # Assurez-vous que le hachage stocké est une chaîne non vide
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        print("Erreur : Le hachage stocké n'est pas un hachage bcrypt valide ou format incorrect.")
        return False
    except Exception as e:
        print(f"Une erreur inattendue est survenue lors de la vérification du mot de passe: {e}")
        return False

def get_user_by_username(username):
    """
    Récupère un utilisateur par son nom d'utilisateur.
    Retourne les données de l'utilisateur (id, username, password_hash, nom, prenom, role) ou None.
    """
    query = "SELECT id, username, password_hash, nom, prenom, role FROM users WHERE username = %s"
    success, result = execute_query(query, (username,), fetch_one=True)
    return result if success else None

def get_user_by_id(user_id):
    """
    Récupère un utilisateur par son ID.
    Retourne les données de l'utilisateur (id, username, nom, prenom, role) ou None.
    """
    query = "SELECT id, username, nom, prenom, role FROM users WHERE id = %s"
    success, result = execute_query(query, (user_id,), fetch_one=True)
    return result if success else None

# Ancien authenticate_user retiré, sera dans auth_manager.py

def add_new_user_to_db(username, password_hash, nom, prenom, role):
    """
    Ajoute un nouvel utilisateur à la base de données.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    # Vérifier si l'utilisateur existe déjà avant d'essayer de l'ajouter
    if get_user_by_username(username):
        return False, f"L'utilisateur '{username}' existe déjà."
    
    if not password_hash:
        return False, "Erreur: Le hachage du mot de passe a échoué."
    
    query = "INSERT INTO users (username, password_hash, nom, prenom, role) VALUES (%s, %s, %s, %s, %s)"
    params = (username, password_hash, nom, prenom, role)
    success, msg = execute_query(query, params)
    return success, msg

def get_all_users():
    """Récupère tous les utilisateurs et leurs informations de base, y compris le statut de changement de mot de passe."""
    # MODIFICATION ICI : Ajout de 'must_change_password' à la requête SQL
    query = "SELECT id, username, nom, prenom, role, must_change_password FROM users"
    success, results = execute_query(query, fetch_all=True)
    return results if success else []
def get_all_chauffeurs_and_responsables():
    """Récupère tous les utilisateurs ayant le rôle 'chauffeur' ou 'responsable'."""
    query = "SELECT id, username, nom, prenom, role FROM users WHERE role IN ('chauffeur', 'responsable')"
    success, results = execute_query(query, fetch_all=True)
    return results if success else []

def update_user_in_db(user_id, username, password_hash, nom, prenom, role):
    """
    Met à jour un utilisateur existant.
    Si password_hash est fourni, le mot de passe est mis à jour.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    if password_hash:
        query = "UPDATE users SET username = %s, password_hash = %s, nom = %s, prenom = %s, role = %s WHERE id = %s"
        params = (username, password_hash, nom, prenom, role, user_id)
    else:
        query = "UPDATE users SET username = %s, nom = %s, prenom = %s, role = %s WHERE id = %s"
        params = (username, nom, prenom, role, user_id)
    
    success, msg = execute_query(query, params)
    return success, msg

def delete_user_from_db(user_id):
    """
    Supprime un utilisateur de la base de données.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    query = "DELETE FROM users WHERE id = %s"
    success, msg = execute_query(query, (user_id,))
    return success, msg

def add_default_users_if_not_exists():
    """
    Ajoute les utilisateurs par défaut définis dans DEFAULT_USERS si non existants.
    Les mots de passe sont hachés avant l'insertion.
    """
    print("Vérification et ajout des utilisateurs par défaut...")
    for username, plain_password, nom, prenom, role in DEFAULT_USERS:
        # Vérifier si l'utilisateur existe déjà
        success, existing_user = execute_query("SELECT id FROM users WHERE username = %s", (username,), fetch_one=True)
        
        if not success:
            print(f"Erreur lors de la vérification de l'utilisateur '{username}': {existing_user}")
            continue # Passer à l'utilisateur suivant en cas d'erreur de vérification

        if not existing_user:
            # Hacher le mot de passe avant de l'ajouter
            hashed_password = hash_password_bcrypt(plain_password)
            if hashed_password:
                success_add, msg_add = add_new_user_to_db(username, hashed_password, nom, prenom, role)
                print(f"Ajout de l'utilisateur {username}: {msg_add}")
            else:
                print(f"Échec du hachage du mot de passe pour l'utilisateur '{username}'.")
        else:
            print(f"L'utilisateur '{username}' existe déjà.")


# --- Fonctions de gestion des véhicules ---
def add_new_vehicle_to_db(immatriculation, marque, modele, kilometrage_actuel, date_acquisition, consommation_theorique, type_vehicule, annee_mise_en_circulation, date_assurance, date_visite_technique, date_carte_rose):
    """
    Ajoute un nouveau véhicule à la base de données.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    query = """
        INSERT INTO vehicles (immatriculation, marque, modele, kilometrage_actuel, date_acquisition, consommation_theorique, type_vehicule, annee_mise_en_circulation, date_assurance, date_visite_technique, date_carte_rose)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (immatriculation, marque, modele, kilometrage_actuel, date_acquisition, consommation_theorique, type_vehicule, annee_mise_en_circulation, date_assurance, date_visite_technique, date_carte_rose)
    success, msg = execute_query(query, params)
    return success, msg

def get_all_vehicles():
    """Récupère tous les véhicules de la base de données."""
    query = "SELECT id, immatriculation, marque, modele, kilometrage_actuel, date_acquisition, consommation_theorique, type_vehicule, annee_mise_en_circulation, date_assurance, date_visite_technique, date_carte_rose, statut FROM vehicles"
    success, results = execute_query(query, fetch_all=True)
    return results if success else []

def get_active_vehicles():
    """Récupère les véhicules qui ne sont pas 'Hors service' ou 'En maintenance'."""
    query = "SELECT id, immatriculation FROM vehicles WHERE statut IN ('Disponible', 'En service')"
    success, results = execute_query(query, fetch_all=True)
    return results if success else []

def get_vehicle_by_immatriculation(immatriculation):
    """Récupère un véhicule par son immatriculation."""
    query = "SELECT id, immatriculation, marque, modele, annee_mise_en_circulation, kilometrage_actuel, consommation_theorique, statut, date_acquisition, date_assurance, date_visite_technique, date_carte_rose, date_derniere_maintenance, type_vehicule FROM vehicles WHERE immatriculation = %s"
    success, result = execute_query(query, (immatriculation,), fetch_one=True)
    return result if success else None

def get_vehicle_by_id(vehicle_id):
    """Récupère un véhicule par son ID."""
    query = "SELECT id, immatriculation, marque, modele, kilometrage_actuel, date_acquisition, consommation_theorique, type_vehicule, annee_mise_en_circulation, date_assurance, date_visite_technique, date_carte_rose, statut FROM vehicles WHERE id = %s"
    success, result = execute_query(query, (vehicle_id,), fetch_one=True)
    return result if success else None

def update_vehicle_in_db(vehicle_id, immatriculation, marque, modele, kilometrage_actuel, date_acquisition, consommation_theorique, type_vehicule, annee_mise_en_circulation, date_assurance, date_visite_technique, date_carte_rose, statut):
    """
    Met à jour un véhicule existant dans la base de données.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    query = """
        UPDATE vehicles SET
        immatriculation = %s, marque = %s, modele = %s, kilometrage_actuel = %s, date_acquisition = %s,
        consommation_theorique = %s, type_vehicule = %s, annee_mise_en_circulation = %s,
        date_assurance = %s, date_visite_technique = %s, date_carte_rose = %s, statut = %s
        WHERE id = %s
    """
    params = (immatriculation, marque, modele, kilometrage_actuel, date_acquisition, consommation_theorique, type_vehicule, annee_mise_en_circulation, date_assurance, date_visite_technique, date_carte_rose, statut, vehicle_id)
    success, msg = execute_query(query, params)
    return success, msg

def update_vehicle_status_and_km(vehicle_id, new_status, new_kilometrage=None):
    """
    Met à jour le statut et/ou le kilométrage d'un véhicule.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    if new_kilometrage is not None:
        query = "UPDATE vehicles SET statut = %s, kilometrage_actuel = %s WHERE id = %s"
        params = (new_status, new_kilometrage, vehicle_id)
    else:
        query = "UPDATE vehicles SET statut = %s WHERE id = %s"
        params = (new_status, vehicle_id)
    
    success, msg = execute_query(query, params)
    return success, msg

def update_vehicle_km(vehicle_id, new_kilometrage):
    """
    Met à jour le kilométrage actuel d'un véhicule.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    query = "UPDATE vehicles SET kilometrage_actuel = %s WHERE id = %s"
    params = (new_kilometrage, vehicle_id)
    success, msg = execute_query(query, params)
    return success, msg

def delete_vehicle_from_db(vehicle_id):
    """
    Supprime un véhicule de la base de données.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    query = "DELETE FROM vehicles WHERE id = %s"
    success, msg = execute_query(query, (vehicle_id,))
    return success, msg

def get_vehicle_document_expiry_dates(vehicle_id):
    """
    Récupère les dates d'expiration des documents (assurance, visite technique, carte rose)
    pour un véhicule donné par son ID.
    Retourne un tuple (date_assurance, date_visite_technique, date_carte_rose, immatriculation) ou None.
    """
    query = "SELECT date_assurance, date_visite_technique, date_carte_rose, immatriculation FROM vehicles WHERE id = %s"
    success, result = execute_query(query, (vehicle_id,), fetch_one=True)
    return result if success else None

# --- Fonctions de gestion des attributions ---
def add_attribution_to_db(user_id, vehicle_id, date_debut, date_fin_prevue, kilometrage_depart, etat_initial_carburant, notes=None):
    """
    Ajoute une nouvelle attribution à la base de données et met à jour le statut du véhicule.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    # Vérifier si le véhicule est déjà attribué et en cours
    check_query = "SELECT id FROM attributions WHERE vehicle_id = %s AND statut = 'en cours'"
    success_check, existing_attribution = execute_query(check_query, (vehicle_id,), fetch_one=True)
    
    if not success_check:
        return False, "Erreur lors de la vérification de l'attribution du véhicule."
    if existing_attribution:
        return False, "Ce véhicule est déjà attribué et en service."

    conn = create_connection()
    if conn is None:
        return False, "Échec de la connexion à la base de données."
    try:
        cursor = conn.cursor()
        
        # 1. Insérer l'attribution avec les nouveaux champs
        # Notes: date_fin_reelle est NULL initialement, etat_final_carburant est NULL initialement
        insert_attr_query = """
            INSERT INTO attributions (user_id, vehicle_id, date_debut, date_fin_prevue, kilometrage_depart, etat_initial_carburant, notes, statut) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'en cours')
        """
        insert_attr_params = (user_id, vehicle_id, date_debut, date_fin_prevue, kilometrage_depart, etat_initial_carburant, notes)
        cursor.execute(insert_attr_query, insert_attr_params)
        
        # 2. Mettre à jour le statut du véhicule et son kilométrage actuel
        update_vehicle_query = "UPDATE vehicles SET statut = 'En service', kilometrage_actuel = %s WHERE id = %s"
        cursor.execute(update_vehicle_query, (kilometrage_depart, vehicle_id))
        
        conn.commit()
        return True, "Attribution ajoutée et statut du véhicule mis à jour avec succès."
    except Error as e:
        conn.rollback()
        print(f"Erreur lors de l'ajout de l'attribution: {e}")
        return False, f"Échec de l'ajout de l'attribution: {e}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Dans votre fichier db_manager.py

def get_all_attributions():
    """
    Récupère toutes les attributions avec les noms du chauffeur et l'immatriculation du véhicule.
    Retourne une liste de tuples (id, chauffeur_display_name, immatriculation, date_debut,
    date_fin_prevue, date_fin_reelle, kilometrage_depart, kilometrage_retour,
    etat_initial_carburant, etat_final_carburant, statut, notes, vehicle_id).
    
    L'ordre de retour DOIT correspondre aux colonnes du Treeview et aux accès par index.
    """
    query = """
        SELECT
            a.id,
            CONCAT(u.prenom, ' ', u.nom, ' (', u.username, ')'), -- Utilisez CONCAT() pour MySQL
            v.immatriculation,
            a.date_debut,
            a.date_fin_prevue,
            a.date_fin_reelle,
            a.kilometrage_depart,
            a.kilometrage_retour,
            a.etat_initial_carburant,
            a.etat_final_carburant,
            a.statut,
            a.notes,
            a.vehicle_id
        FROM attributions AS a
        JOIN users AS u ON a.user_id = u.id
        JOIN vehicles AS v ON a.vehicle_id = v.id
        ORDER BY a.date_debut DESC
    """
    success, results = execute_query(query, fetch_all=True)
    print(f"DEBUG DB: get_all_attributions - Success: {success}, Results count: {len(results) if results else 0}")
    if not success:
        print(f"DEBUG DB: get_all_attributions - Error: {results}")
    return results if success else []

def get_attribution_by_id(attribution_id):
    """
    Récupère une attribution par son ID.
    Retourne les données de l'attribution ou None.
    (id, user_id, vehicle_id, date_debut, date_fin_prevue, date_fin_reelle,
    kilometrage_depart, kilometrage_retour, etat_initial_carburant, etat_final_carburant, notes, statut)
    """
    query = """
        SELECT 
            id, user_id, vehicle_id, date_debut, date_fin_prevue, date_fin_reelle,
            kilometrage_depart, kilometrage_retour, etat_initial_carburant, etat_final_carburant, notes, statut
        FROM attributions 
        WHERE id = %s
    """
    success, result = execute_query(query, (attribution_id,), fetch_one=True)
    return result if success else None

def get_attribution_by_chauffeur_id(user_id):
    """
    Récupère les attributions pour un chauffeur donné.
    Retourne une liste de tuples (id, user_id, vehicle_id, date_debut, date_fin_prevue, date_fin_reelle,
    kilometrage_depart, kilometrage_retour, etat_initial_carburant, etat_final_carburant, notes, statut, immatriculation).
    """
    query = """
        SELECT 
            a.id, a.user_id, a.vehicle_id, a.date_debut, a.date_fin_prevue, a.date_fin_reelle,
            a.kilometrage_depart, a.kilometrage_retour, a.etat_initial_carburant, a.etat_final_carburant, a.notes, a.statut,
            v.immatriculation
        FROM attributions AS a
        JOIN vehicles AS v ON a.vehicle_id = v.id
        WHERE a.user_id = %s
        ORDER BY a.date_debut DESC
    """
    success, results = execute_query(query, (user_id,), fetch_all=True)
    return results if success else []

def update_attribution_in_db(attribution_id, user_id, vehicle_id, date_debut, date_fin_prevue, date_fin_reelle, kilometrage_depart, kilometrage_retour, etat_initial_carburant, etat_final_carburant, notes, statut):
    """
    Met à jour une attribution existante dans la base de données.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    conn = create_connection()
    if conn is None:
        return False, "Échec de la connexion à la base de données."
    try:
        cursor = conn.cursor()

        # Mettre à jour l'attribution
        update_attr_query = """
            UPDATE attributions SET
            user_id = %s, vehicle_id = %s, date_debut = %s, date_fin_prevue = %s, date_fin_reelle = %s,
            kilometrage_depart = %s, kilometrage_retour = %s, etat_initial_carburant = %s,
            etat_final_carburant = %s, notes = %s, statut = %s
            WHERE id = %s
        """
        update_attr_params = (user_id, vehicle_id, date_debut, date_fin_prevue, date_fin_reelle,
                              kilometrage_depart, kilometrage_retour, etat_initial_carburant,
                              etat_final_carburant, notes, statut, attribution_id)
        cursor.execute(update_attr_query, update_attr_params)

        # Si l'attribution est terminée, mettre à jour le statut du véhicule à 'Disponible' et son kilométrage
        if statut == 'terminee':
            update_vehicle_query = "UPDATE vehicles SET statut = 'Disponible', kilometrage_actuel = %s WHERE id = %s"
            cursor.execute(update_vehicle_query, (kilometrage_retour, vehicle_id))
        elif statut == 'en cours':
            # Si elle repasse "en cours", remettre le véhicule "En service"
            update_vehicle_query = "UPDATE vehicles SET statut = 'En service', kilometrage_actuel = %s WHERE id = %s"
            cursor.execute(update_vehicle_query, (kilometrage_depart, vehicle_id))
        
        conn.commit()
        return True, "Attribution mise à jour avec succès."
    except Error as e:
        conn.rollback()
        print(f"Erreur lors de la mise à jour de l'attribution: {e}")
        return False, f"Échec de la mise à jour de l'attribution: {e}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def end_attribution_in_db(attribution_id, date_fin_reelle, kilometrage_retour, etat_final_carburant, notes):
    """
    Termine une attribution en mettant à jour sa date de fin réelle, le km de retour,
    l'état final du carburant, les notes et le statut de l'attribution et du véhicule.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    conn = create_connection()
    if conn is None:
        return False, "Échec de la connexion à la base de données."

    try:
        cursor = conn.cursor()

        # 1. Récupérer les détails de l'attribution pour obtenir le vehicle_id, kilometrage_depart et statut
        get_attr_query = "SELECT vehicle_id, kilometrage_depart, statut FROM attributions WHERE id = %s"
        cursor.execute(get_attr_query, (attribution_id,))
        attribution_details = cursor.fetchone()
        
        if not attribution_details:
            return False, "Attribution introuvable."
        
        vehicle_id = attribution_details[0]
        kilometrage_depart = attribution_details[1]
        current_attribution_status = attribution_details[2]

        if current_attribution_status == 'terminee':
            return False, "Cette attribution est déjà terminée."

        if kilometrage_retour is not None and kilometrage_retour < kilometrage_depart:
            return False, "Le kilométrage de retour ne peut pas être inférieur au kilométrage de départ."

        # 2. Mettre à jour l'attribution
        update_attr_query = """
            UPDATE attributions 
            SET date_fin_reelle = %s, kilometrage_retour = %s, etat_final_carburant = %s, notes = %s, statut = 'terminee' 
            WHERE id = %s
        """
        update_attr_params = (date_fin_reelle, kilometrage_retour, etat_final_carburant, notes, attribution_id)
        cursor.execute(update_attr_query, update_attr_params)
        
        # 3. Mettre à jour le statut du véhicule et son kilométrage actuel
        # Le statut devient 'Disponible' car l'attribution se termine.
        update_vehicle_query = "UPDATE vehicles SET statut = 'Disponible', kilometrage_actuel = %s WHERE id = %s"
        cursor.execute(update_vehicle_query, (kilometrage_retour, vehicle_id))
        
        conn.commit()
        return True, "Attribution terminée et statut du véhicule mis à jour avec succès."
    except Error as e:
        conn.rollback()
        print(f"Erreur lors de la fin de l'attribution: {e}")
        return False, f"Échec de la fin de l'attribution: {e}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def delete_attribution_from_db(attribution_id):
    """
    Supprime une attribution de la base de données.
    Réévalue le statut du véhicule si l'attribution était active.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    conn = create_connection()
    if conn is None:
        return False, "Échec de la connexion à la base de données."
    try:
        cursor = conn.cursor()
        # 1. Récupérer l'ID du véhicule lié et le statut de l'attribution
        cursor.execute("SELECT vehicle_id, statut FROM attributions WHERE id = %s", (attribution_id,))
        result = cursor.fetchone()
        
        # 2. Supprimer l'attribution
        delete_query = "DELETE FROM attributions WHERE id = %s"
        cursor.execute(delete_query, (attribution_id,))

        if result:
            vehicle_id, status = result
            # Si l'attribution n'était pas terminée, remettre le véhicule en 'Disponible'
            if status == 'en cours': # Check against 'en cours' status
                # Vérifier s'il n'y a pas d'autres attributions actives pour ce véhicule
                check_other_attr_query = "SELECT id FROM attributions WHERE vehicle_id = %s AND statut = 'en cours'"
                cursor.execute(check_other_attr_query, (vehicle_id,))
                if not cursor.fetchone(): # Si aucune autre attribution en cours
                    update_vehicle_query = "UPDATE vehicles SET statut = 'Disponible' WHERE id = %s"
                    cursor.execute(update_vehicle_query, (vehicle_id,))
        
        conn.commit()
        return True, "Attribution supprimée avec succès."
    except Error as e:
        conn.rollback()
        print(f"Erreur lors de la suppression de l'attribution: {e}")
        return False, f"Échec de la suppression de l'attribution: {e}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- Fonctions de gestion des maintenances ---
def add_maintenance_to_db(vehicle_id, type_maintenance, date_maintenance, cout, notes=None, statut='Planifiée', kilometrage_maintenance=None, date_prochain_entretien=None, kilometrage_prochain_entretien=None):
    """
    Ajoute une nouvelle entrée de maintenance à la base de données.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    conn = create_connection()
    if conn is None:
        return False, "Échec de la connexion à la base de données."
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO maintenances (vehicle_id, type_maintenance, date_maintenance, cout, notes, statut, kilometrage_maintenance, date_prochain_entretien, kilometrage_prochain_entretien)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (vehicle_id, type_maintenance, date_maintenance, cout, notes, statut, kilometrage_maintenance, date_prochain_entretien, kilometrage_prochain_entretien)
        cursor.execute(query, params)

        # Mettre à jour le statut du véhicule si la maintenance est "En Cours"
        if statut == 'En Cours':
            update_vehicle_status_query = "UPDATE vehicles SET statut = 'En maintenance' WHERE id = %s"
            cursor.execute(update_vehicle_status_query, (vehicle_id,))
        elif statut == 'Terminée':
            # Si la maintenance est terminée, le véhicule redevient "Disponible"
            update_vehicle_status_query = "UPDATE vehicles SET statut = 'Disponible', date_derniere_maintenance = %s WHERE id = %s"
            cursor.execute(update_vehicle_status_query, (date_maintenance, vehicle_id))
        
        conn.commit()
        return True, "Maintenance ajoutée avec succès."
    except Error as e:
        conn.rollback()
        print(f"Erreur lors de l'ajout de la maintenance: {e}")
        return False, f"Échec de l'ajout de la maintenance: {e}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_all_maintenances():
    """
    Récupère toutes les maintenances avec l'immatriculation du véhicule.
    Retourne une liste de tuples (id, immatriculation, type_maintenance, date_maintenance, cout, notes, statut, kilometrage_maintenance, date_prochain_entretien, kilometrage_prochain_entretien, vehicle_id).
    """
    query = """
        SELECT 
            m.id, 
            v.immatriculation, 
            m.type_maintenance, 
            m.date_maintenance, 
            m.cout, 
            m.notes, 
            m.statut, 
            m.kilometrage_maintenance, 
            m.date_prochain_entretien, 
            m.kilometrage_prochain_entretien,
            m.vehicle_id
        FROM maintenances AS m
        JOIN vehicles AS v ON m.vehicle_id = v.id
        ORDER BY m.date_maintenance DESC
    """
    success, results = execute_query(query, fetch_all=True)
    return results if success else []

def get_maintenance_by_id(maintenance_id):
    """
    Récupère une maintenance par son ID.
    Retourne les données de la maintenance ou None.
    """
    query = "SELECT id, vehicle_id, type_maintenance, date_maintenance, cout, notes, statut, kilometrage_maintenance, date_prochain_entretien, kilometrage_prochain_entretien FROM maintenances WHERE id = %s"
    success, result = execute_query(query, (maintenance_id,), fetch_one=True)
    return result if success else None

def update_maintenance_in_db(maintenance_id, vehicle_id, type_maintenance, 
                           date_maintenance, cout, notes, statut,
                           kilometrage_maintenance, date_prochain_entretien,
                           kilometrage_prochain_entretien):
    
    """
    Met à jour une entrée de maintenance existante.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    conn = create_connection()
    if conn is None:
        return False, "Échec de la connexion à la base de données."
    try:
        cursor = conn.cursor()
        query = """
            UPDATE maintenances SET
            vehicle_id = %s, type_maintenance = %s, date_maintenance = %s, cout = %s, notes = %s, statut = %s,
            kilometrage_maintenance = %s, date_prochain_entretien = %s, kilometrage_prochain_entretien = %s
            WHERE id = %s
        """
        params = (vehicle_id, type_maintenance, date_maintenance, cout, notes, statut, kilometrage_maintenance, date_prochain_entretien, kilometrage_prochain_entretien, maintenance_id)
        cursor.execute(query, params)

        # Mettre à jour le statut du véhicule en fonction du statut de la maintenance
        if statut == 'En Cours':
            update_vehicle_status_query = "UPDATE vehicles SET statut = 'En maintenance' WHERE id = %s"
            cursor.execute(update_vehicle_status_query, (vehicle_id,))
        elif statut == 'Terminée':
            update_vehicle_status_query = "UPDATE vehicles SET statut = 'Disponible', date_derniere_maintenance = %s WHERE id = %s"
            cursor.execute(update_vehicle_status_query, (date_maintenance, vehicle_id))
        else: # Planifiée, Annulée - le véhicule redevient disponible s'il était en maintenance
            # Récupérer le statut actuel du véhicule pour éviter de le changer si ce n'est pas nécessaire
            success_veh_stat, current_veh_status = execute_query("SELECT statut FROM vehicles WHERE id = %s", (vehicle_id,), fetch_one=True)
            if success_veh_stat and current_veh_status and current_veh_status[0] == 'En maintenance':
                update_vehicle_status_query = "UPDATE vehicles SET statut = 'Disponible' WHERE id = %s"
                cursor.execute(update_vehicle_status_query, (vehicle_id,))

        conn.commit()
        return True, "Maintenance mise à jour avec succès."
    except Error as e:
        conn.rollback()
        print(f"Erreur lors de la mise à jour de la maintenance: {e}")
        return False, f"Échec de la mise à jour de la maintenance: {e}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def delete_maintenance_from_db(maintenance_id):
    """
    Supprime une entrée de maintenance de la base de données.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    query = "DELETE FROM maintenances WHERE id = %s"
    success, msg = execute_query(query, (maintenance_id,))
    return success, msg

# --- Fonctions de gestion des entrées de carburant ---
def add_fuel_entry_to_db(user_id, vehicle_id, date_plein, type_carburant, quantite_litres, prix_total, kilometrage_depart, kilometrage_releve, lieu, notes):
    """
    Ajoute une nouvelle entrée de carburant à la base de données.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    query = """
        INSERT INTO fuel_entries (user_id, vehicle_id, date_plein, type_carburant, quantite_litres, prix_total, kilometrage_depart, kilometrage_releve, lieu, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (user_id, vehicle_id, date_plein, type_carburant, quantite_litres, prix_total, kilometrage_depart, kilometrage_releve, lieu, notes)
    success, msg = execute_query(query, params)
    return success, msg

def get_all_fuel_entries():
    """
    Récupère toutes les entrées de carburant avec les noms de l'utilisateur et l'immatriculation du véhicule.
    Retourne une liste de tuples (fe.id, u.nom, u.prenom, v.immatriculation, fe.date_plein, fe.type_carburant, fe.quantite_litres, fe.prix_total, fe.kilometrage_depart, fe.kilometrage_releve, fe.lieu, fe.notes, fe.user_id, fe.vehicle_id).
    """
    query = """
        SELECT 
            fe.id, 
            u.nom, 
            u.prenom, 
            v.immatriculation, 
            fe.date_plein, 
            fe.type_carburant, 
            fe.quantite_litres, 
            fe.prix_total, 
            fe.kilometrage_depart, 
            fe.kilometrage_releve, 
            fe.lieu, 
            fe.notes,
            fe.user_id,
            fe.vehicle_id
        FROM fuel_entries AS fe
        JOIN users AS u ON fe.user_id = u.id
        JOIN vehicles AS v ON fe.vehicle_id = v.id
        ORDER BY fe.date_plein DESC
    """
    success, results = execute_query(query, fetch_all=True)
    return results if success else []

def get_fuel_entries_by_user(user_id):
    """
    Récupère toutes les entrées de carburant pour un utilisateur donné, avec les noms de l'utilisateur et l'immatriculation du véhicule.
    Retourne une liste de tuples (fe.id, u.nom, u.prenom, v.immatriculation, fe.date_plein, fe.type_carburant, fe.quantite_litres, fe.prix_total, fe.kilometrage_depart, fe.kilometrage_releve, fe.lieu, fe.notes, fe.user_id, fe.vehicle_id).
    """
    query = """
        SELECT 
            fe.id, 
            u.nom, 
            u.prenom, 
            v.immatriculation, 
            fe.date_plein, 
            fe.type_carburant, 
            fe.quantite_litres, 
            fe.prix_total, 
            fe.kilometrage_depart, 
            fe.kilometrage_releve, 
            fe.lieu, 
            fe.notes,
            fe.user_id,
            fe.vehicle_id
        FROM fuel_entries AS fe
        JOIN users AS u ON fe.user_id = u.id
        JOIN vehicles AS v ON fe.vehicle_id = v.id
        WHERE fe.user_id = %s
        ORDER BY fe.date_plein DESC
    """
    success, results = execute_query(query, (user_id,), fetch_all=True)
    return results if success else []


def get_fuel_entry_by_id(fuel_entry_id):
    """
    Récupère une entrée de carburant par son ID.
    Retourne les données de l'entrée de carburant ou None.
    """
    query = "SELECT id, user_id, vehicle_id, date_plein, type_carburant, quantite_litres, prix_total, kilometrage_depart, kilometrage_releve, lieu, notes FROM fuel_entries WHERE id = %s"
    success, result = execute_query(query, (fuel_entry_id,), fetch_one=True)
    return result if success else None

def update_fuel_entry_in_db(fuel_entry_id, user_id, vehicle_id, date_plein, type_carburant, quantite_litres, prix_total, kilometrage_depart, kilometrage_releve, lieu, notes):
    """
    Met à jour une entrée de carburant existante.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    query = """
        UPDATE fuel_entries SET
        user_id = %s, vehicle_id = %s, date_plein = %s, type_carburant = %s, quantite_litres = %s, 
        prix_total = %s, kilometrage_depart = %s, kilometrage_releve = %s, lieu = %s, notes = %s
        WHERE id = %s
    """
    params = (user_id, vehicle_id, date_plein, type_carburant, quantite_litres, prix_total, kilometrage_depart, kilometrage_releve, lieu, notes, fuel_entry_id)
    success, msg = execute_query(query, params)
    return success, msg

def delete_fuel_entry_from_db(fuel_entry_id):
    """
    Supprime une entrée de carburant de la base de données.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    query = "DELETE FROM fuel_entries WHERE id = %s"
    success, msg = execute_query(query, (fuel_entry_id,))
    return success, msg

# --- Fonctions de gestion des rapports d'incident ---
def add_incident_report_to_db(user_id, vehicle_id, date_incident, type_probleme, description, gravite, kilometrage_incident=None):
    """
    Ajoute un nouveau rapport d'incident à la base de données.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    query = """
        INSERT INTO incident_reports (user_id, vehicle_id, date_incident, type_probleme, description, gravite, kilometrage_incident)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (user_id, vehicle_id, date_incident, type_probleme, description, gravite, kilometrage_incident)
    success, msg = execute_query(query, params)
    return success, msg

def get_all_incident_reports():
    """
    Récupère tous les rapports d'incident.
    Retourne une liste de tuples (id, user_id, vehicle_id, date_incident, type_probleme, description, gravite, kilometrage_incident).
    """
    query = "SELECT id, user_id, vehicle_id, date_incident, type_probleme, description, gravite, kilometrage_incident FROM incident_reports ORDER BY date_incident DESC"
    success, results = execute_query(query, fetch_all=True)
    return results if success else []

def get_incident_reports_by_user(user_id):
    """
    Récupère tous les rapports d'incident pour un utilisateur donné.
    Retourne une liste de tuples (id, user_id, vehicle_id, date_incident, type_probleme, description, gravite, kilometrage_incident).
    """
    query = "SELECT id, user_id, vehicle_id, date_incident, type_probleme, description, gravite, kilometrage_incident FROM incident_reports WHERE user_id = %s ORDER BY date_incident DESC"
    success, results = execute_query(query, (user_id,), fetch_all=True)
    return results if success else []

def get_incident_report_by_id(incident_id):
    """
    Récupère un rapport d'incident par son ID.
    Retourne les données du rapport ou None.
    """
    query = "SELECT id, user_id, vehicle_id, date_incident, type_probleme, description, gravite, kilometrage_incident FROM incident_reports WHERE id = %s"
    success, result = execute_query(query, (incident_id,), fetch_one=True)
    return result if success else None

def update_incident_report_in_db(incident_id, user_id, vehicle_id, date_incident, type_probleme, description, gravite, kilometrage_incident=None):
    """
    Met à jour un rapport d'incident existant.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    query = """
        UPDATE incident_reports SET
        user_id = %s, vehicle_id = %s, date_incident = %s, type_probleme = %s, description = %s,
        gravite = %s, kilometrage_incident = %s
        WHERE id = %s
    """
    params = (user_id, vehicle_id, date_incident, type_probleme, description, gravite, kilometrage_incident, incident_id)
    success, msg = execute_query(query, params)
    return success, msg

def delete_incident_report_from_db(incident_id):
    """
    Supprime un rapport d'incident de la base de données.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    query = "DELETE FROM incident_reports WHERE id = %s"
    success, msg = execute_query(query, (incident_id,))
    return success, msg

# --- Fonctions de gestion des inspections de véhicule ---
def add_vehicle_inspection_report(user_id, vehicle_id, date_inspection, etat_general, niveau_carburant, observations, niveau_huile_ok, liquide_refroidissement_ok, feux_ok, clignotants_ok, pneus_ok, carrosserie_ok, kilometrage):
    """
    Ajoute un nouveau rapport d'inspection de véhicule à la base de données.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    query = """
        INSERT INTO vehicle_inspections (user_id, vehicle_id, date_inspection, etat_general, niveau_carburant, observations, niveau_huile_ok, liquide_refroidissement_ok, feux_ok, clignotants_ok, pneus_ok, carrosserie_ok, kilometrage)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (user_id, vehicle_id, date_inspection, etat_general, niveau_carburant, observations, niveau_huile_ok, liquide_refroidissement_ok, feux_ok, clignotants_ok, pneus_ok, carrosserie_ok, kilometrage)
    success, msg = execute_query(query, params)
    return success, msg

def get_all_vehicle_inspection_reports():
    """
    Récupère tous les rapports d'inspection de véhicules.
    Retourne une liste de tuples.
    """
    query = "SELECT id, user_id, vehicle_id, date_inspection, etat_general, niveau_carburant, observations, niveau_huile_ok, liquide_refroidissement_ok, feux_ok, clignotants_ok, pneus_ok, carrosserie_ok, kilometrage FROM vehicle_inspections ORDER BY date_inspection DESC"
    success, results = execute_query(query, fetch_all=True)
    return results if success else []

def get_vehicle_inspection_reports_by_user(user_id):
    """
    Récupère tous les rapports d'inspection de véhicules pour un utilisateur donné.
    Retourne une liste de tuples.
    """
    query = "SELECT id, user_id, vehicle_id, date_inspection, etat_general, niveau_carburant, observations, niveau_huile_ok, liquide_refroidissement_ok, feux_ok, clignotants_ok, pneus_ok, carrosserie_ok, kilometrage FROM vehicle_inspections WHERE user_id = %s ORDER BY date_inspection DESC"
    success, results = execute_query(query, (user_id,), fetch_all=True)
    return results if success else []

def get_vehicle_inspection_report_by_id(report_id):
    """
    Récupère un rapport d'inspection de véhicule par son ID.
    """
    query = "SELECT id, user_id, vehicle_id, date_inspection, etat_general, niveau_carburant, observations, niveau_huile_ok, liquide_refroidissement_ok, feux_ok, clignotants_ok, pneus_ok, carrosserie_ok, kilometrage FROM vehicle_inspections WHERE id = %s"
    success, result = execute_query(query, (report_id,), fetch_one=True)
    return result if success else None

def update_vehicle_inspection_report(report_id, user_id, vehicle_id, date_inspection, etat_general, niveau_carburant, observations, niveau_huile_ok, liquide_refroidissement_ok, feux_ok, clignotants_ok, pneus_ok, carrosserie_ok, kilometrage):
    """
    Met à jour un rapport d'inspection de véhicule existant.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    query = """
        UPDATE vehicle_inspections SET
        user_id = %s, vehicle_id = %s, date_inspection = %s, etat_general = %s, niveau_carburant = %s, 
        observations = %s, niveau_huile_ok = %s, liquide_refroidissement_ok = %s, feux_ok = %s, 
        clignotants_ok = %s, pneus_ok = %s, carrosserie_ok = %s, kilometrage = %s
        WHERE id = %s
    """
    params = (user_id, vehicle_id, date_inspection, etat_general, niveau_carburant, observations, niveau_huile_ok, liquide_refroidissement_ok, feux_ok, clignotants_ok, pneus_ok, carrosserie_ok, kilometrage, report_id)
    success, msg = execute_query(query, params)
    return success, msg

def delete_vehicle_inspection_report(report_id):
    """
    Supprime un rapport d'inspection de véhicule de la base de données.
    Retourne (True, message) si succès, (False, message_erreur) sinon.
    """
    query = "DELETE FROM vehicle_inspections WHERE id = %s"
    success, msg = execute_query(query, (report_id,))
    return success, msg

# --- Fonctions de gestion de l'assiduité (attendance) ---
def add_attendance_entry(user_id, qr_code_value, type_entry, timestamp=None):
    """
    Ajoute une nouvelle entrée de pointage (entrée/sortie) à la base de données.
    """
    if timestamp is None:
        timestamp = datetime.now()
    query = "INSERT INTO attendance (user_id, qr_code_value, type, timestamp) VALUES (%s, %s, %s, %s)"
    params = (user_id, qr_code_value, type_entry, timestamp)
    success, msg = execute_query(query, params)
    return success, msg

def get_last_attendance_entry_for_user(user_id):
    """
    Récupère la dernière entrée de pointage pour un utilisateur donné.
    Retourne (id, user_id, timestamp, qr_code_value, type) ou None.
    """
    query = "SELECT id, user_id, timestamp, qr_code_value, type FROM attendance WHERE user_id = %s ORDER BY timestamp DESC LIMIT 1"
    success, result = execute_query(query, (user_id,), fetch_one=True)
    return result if success else None

def get_all_attendance_entries():
    """
    Récupère toutes les entrées de pointage avec les noms de l'utilisateur.
    Retourne une liste de tuples (id, user_id, timestamp, qr_code_value, type, nom_utilisateur, prenom_utilisateur).
    """
    query = """
        SELECT 
            a.id, 
            a.user_id, 
            a.timestamp, 
            a.qr_code_value, 
            a.type,
            u.nom,
            u.prenom
        FROM attendance AS a
        JOIN users AS u ON a.user_id = u.id
        ORDER BY a.timestamp DESC
    """
    success, results = execute_query(query, fetch_all=True)
    return results if success else []

def process_qr_code_attendance(user_id, qr_code_value):
    """
    Traite un scan de QR code pour l'assiduité (pointage d'entrée/sortie).
    Détermine si c'est une entrée ou une sortie et enregistre l'événement.
    Retourne (True, message) en cas de succès, (False, message_erreur) sinon.
    """
    last_entry = get_last_attendance_entry_for_user(user_id)
    current_time = datetime.now()
    
    attendance_type = 'entree'
    message = ""

    if last_entry:
        last_type = last_entry[4] # 'entree' ou 'sortie'
        last_timestamp = last_entry[2] # Objet datetime
        
        if last_type == 'entree':
            # Si la dernière était une entrée, la prochaine doit être une sortie
            attendance_type = 'sortie'
            duration = current_time - last_timestamp
            # Formater la durée pour un affichage plus lisible (sans les microsecondes)
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            message = f"Pointage de sortie enregistré."
            message += f" Durée de service: {hours:02d}h {minutes:02d}min {seconds:02d}s."
        else: # last_type == 'sortie' (ou pas d'entrée du tout)
            # Si la dernière était une sortie, la prochaine doit être une entrée
            attendance_type = 'entree'
            message = "Pointage d'entrée enregistré."
    
    # Enregistrer la nouvelle entrée de pointage
    success, msg = add_attendance_entry(user_id, qr_code_value, attendance_type, current_time)
    if success:
        return True, message
    else:
        return False, f"Erreur lors de l'enregistrement du pointage: {msg}"

# --- Initialisation de la base de données au démarrage du module ---
if __name__ == '__main__':
    # Ceci s'exécutera uniquement si db_manager.py est exécuté directement
    # et non s'il est importé comme un module.
    print("Exécution de db_manager.py en tant que script principal.")
    init_success, init_message = initialize_database()
    print(init_message)
    if init_success:
        add_default_users_if_not_exists()
        # Vous pouvez ajouter ici d'autres données de test si nécessaire
        # Exemple d'ajout de véhicule (s'il n'existe pas déjà)
        # add_new_vehicle_to_db("1234AB", "Toyota", "Corolla", 50000, date(2020, 1, 1), 7.5, "voiture", 2020, date(2025, 1, 1), date(2025, 6, 30), date(2030, 1, 1))
        # add_new_vehicle_to_db("5678CD", "Honda", "Civic", 75000, date(2018, 5, 10), 6.8, "voiture", 2018, date(2024, 12, 1), date(2025, 5, 15), date(2028, 5, 10))
        print("Base de données et utilisateurs par défaut configurés.")
    else:
        print("L'initialisation de la base de données a échoué. Veuillez vérifier les messages d'erreur ci-dessus.")


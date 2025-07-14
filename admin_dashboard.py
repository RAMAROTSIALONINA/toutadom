import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import tkinter.font as tkFont
from tkcalendar import DateEntry
from datetime import datetime, date
import string
import os

# Import de TOUTES les fonctions nécessaires de db_manager
from db_manager import (
    hash_password_bcrypt,
    add_new_user_to_db, get_all_users, get_user_by_id, update_user_in_db, delete_user_from_db,
    add_new_vehicle_to_db, get_all_vehicles, update_vehicle_in_db, delete_vehicle_from_db,
    update_vehicle_status_and_km
)

class AdminDashboard:
    def __init__(self, parent_frame, app_manager_instance):
        self.parent_frame = parent_frame
        self.app_manager_instance = app_manager_instance

        # Styles personnalisés
        self.font_title = tkFont.Font(family="Helvetica", size=20, weight="bold")
        self.font_subtitle = tkFont.Font(family="Helvetica", size=14, weight="bold")
        self.font_label = tkFont.Font(family="Helvetica", size=10)
        self.font_button_text = tkFont.Font(family="Helvetica", size=10, weight="bold")

        # --- MODIFICATION 1 : Couleurs de fond en blanc et texte en noir si nécessaire ---
        self.bg_color_dashboard = "#FFFFFF" # Blanc pour les cadres intérieurs (onglets)
        self.bg_color_main = "#FFFFFF"      # Blanc pour la couleur de fond principale (en-tête et parent_frame)
        self.fg_color_text = "#333333"      # Un gris très foncé ou noir pour le texte sur fond blanc
                                            # J'utilise #333333 pour un meilleur contraste que le noir pur.

        self.button_bg = "#3498DB"          # Couleur des boutons (gardée)
        self.button_fg = "#FFFFFF"          # Couleur du texte des boutons (gardée)
        self.entry_bg = "#E0E0E0"           # Fond des champs de saisie (un gris clair pour la visibilité)
        self.selected_item_bg = "#D0D0D0"   # Gris clair pour la sélection dans Treeview

        # --- IMPORTANT : Définir la couleur de fond du parent_frame ---
        self.parent_frame.config(bg=self.bg_color_main)

        # Chemin du logo
        script_dir = os.path.dirname(__file__)
        self.logo_path = os.path.join(script_dir, "Toutadom.png")
        self.logo_image = None # Pour stocker l'image du logo

        self.create_widgets()
        self.populate_users_treeview()
        self.populate_vehicles_treeview()

    def create_widgets(self):
        # --- En-tête du tableau de bord ---
        # Utiliser la nouvelle couleur de fond principale pour l'en-tête
        self.header_frame = tk.Frame(self.parent_frame, bg=self.bg_color_main)
        self.header_frame.pack(fill="x", pady=5, padx=10)
        self.header_frame.grid_columnconfigure(0, weight=0) # Pour le logo
        self.header_frame.grid_columnconfigure(1, weight=1) # Pour le titre (prendra l'espace restant)
        self.header_frame.grid_columnconfigure(2, weight=0) # Pour le bouton de déconnexion

        # Logo à gauche
        try:
            self.logo_image = tk.PhotoImage(file=self.logo_path)
            # --- MODIFICATION 2 : Supprimer le redimensionnement du logo ---
            # self.logo_image = self.logo_image.subsample(self.logo_image.width() // 50, self.logo_image.height() // 50) # Supprimer ou commenter cette ligne
            logo_label = tk.Label(self.header_frame, image=self.logo_image, bg=self.bg_color_main)
            logo_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        except tk.TclError:
            print(f"Erreur: Impossible de charger le logo depuis {self.logo_path}. Vérifiez le chemin et le format de l'image.")
            # Si le logo ne peut pas être chargé, afficher un texte alternatif
            empty_logo_label = tk.Label(self.header_frame, text="[Logo]", bg=self.bg_color_main, fg=self.fg_color_text, width=8)
            empty_logo_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        # Titre "GESTION ADMIN" au centre
        title_label = tk.Label(self.header_frame, text="GESTION ADMIN", font=self.font_title,
                               fg=self.fg_color_text, bg=self.bg_color_main) # Utiliser fg_color_text pour le texte
        title_label.grid(row=0, column=1, pady=5, sticky="ew")

        

        # --- Contenu principal du tableau de bord (Notebook) ---
        self.notebook = ttk.Notebook(self.parent_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Onglet Gestion des utilisateurs
        self.user_management_frame = tk.Frame(self.notebook, bg=self.bg_color_dashboard) # Utilise la couleur blanche
        self.notebook.add(self.user_management_frame, text="Gestion des Utilisateurs")
        self.create_user_management_tab()

        # Onglet Gestion des véhicules
        self.vehicle_management_frame = tk.Frame(self.notebook, bg=self.bg_color_dashboard) # Utilise la couleur blanche
        self.notebook.add(self.vehicle_management_frame, text="Gestion des Véhicules")
        self.create_vehicle_management_tab()

    def create_user_management_tab(self):
        # Configuration de la grille pour l'onglet utilisateur
        self.user_management_frame.grid_columnconfigure(0, weight=1)
        self.user_management_frame.grid_columnconfigure(1, weight=2)
        self.user_management_frame.grid_rowconfigure(1, weight=1)

        # Cadre de saisie des utilisateurs (à gauche)
        input_frame = tk.LabelFrame(self.user_management_frame, text="Détails de l'utilisateur",
                                    bg=self.bg_color_dashboard, fg=self.fg_color_text,
                                    font=self.font_subtitle, bd=2, relief="groove")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.user_entries = {}
        fields = [("Nom d'utilisateur:", "username"), ("Mot de passe:", "password"),
                  ("Nom:", "nom"), ("Prénom:", "prenom"), ("Rôle:", "role")]

        for i, (label_text, key) in enumerate(fields):
            lbl = tk.Label(input_frame, text=label_text, bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
            lbl.grid(row=i, column=0, padx=5, pady=2, sticky="w")
            
            if key == "role":
                self.user_role_var = tk.StringVar(self.user_management_frame)
                self.user_role_var.set("chauffeur") # Valeur par défaut
                role_options = ["admin", "responsable", "chauffeur"]
                entry = ttk.Combobox(input_frame, textvariable=self.user_role_var, values=role_options, state="readonly",
                                     font=self.font_label)
                entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
                self.user_entries[key] = entry
            else:
                entry = tk.Entry(input_frame, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text,
                                 insertbackground=self.fg_color_text)
                if key == "password":
                    entry.config(show="*") # Masquer le mot de passe
                entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
                self.user_entries[key] = entry

        # Checkbutton pour "Doit changer le mot de passe"
        self.must_change_password_var = tk.BooleanVar(value=True) # Par défaut, nouveau user doit changer mdp
        must_change_cb = tk.Checkbutton(input_frame, text="Doit changer le mot de passe à la prochaine connexion",
                                        variable=self.must_change_password_var,
                                        bg=self.bg_color_dashboard, fg=self.fg_color_text,
                                        selectcolor=self.bg_color_dashboard,
                                        activebackground=self.bg_color_dashboard, activeforeground=self.fg_color_text,
                                        font=self.font_label)
        must_change_cb.grid(row=len(fields), column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Bouton Afficher/Masquer le mot de passe pour le champ de création/modification
        self.show_user_password_var = tk.BooleanVar()
        self.show_user_password_var.set(False)
        show_password_check = tk.Checkbutton(input_frame, text="Afficher le mot de passe",
                                             variable=self.show_user_password_var,
                                             command=self.toggle_user_password_visibility,
                                             bg=self.bg_color_dashboard, fg=self.fg_color_text,
                                             selectcolor=self.bg_color_dashboard,
                                             activebackground=self.bg_color_dashboard, activeforeground=self.fg_color_text,
                                             font=self.font_label)
        show_password_check.grid(row=len(fields)+1, column=0, columnspan=2, padx=5, pady=2, sticky="w")


        # Cadre des boutons d'action (utilisateur)
        button_frame = tk.Frame(self.user_management_frame, bg=self.bg_color_dashboard)
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        add_button = tk.Button(button_frame, text="Ajouter", command=self.add_user, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        update_button = tk.Button(button_frame, text="Modifier", command=self.update_user, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        delete_button = tk.Button(button_frame, text="Supprimer", command=self.delete_user, font=self.font_button_text, bg="#E74C3C", fg=self.button_fg)
        clear_button = tk.Button(button_frame, text="Effacer", command=self.clear_user_fields, font=self.font_button_text, bg="#7F8C8D", fg=self.button_fg)

        add_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        update_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        delete_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        clear_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        # Treeview pour afficher les utilisateurs (à droite)
        self.user_tree = ttk.Treeview(self.user_management_frame, columns=("ID", "Username", "Nom", "Prénom", "Rôle", "Changer MDP"), show="headings")
        self.user_tree.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        # Configuration des colonnes du Treeview utilisateur
        self.user_tree.heading("ID", text="ID", anchor="center")
        self.user_tree.heading("Username", text="Nom d'utilisateur", anchor="center")
        self.user_tree.heading("Nom", text="Nom", anchor="center")
        self.user_tree.heading("Prénom", text="Prénom", anchor="center")
        self.user_tree.heading("Rôle", text="Rôle", anchor="center")
        self.user_tree.heading("Changer MDP", text="Changer MDP", anchor="center") # Nouvelle colonne
        self.user_tree.column("ID", width=30, anchor="center")
        self.user_tree.column("Username", width=100, anchor="w")
        self.user_tree.column("Nom", width=100, anchor="w")
        self.user_tree.column("Prénom", width=100, anchor="w")
        self.user_tree.column("Rôle", width=80, anchor="center")
        self.user_tree.column("Changer MDP", width=80, anchor="center") # Largeur de la nouvelle colonne
        
        # Scrollbar pour le Treeview utilisateur
        user_scrollbar = ttk.Scrollbar(self.user_management_frame, orient="vertical", command=self.user_tree.yview)
        user_scrollbar.grid(row=0, column=2, rowspan=2, sticky="ns")
        self.user_tree.configure(yscrollcommand=user_scrollbar.set)
        self.user_tree.bind("<<TreeviewSelect>>", self.load_user_into_fields)

    def toggle_user_password_visibility(self):
        """Affiche ou masque le mot de passe dans le champ de saisie utilisateur."""
        if self.show_user_password_var.get():
            self.user_entries['password'].config(show="")
        else:
            self.user_entries['password'].config(show="*")

    def populate_users_treeview(self):
        """Remplit le Treeview des utilisateurs avec les données de la base de données."""
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)

        users = get_all_users()
        for user in users:
            # user tuple: (id, username, nom, prenom, role)
            # Pour l'instant, on n'affiche pas si le mot de passe doit être changé
            # car cette information n'est pas directement stockée/récupérée ici pour les utilisateurs existants.
            # On pourrait ajouter une colonne pour cela si le besoin s'avère.
            self.user_tree.insert("", "end", values=(user[0], user[1], user[2], user[3], user[4], "N/A"))

    def load_user_into_fields(self, event):
        """Charge les données de l'utilisateur sélectionné dans les champs de saisie."""
        selected_item = self.user_tree.focus()
        if selected_item:
            values = self.user_tree.item(selected_item, 'values')
            self.user_entries['username'].delete(0, tk.END)
            self.user_entries['username'].insert(0, values[1])
            self.user_entries['nom'].delete(0, tk.END)
            self.user_entries['nom'].insert(0, values[2])
            self.user_entries['prenom'].delete(0, tk.END)
            self.user_entries['prenom'].insert(0, values[3])
            self.user_role_var.set(values[4])
            
            # Ne pas charger le mot de passe haché dans le champ 'password'
            # Le champ password doit être effacé ou laissé vide pour une nouvelle saisie
            self.user_entries['password'].delete(0, tk.END)
            # Désactiver ou masquer la case "Doit changer le mot de passe" pour les utilisateurs existants
            self.must_change_password_var.set(False) # Un user existant n'a pas cette contrainte par défaut
            
            # Stocker l'ID de l'utilisateur sélectionné pour les opérations de modification/suppression
            self.selected_user_id = values[0]
        else:
            self.selected_user_id = None

    def add_user(self):
        """Ajoute un nouvel utilisateur à la base de données."""
        username = self.user_entries['username'].get()
        password = self.user_entries['password'].get()
        nom = self.user_entries['nom'].get()
        prenom = self.user_entries['prenom'].get()
        role = self.user_role_var.get()

        if not all([username, password, nom, prenom, role]):
            messagebox.showerror("Erreur de saisie", "Tous les champs utilisateur doivent être remplis.")
            return

        hashed_password = hash_password_bcrypt(password)
        if not hashed_password:
            messagebox.showerror("Erreur", "Échec du hachage du mot de passe.")
            return

        success, message = add_new_user_to_db(username, hashed_password, nom, prenom, role)
        if success:
            messagebox.showinfo("Succès", message)
            self.populate_users_treeview()
            self.clear_user_fields()
        else:
            messagebox.showerror("Erreur", message)

    def update_user(self):
        """Met à jour un utilisateur existant dans la base de données."""
        if not hasattr(self, 'selected_user_id') or self.selected_user_id is None:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner un utilisateur à modifier dans le tableau.")
            return

        username = self.user_entries['username'].get()
        password = self.user_entries['password'].get() # Peut être vide si pas de changement
        nom = self.user_entries['nom'].get()
        prenom = self.user_entries['prenom'].get()
        role = self.user_role_var.get()

        if not all([username, nom, prenom, role]):
            messagebox.showerror("Erreur de saisie", "Tous les champs utilisateur (sauf mot de passe) doivent être remplis.")
            return

        hashed_password = None
        if password: # Si un nouveau mot de passe est saisi, le hacher
            hashed_password = hash_password_bcrypt(password)
            if not hashed_password:
                messagebox.showerror("Erreur", "Échec du hachage du nouveau mot de passe.")
                return

        success, message = update_user_in_db(self.selected_user_id, username, hashed_password, nom, prenom, role)
        if success:
            messagebox.showinfo("Succès", message)
            self.populate_users_treeview()
            self.clear_user_fields()
        else:
            messagebox.showerror("Erreur", message)

    def delete_user(self):
        """Supprime un utilisateur de la base de données."""
        if not hasattr(self, 'selected_user_id') or self.selected_user_id is None:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner un utilisateur à supprimer dans le tableau.")
            return

        if messagebox.askyesno("Confirmer la suppression", "Êtes-vous sûr de vouloir supprimer cet utilisateur ?"):
            success, message = delete_user_from_db(self.selected_user_id)
            if success:
                messagebox.showinfo("Succès", message)
                self.populate_users_treeview()
                self.clear_user_fields()
            else:
                messagebox.showerror("Erreur", message)

    def clear_user_fields(self):
        """Efface tous les champs de saisie utilisateur."""
        for key in self.user_entries:
            if key != 'role': # Le rôle est géré par StringVar
                self.user_entries[key].delete(0, tk.END)
        self.user_role_var.set("chauffeur") # Réinitialiser le rôle par défaut
        self.selected_user_id = None
        self.must_change_password_var.set(True) # Réinitialiser pour un nouvel utilisateur
        self.user_entries['password'].config(show="*") # Masquer le mot de passe
        self.show_user_password_var.set(False)


    # --- Gestion des Véhicules ---
    def create_vehicle_management_tab(self):
        self.vehicle_management_frame.grid_columnconfigure(0, weight=1)
        self.vehicle_management_frame.grid_columnconfigure(1, weight=2)
        self.vehicle_management_frame.grid_rowconfigure(1, weight=1)

        # Cadre de saisie des véhicules (à gauche)
        input_frame = tk.LabelFrame(self.vehicle_management_frame, text="Détails du véhicule",
                                    bg=self.bg_color_dashboard, fg=self.fg_color_text,
                                    font=self.font_subtitle, bd=2, relief="groove")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.vehicle_entries = {}
        fields = [
            ("Immatriculation:", "immatriculation"),
            ("Marque:", "marque"),
            ("Modèle:", "modele"),
            ("Kilométrage Actuel:", "kilometrage_actuel"),
            ("Date d'Acquisition:", "date_acquisition"),
            ("Consommation Théorique (L/100km):", "consommation_theorique"),
            ("Type de Véhicule:", "type_vehicule"),
            ("Année de Mise en Circulation:", "annee_mise_en_circulation"),
            ("Date Assurance:", "date_assurance"),
            ("Date Visite Technique:", "date_visite_technique"),
            ("Date Carte Rose:", "date_carte_rose"),
            ("Statut:", "statut")
        ]

        for i, (label_text, key) in enumerate(fields):
            lbl = tk.Label(input_frame, text=label_text, bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
            lbl.grid(row=i, column=0, padx=5, pady=2, sticky="w")
            
            if key in ["date_acquisition", "date_assurance", "date_visite_technique", "date_carte_rose"]:
                cal = DateEntry(input_frame, selectmode='day', font=self.font_label,
                                locale='fr_FR', date_pattern='yyyy-mm-dd',
                                background=self.entry_bg, foreground='black', borderwidth=2)
                cal.set_date(datetime.now().date()) # Date par défaut
                cal.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
                self.vehicle_entries[key] = cal
            elif key == "type_vehicule":
                self.vehicle_type_var = tk.StringVar(self.vehicle_management_frame)
                self.vehicle_type_var.set("voiture")
                type_options = ["voiture", "moto"]
                entry = ttk.Combobox(input_frame, textvariable=self.vehicle_type_var, values=type_options, state="readonly",
                                     font=self.font_label)
                entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
                self.vehicle_entries[key] = entry
            elif key == "statut":
                self.vehicle_status_var = tk.StringVar(self.vehicle_management_frame)
                self.vehicle_status_var.set("Disponible")
                status_options = ["Disponible", "En service", "En maintenance", "Hors service"]
                entry = ttk.Combobox(input_frame, textvariable=self.vehicle_status_var, values=status_options, state="readonly",
                                     font=self.font_label)
                entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
                self.vehicle_entries[key] = entry
            else:
                entry = tk.Entry(input_frame, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text,
                                 insertbackground=self.fg_color_text)
                entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
                self.vehicle_entries[key] = entry

        # Cadre des boutons d'action (véhicule)
        button_frame = tk.Frame(self.vehicle_management_frame, bg=self.bg_color_dashboard)
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        add_button = tk.Button(button_frame, text="Ajouter", command=self.add_vehicle, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        update_button = tk.Button(button_frame, text="Modifier", command=self.update_vehicle, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        delete_button = tk.Button(button_frame, text="Supprimer", command=self.delete_vehicle, font=self.font_button_text, bg="#E74C3C", fg=self.button_fg)
        clear_button = tk.Button(button_frame, text="Effacer", command=self.clear_vehicle_fields, font=self.font_button_text, bg="#7F8C8D", fg=self.button_fg)

        add_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        update_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        delete_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        clear_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        # Treeview pour afficher les véhicules (à droite)
        self.vehicle_tree = ttk.Treeview(self.vehicle_management_frame, columns=(
            "ID", "Immatriculation", "Marque", "Modèle", "Kilométrage", "Date Acquisition",
            "Conso Théorique", "Type", "Année Circul.", "Date Assurance", "Date Visite Tech.",
            "Date Carte Rose", "Statut"
        ), show="headings")
        self.vehicle_tree.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        # Configuration des colonnes du Treeview véhicule
        self.vehicle_tree.heading("ID", text="ID", anchor="center")
        self.vehicle_tree.heading("Immatriculation", text="Immatriculation", anchor="center")
        self.vehicle_tree.heading("Marque", text="Marque", anchor="center")
        self.vehicle_tree.heading("Modèle", text="Modèle", anchor="center")
        self.vehicle_tree.heading("Kilométrage", text="Kilométrage", anchor="center")
        self.vehicle_tree.heading("Date Acquisition", text="Date Acquisition", anchor="center")
        self.vehicle_tree.heading("Conso Théorique", text="Conso Théorique", anchor="center")
        self.vehicle_tree.heading("Type", text="Type", anchor="center")
        self.vehicle_tree.heading("Année Circul.", text="Année Circul.", anchor="center")
        self.vehicle_tree.heading("Date Assurance", text="Date Assurance", anchor="center")
        self.vehicle_tree.heading("Date Visite Tech.", text="Date Visite Tech.", anchor="center")
        self.vehicle_tree.heading("Date Carte Rose", text="Date Carte Rose", anchor="center")
        self.vehicle_tree.heading("Statut", text="Statut", anchor="center")

        self.vehicle_tree.column("ID", width=30, anchor="center")
        self.vehicle_tree.column("Immatriculation", width=100, anchor="w")
        self.vehicle_tree.column("Marque", width=80, anchor="w")
        self.vehicle_tree.column("Modèle", width=80, anchor="w")
        self.vehicle_tree.column("Kilométrage", width=90, anchor="e")
        self.vehicle_tree.column("Date Acquisition", width=110, anchor="center")
        self.vehicle_tree.column("Conso Théorique", width=120, anchor="e")
        self.vehicle_tree.column("Type", width=60, anchor="center")
        self.vehicle_tree.column("Année Circul.", width=100, anchor="center")
        self.vehicle_tree.column("Date Assurance", width=100, anchor="center")
        self.vehicle_tree.column("Date Visite Tech.", width=120, anchor="center")
        self.vehicle_tree.column("Date Carte Rose", width=110, anchor="center")
        self.vehicle_tree.column("Statut", width=90, anchor="center")

        # Scrollbar pour le Treeview véhicule
        vehicle_scrollbar = ttk.Scrollbar(self.vehicle_management_frame, orient="vertical", command=self.vehicle_tree.yview)
        vehicle_scrollbar.grid(row=0, column=2, rowspan=2, sticky="ns")
        self.vehicle_tree.configure(yscrollcommand=vehicle_scrollbar.set)
        self.vehicle_tree.bind("<<TreeviewSelect>>", self.load_vehicle_into_fields)

    def populate_vehicles_treeview(self):
        """Remplit le Treeview des véhicules avec les données de la base de données."""
        for item in self.vehicle_tree.get_children():
            self.vehicle_tree.delete(item)

        vehicles = get_all_vehicles()
        for vehicle in vehicles:
            # Assurez-vous que les indices correspondent à la requête SELECT dans db_manager.py
            # id, immatriculation, marque, modele, kilometrage_actuel, date_acquisition,
            # consommation_theorique, type_vehicule, annee_mise_en_circulation, date_assurance,
            # date_visite_technique, date_carte_rose, statut
            
            vehicle_id = vehicle[0]
            immatriculation = vehicle[1]
            marque = vehicle[2]
            modele = vehicle[3]
            kilometrage_actuel = vehicle[4]
            date_acquisition_str = vehicle[5].strftime("%Y-%m-%d") if vehicle[5] else ""
            consommation_theorique = vehicle[6]
            type_vehicule = vehicle[7]
            annee_mise_en_circulation = vehicle[8]
            # CORRECTION ICI: Les indices pour les dates étaient décalés.
            date_assurance_str = vehicle[9].strftime("%Y-%m-%d") if vehicle[9] else ""
            date_visite_technique_str = vehicle[10].strftime("%Y-%m-%d") if vehicle[10] else ""
            date_carte_rose_str = vehicle[11].strftime("%Y-%m-%d") if vehicle[11] else ""
            statut = vehicle[12]

            self.vehicle_tree.insert("", "end", values=(
                vehicle_id, immatriculation, marque, modele, kilometrage_actuel,
                date_acquisition_str, consommation_theorique, type_vehicule,
                annee_mise_en_circulation, date_assurance_str, date_visite_technique_str,
                date_carte_rose_str, statut
            ))

    def load_vehicle_into_fields(self, event):
        """Charge les données du véhicule sélectionné dans les champs de saisie."""
        selected_item = self.vehicle_tree.focus()
        if selected_item:
            values = self.vehicle_tree.item(selected_item, 'values')
            self.vehicle_entries['immatriculation'].delete(0, tk.END)
            self.vehicle_entries['immatriculation'].insert(0, values[1])
            self.vehicle_entries['marque'].delete(0, tk.END)
            self.vehicle_entries['marque'].insert(0, values[2])
            self.vehicle_entries['modele'].delete(0, tk.END)
            self.vehicle_entries['modele'].insert(0, values[3])
            self.vehicle_entries['kilometrage_actuel'].delete(0, tk.END)
            self.vehicle_entries['kilometrage_actuel'].insert(0, values[4])
            
            # Pour les DateEntry, utilisez set_date
            if values[5]: # Date Acquisition
                self.vehicle_entries['date_acquisition'].set_date(datetime.strptime(values[5], "%Y-%m-%d").date())
            if values[9]: # Date Assurance (index corrigé)
                self.vehicle_entries['date_assurance'].set_date(datetime.strptime(values[9], "%Y-%m-%d").date())
            if values[10]: # Date Visite Technique (index corrigé)
                self.vehicle_entries['date_visite_technique'].set_date(datetime.strptime(values[10], "%Y-%m-%d").date())
            if values[11]: # Date Carte Rose (index corrigé)
                self.vehicle_entries['date_carte_rose'].set_date(datetime.strptime(values[11], "%Y-%m-%d").date())
            
            self.vehicle_entries['consommation_theorique'].delete(0, tk.END)
            self.vehicle_entries['consommation_theorique'].insert(0, values[6])
            self.vehicle_type_var.set(values[7])
            self.vehicle_entries['annee_mise_en_circulation'].delete(0, tk.END)
            self.vehicle_entries['annee_mise_en_circulation'].insert(0, values[8])
            self.vehicle_status_var.set(values[12]) # Statut (index corrigé)

            self.selected_vehicle_id = values[0]
        else:
            self.selected_vehicle_id = None

    def add_vehicle(self):
        """Ajoute un nouveau véhicule à la base de données."""
        immatriculation = self.vehicle_entries['immatriculation'].get()
        marque = self.vehicle_entries['marque'].get()
        modele = self.vehicle_entries['modele'].get()
        
        try:
            kilometrage_actuel = int(self.vehicle_entries['kilometrage_actuel'].get())
        except ValueError:
            messagebox.showerror("Erreur de saisie", "Le kilométrage doit être un nombre entier.")
            return

        date_acquisition = self.vehicle_entries['date_acquisition'].get_date()
        
        try:
            consommation_theorique = float(self.vehicle_entries['consommation_theorique'].get())
        except ValueError:
            messagebox.showerror("Erreur de saisie", "La consommation théorique doit être un nombre.")
            return
            
        type_vehicule = self.vehicle_type_var.get()
        
        try:
            annee_mise_en_circulation = int(self.vehicle_entries['annee_mise_en_circulation'].get())
        except ValueError:
            messagebox.showerror("Erreur de saisie", "L'année de mise en circulation doit être un nombre entier.")
            return

        date_assurance = self.vehicle_entries['date_assurance'].get_date()
        date_visite_technique = self.vehicle_entries['date_visite_technique'].get_date()
        date_carte_rose = self.vehicle_entries['date_carte_rose'].get_date()

        if not all([immatriculation, marque, modele, type_vehicule]):
            messagebox.showerror("Erreur de saisie", "Les champs Immatriculation, Marque, Modèle et Type de Véhicule sont obligatoires.")
            return

        success, message = add_new_vehicle_to_db(
            immatriculation, marque, modele, kilometrage_actuel, date_acquisition,
            consommation_theorique, type_vehicule, annee_mise_en_circulation,
            date_assurance, date_visite_technique, date_carte_rose
        )
        if success:
            messagebox.showinfo("Succès", message)
            self.populate_vehicles_treeview()
            self.clear_vehicle_fields()
        else:
            messagebox.showerror("Erreur", message)

    def update_vehicle(self):
        """Met à jour un véhicule existant dans la base de données."""
        if not hasattr(self, 'selected_vehicle_id') or self.selected_vehicle_id is None:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner un véhicule à modifier dans le tableau.")
            return

        immatriculation = self.vehicle_entries['immatriculation'].get()
        marque = self.vehicle_entries['marque'].get()
        modele = self.vehicle_entries['modele'].get()
        
        try:
            kilometrage_actuel = int(self.vehicle_entries['kilometrage_actuel'].get())
        except ValueError:
            messagebox.showerror("Erreur de saisie", "Le kilométrage doit être un nombre entier.")
            return

        date_acquisition = self.vehicle_entries['date_acquisition'].get_date()
        
        try:
            consommation_theorique = float(self.vehicle_entries['consommation_theorique'].get())
        except ValueError:
            messagebox.showerror("Erreur de saisie", "La consommation théorique doit être un nombre.")
            return
            
        type_vehicule = self.vehicle_type_var.get()
        
        try:
            annee_mise_en_circulation = int(self.vehicle_entries['annee_mise_en_circulation'].get())
        except ValueError:
            messagebox.showerror("Erreur de saisie", "L'année de mise en circulation doit être un nombre entier.")
            return

        date_assurance = self.vehicle_entries['date_assurance'].get_date()
        date_visite_technique = self.vehicle_entries['date_visite_technique'].get_date()
        date_carte_rose = self.vehicle_entries['date_carte_rose'].get_date()
        statut = self.vehicle_status_var.get()


        if not all([immatriculation, marque, modele, type_vehicule, statut]):
            messagebox.showerror("Erreur de saisie", "Les champs Immatriculation, Marque, Modèle, Type de Véhicule et Statut sont obligatoires.")
            return

        success, message = update_vehicle_in_db(
            self.selected_vehicle_id, immatriculation, marque, modele, kilometrage_actuel,
            date_acquisition, consommation_theorique, type_vehicule, annee_mise_en_circulation,
            date_assurance, date_visite_technique, date_carte_rose, statut
        )
        if success:
            messagebox.showinfo("Succès", message)
            self.populate_vehicles_treeview()
            self.clear_vehicle_fields()
        else:
            messagebox.showerror("Erreur", message)

    def delete_vehicle(self):
        """Supprime un véhicule de la base de données."""
        selected_item = self.vehicle_tree.focus()
        if not selected_item:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner un véhicule à supprimer dans le tableau.")
            return
        
        vehicle_id = self.vehicle_tree.item(selected_item, 'values')[0]
        immatriculation_to_delete = self.vehicle_tree.item(selected_item, 'values')[1]

        if messagebox.askyesno("Confirmer la suppression", f"Êtes-vous sûr de vouloir supprimer le véhicule '{immatriculation_to_delete}' (ID: {vehicle_id})?"):
            success, message = delete_vehicle_from_db(vehicle_id)
            if success:
                messagebox.showinfo("Succès", message)
                self.populate_vehicles_treeview()
            else:
                messagebox.showerror("Erreur", message)

    def clear_vehicle_fields(self):
        """Efface tous les champs de saisie véhicule."""
        for key in ['immatriculation', 'marque', 'modele', 'kilometrage_actuel', 'annee_mise_en_circulation', 'consommation_theorique']:# Clear other entry fields
            self.vehicle_entries[key].delete(0, tk.END)
        
        # Réinitialiser les DateEntry à la date actuelle ou une valeur par défaut
        self.vehicle_entries['date_acquisition'].set_date(datetime.now().date())
        self.vehicle_entries['date_assurance'].set_date(datetime.now().date())
        self.vehicle_entries['date_visite_technique'].set_date(datetime.now().date())
        self.vehicle_entries['date_carte_rose'].set_date(datetime.now().date())

        self.vehicle_type_var.set("voiture") # Réinitialiser le type de véhicule
        self.vehicle_status_var.set("Disponible") # Réinitialiser le statut
        self.selected_vehicle_id = None
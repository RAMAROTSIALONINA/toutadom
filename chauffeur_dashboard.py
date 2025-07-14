import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import tkinter.font as tkFont
from tkcalendar import DateEntry
from datetime import datetime, date, timedelta
import qrcode
from PIL import ImageTk, Image
import os
import io
from pyzbar import pyzbar
import json

# Import des fonctions nécessaires de db_manager (à adapter selon votre implémentation réelle)
from db_manager import (
    get_all_chauffeurs_and_responsables, get_active_vehicles,
    get_vehicle_by_id, get_user_by_id,
    get_attribution_by_chauffeur_id,
    add_vehicle_inspection_report, get_all_vehicle_inspection_reports, update_vehicle_inspection_report, delete_vehicle_inspection_report, get_vehicle_inspection_report_by_id,
    add_fuel_entry_to_db, get_all_fuel_entries, update_fuel_entry_in_db, delete_fuel_entry_from_db, get_fuel_entry_by_id,
    add_incident_report_to_db, get_all_incident_reports, update_incident_report_in_db, delete_incident_report_from_db, get_incident_report_by_id,
    get_vehicle_document_expiry_dates,
    update_vehicle_km
)

class ChauffeurDashboard:
    def __init__(self, parent_frame, app_manager_instance, user_id, username, user_role, user_fullname):
        print("ChauffeurDashboard: __init__ called.") # Diagnostic print
        self.parent_frame = parent_frame
        self.app_manager_instance = app_manager_instance
        
        self.logged_in_user_id = user_id
        self.logged_in_username = username
        self.logged_in_user_role = user_role
        self.logged_in_user_fullname = user_fullname

        # Initialisation des attributs
        self.qr_img = None
        self.ATTENDANCE_DIR = "pointages"
        os.makedirs(self.ATTENDANCE_DIR, exist_ok=True)

        # Configuration initiale
        self.setup_fonts_and_colors()
        self.setup_dropdown_options()

        # Création des widgets principaux
        self.create_widgets()
        print("ChauffeurDashboard: create_widgets completed.") # Diagnostic print

        # Initialisation des IDs de sélection
        self.selected_fuel_entry_id = None
        self.selected_incident_id = None
        self.selected_inspection_id = None
        

    def setup_fonts_and_colors(self):
        """Configure les polices et couleurs"""
        self.font_title = tkFont.Font(family="Helvetica", size=20, weight="bold")
        self.font_subtitle = tkFont.Font(family="Helvetica", size=14, weight="bold")
        self.font_label = tkFont.Font(family="Helvetica", size=10)
        self.font_button_text = tkFont.Font(family="Helvetica", size=10, weight="bold")

        # Couleurs
        self.bg_color_dashboard = "#FFFFFF"
        self.fg_color_text = "#2C3E50"
        self.button_bg = "#E0E0E0"
        self.button_fg = "#000000"
        self.entry_bg = "#F8F9F9"
        self.selected_item_bg = "#D6EAF8"

    def setup_dropdown_options(self):
        """Configure les options des listes déroulantes"""
        self.incident_types = ["Panne mécanique", "Accident", "Problème électrique", "Pneu crevé", "Vandalisme", "Autre"]
        self.etat_general_options = ["Excellent", "Bon", "Moyen", "Mauvais"]
        self.qr_colors = ["black", "white", "blue", "red", "green", "purple", "orange", "grey", "darkblue", "darkgreen"]

    def create_widgets(self):
        """Crée tous les widgets principaux"""
        print("ChauffeurDashboard: create_widgets called.") # Diagnostic print
        # Configuration du parent frame
        self.parent_frame.grid_rowconfigure(0, weight=0)
        self.parent_frame.grid_rowconfigure(1, weight=1)
        self.parent_frame.grid_columnconfigure(0, weight=1)

        # Création du header
        self.create_header()

        # Création du notebook et des onglets
        self.notebook = ttk.Notebook(self.parent_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Création des onglets
        self.pointage_tab = ttk.Frame(self.notebook)  # Création de l'onglet
        self.notebook.add(self.pointage_tab, text="Pointage")
        self.create_pointage_tab_content()  # Appelle la méthode pour peupler le contenu de cet onglet
        
        # Création des autres onglets...
        self.controle_vehicule_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.controle_vehicule_tab, text="Contrôle Véhicule")
        self.create_controle_vehicule_tab() # Appel de la méthode pour cet onglet
        
        self.declaration_probleme_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.declaration_probleme_tab, text="Déclaration Problème")
        self.create_declaration_probleme_tab() # Appel de la méthode pour cet onglet

        self.alertes_documents_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.alertes_documents_tab, text="Alertes Documents")
        self.create_alertes_documents_tab() # Appel de la méthode pour cet onglet

    def create_header(self):
        """Crée l'en-tête avec logo, titre et bouton de déconnexion"""
        header_frame = tk.Frame(self.parent_frame, bg=self.bg_color_dashboard)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(0, weight=0)
        header_frame.grid_columnconfigure(1, weight=1)
        header_frame.grid_columnconfigure(2, weight=0)

        # Logo
        try:
            script_dir = os.path.dirname(__file__)
            logo_path = os.path.join(script_dir, "Toutadom.png")
            logo_image_pil = Image.open(logo_path).resize((80, 80), Image.Resampling.LANCZOS)
            self.logo_tk = ImageTk.PhotoImage(logo_image_pil)
            logo_label = tk.Label(header_frame, image=self.logo_tk, bg=self.bg_color_dashboard)
        except Exception as e:
            logo_label = tk.Label(header_frame, text="[Erreur Logo]", bg=self.bg_color_dashboard, fg="red")
        logo_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        # Titre
        title_label = tk.Label(header_frame, text="GESTION CHAUFFEUR", font=self.font_title,
                               bg=self.bg_color_dashboard, fg=self.fg_color_text)
        title_label.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")

        

    def create_pointage_tab_content(self):
        """Crée le contenu de l'onglet Pointage"""
        print("ChauffeurDashboard: create_pointage_tab_content called.") # Diagnostic print
        # Configuration de la grille de l'onglet (self.pointage_tab est le parent)
        self.pointage_tab.grid_columnconfigure(0, weight=1)
        self.pointage_tab.grid_columnconfigure(1, weight=1)
        self.pointage_tab.grid_rowconfigure(0, weight=1)

        # Frame pour la génération de QR Code
        qr_gen_frame = tk.LabelFrame(self.pointage_tab, text="Générer QR Code de Pointage",
                                     bg=self.bg_color_dashboard, fg=self.fg_color_text,
                                     font=self.font_subtitle, bd=2, relief="groove")
        qr_gen_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        qr_gen_frame.grid_columnconfigure(1, weight=1)

        # Frame pour la lecture de QR Code
        qr_read_frame = tk.LabelFrame(self.pointage_tab, text="Lire QR Code",
                                     bg=self.bg_color_dashboard, fg=self.fg_color_text,
                                     font=self.font_subtitle, bd=2, relief="groove")
        qr_read_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        qr_read_frame.grid_columnconfigure(0, weight=1)
        
        # --- Contenu de qr_gen_frame ---
        tk.Label(qr_gen_frame, text="Contenu (Nom d'utilisateur):", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label).grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.qr_content_entry = tk.Entry(qr_gen_frame, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text)
        self.qr_content_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.qr_content_entry.insert(0, self.logged_in_username) # Pré-remplir avec le nom d'utilisateur

        tk.Label(qr_gen_frame, text="Taille du module (box_size):", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label).grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.qr_box_size_var = tk.StringVar(value="10")
        self.qr_box_size_combobox = ttk.Combobox(qr_gen_frame, textvariable=self.qr_box_size_var, values=[10, 8, 6, 4], state="readonly", font=self.font_label)
        self.qr_box_size_combobox.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.qr_box_size_combobox.set(10)

        tk.Label(qr_gen_frame, text="Couleur du QR Code (fill_color):", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label).grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.qr_fill_color_var = tk.StringVar(value="black")
        self.qr_fill_color_combobox = ttk.Combobox(qr_gen_frame, textvariable=self.qr_fill_color_var, values=self.qr_colors, state="readonly", font=self.font_label)
        self.qr_fill_color_combobox.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        self.qr_fill_color_combobox.set("black")

        tk.Label(qr_gen_frame, text="Couleur de fond (back_color):", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label).grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.qr_back_color_var = tk.StringVar(value="white")
        self.qr_back_color_combobox = ttk.Combobox(qr_gen_frame, textvariable=self.qr_back_color_var, values=self.qr_colors, state="readonly", font=self.font_label)
        self.qr_back_color_combobox.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        self.qr_back_color_combobox.set("white")

        generate_qr_button = tk.Button(qr_gen_frame, text="Générer QR Code",
                                       command=self.generate_pointage_qr_code,
                                       font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        generate_qr_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        save_qr_button = tk.Button(qr_gen_frame, text="Sauvegarder QR Code",
                                   command=self.save_qr_code,
                                   font=self.font_button_text, bg="#27AE60", fg=self.button_fg)
        save_qr_button.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.qr_code_label = tk.Label(qr_gen_frame, bg=self.bg_color_dashboard)
        self.qr_code_label.grid(row=6, column=0, columnspan=2, pady=10)

        tk.Label(qr_gen_frame, text="Ce QR Code est un exemple. Dans une application réelle, des tokens sécurisés seraient utilisés.",
                 bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label, wraplength=400).grid(row=7, column=0, columnspan=2, pady=5)

        # --- Contenu de qr_read_frame ---
        tk.Label(qr_read_frame, text="Contenu du QR Code lu:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label).pack(pady=5)
        self.decoded_qr_text = tk.Text(qr_read_frame, height=5, width=40, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text, state="disabled")
        self.decoded_qr_text.pack(pady=5, fill="x", expand=True)

        load_qr_button = tk.Button(qr_read_frame, text="Charger QR Code depuis Image",
                                   command=self.load_qr_code_from_image,
                                   font=self.font_button_text, bg="#2980B9", fg=self.button_fg)
        load_qr_button.pack(pady=10)

        tk.Label(qr_read_frame, text="Note: La lecture par caméra nécessiterait des librairies supplémentaires (ex: OpenCV) et une implémentation plus complexe.",
                 bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label, wraplength=300).pack(pady=5)
        
        print("ChauffeurDashboard: create_pointage_tab_content completed.") # Diagnostic print


    # --- Fonctions de gestion des fichiers JSON de pointage ---
    def get_attendance_file_path(self, date_str):
        """
        Génère le chemin complet du fichier JSON de pointage pour une date donnée.
        Le format du nom de fichier sera 'pointage_AAAA-MM-JJ.json'.
        """
        return os.path.join(self.ATTENDANCE_DIR, f"pointage_{date_str}.json")

    def load_daily_attendance(self, date_str):
        """
        Charge les données de pointage pour une date spécifique depuis un fichier JSON.
        Retourne un dictionnaire vide si le fichier n'existe pas ou est vide.
        """
        file_path = self.get_attendance_file_path(date_str)
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return {"date": date_str, "attendances": []}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            messagebox.showwarning("Erreur JSON", f"Le fichier de pointage {file_path} est corrompu. Création d'un nouveau.")
            return {"date": date_str, "attendances": []}
        except Exception as e:
            messagebox.showerror("Erreur de chargement", f"Erreur lors du chargement des pointages pour {date_str}: {e}")
            return {"date": date_str, "attendances": []}

    def save_daily_attendance(self, date_str, data):
        """
        Sauvegarde les données de pointage pour une date spécifique dans un fichier JSON.
        """
        file_path = self.get_attendance_file_path(date_str)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Erreur de sauvegarde", f"Erreur lors de la sauvegarde des pointages pour {date_str}: {e}")

    def record_attendance(self, username):
        """
        Enregistre le pointage d'un utilisateur pour la date et l'heure actuelles.
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        daily_attendance_data = self.load_daily_attendance(date_str)
        
        # Vérifier si l'utilisateur a déjà pointé pour l'heure actuelle (pour éviter des doublons immédiats)
        already_punched = False
        for entry in daily_attendance_data["attendances"]:
            if entry["username"] == username and entry["time"] == time_str:
                already_punched = True
                break

        if already_punched:
            messagebox.showinfo("Pointage", f"L'utilisateur {username} a déjà pointé à {time_str} aujourd'hui. (Doublon évité)")
        else:
            attendance_entry = {
                "username": username,
                "time": time_str
            }
            daily_attendance_data["attendances"].append(attendance_entry)
            self.save_daily_attendance(date_str, daily_attendance_data)
            messagebox.showinfo("Pointage Enregistré", f"Pointage enregistré pour {username} à {time_str} le {date_str}.")


    def generate_pointage_qr_code(self):
        """
        Génère un QR code pour le pointage avec des options personnalisables.
        """
        print("ChauffeurDashboard: generate_pointage_qr_code called.") # Diagnostic print
        qr_data = self.qr_content_entry.get()
        if not qr_data:
            messagebox.showwarning("Contenu manquant", "Veuillez entrer un contenu pour le QR Code.")
            return

        try:
            box_size = int(self.qr_box_size_var.get())
            fill_color = self.qr_fill_color_var.get()
            back_color = self.qr_back_color_var.get()
        except ValueError:
            messagebox.showwarning("Erreur de saisie", "La taille du module doit être un nombre entier.")
            return
        
        # Utilise le nom d'utilisateur et un timestamp pour simuler un token de pointage.
        final_qr_data = f"Pointage - Utilisateur: {qr_data} | Timestamp: {datetime.now().timestamp()}"
        
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=box_size,
                border=4,
            )
            qr.add_data(final_qr_data)
            qr.make(fit=True)

            self.qr_img = qr.make_image(fill_color=fill_color, back_color=back_color)
            
            img_byte_arr = io.BytesIO()
            self.qr_img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            photo = ImageTk.PhotoImage(Image.open(io.BytesIO(img_byte_arr)))
            self.qr_code_label.config(image=photo)
            self.qr_code_label.image = photo
            
            messagebox.showinfo("QR Code Généré", "Le QR Code de pointage a été généré avec succès.")

        except Exception as e:
            messagebox.showerror("Erreur QR Code", f"Impossible de générer le QR Code: {e}\nAssurez-vous d'avoir installé 'qrcode' et 'Pillow' (pip install qrcode Pillow).")

    def save_qr_code(self):
        """
        Sauvegarde le QR code actuellement affiché dans un fichier.
        """
        if self.qr_img is None:
            messagebox.showwarning("Aucun QR Code", "Veuillez d'abord générer un QR Code.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("Fichiers PNG", "*.png"), ("Tous les fichiers", "*.*")],
            title="Sauvegarder le QR Code"
        )
        if file_path:
            try:
                self.qr_img.save(file_path)
                messagebox.showinfo("Succès", f"QR Code sauvegardé sous: {file_path}")
            except Exception as e:
                messagebox.showerror("Erreur de sauvegarde", f"Impossible de sauvegarder le QR Code: {e}")

    def load_qr_code_from_image(self):
        """
        Charge une image et tente de lire un QR code à partir d'elle.
        Si un QR code de pointage est détecté, enregistre le pointage.
        """
        file_path = filedialog.askopenfilename(
            filetypes=[("Fichiers Image", "*.png;*.jpg;*.jpeg;*.gif"), ("Tous les fichiers", "*.*")],
            title="Sélectionner une image QR Code"
        )
        if file_path:
            try:
                img = Image.open(file_path)
                decoded_objects = pyzbar.decode(img)

                self.decoded_qr_text.config(state="normal")
                self.decoded_qr_text.delete("1.0", tk.END)

                if decoded_objects:
                    for obj in decoded_objects:
                        decoded_data = obj.data.decode("utf-8")
                        self.decoded_qr_text.insert(tk.END, f"Type: {obj.type}\n")
                        self.decoded_qr_text.insert(tk.END, f"Données: {decoded_data}\n\n")
                        
                        # Simuler le pointage si les données correspondent au format attendu
                        if "Pointage - Utilisateur:" in decoded_data:
                            try:
                                user_part_start_index = decoded_data.find("Utilisateur:") + len("Utilisateur:")
                                user_part_end_index = decoded_data.find("|", user_part_start_index)
                                if user_part_end_index == -1:
                                    username = decoded_data[user_part_start_index:].strip()
                                else:
                                    username = decoded_data[user_part_start_index:user_part_end_index].strip()
                                
                                if username:
                                    self.record_attendance(username) # Appelle la fonction de pointage
                                else:
                                    messagebox.showwarning("Données QR invalides", "Le nom d'utilisateur n'a pas pu être extrait du QR Code.")
                            except Exception as parse_e:
                                messagebox.showerror("Erreur de parsing QR", f"Erreur lors de l'extraction du nom d'utilisateur: {parse_e}")
                        else:
                            messagebox.showinfo("QR Code lu", "Ce n'est pas un QR Code de pointage reconnu.")
                else:
                    self.decoded_qr_text.insert(tk.END, "Aucun QR Code détecté dans l'image.")
                
                self.decoded_qr_text.config(state="disabled")

            except FileNotFoundError:
                messagebox.showerror("Erreur", "Fichier non trouvé.")
            except Exception as e:
               messagebox.showerror("Erreur de lecture QR Code", f"Impossible de lire le QR Code: {e}\nAssurez-vous d'avoir installé 'pyzbar' (pip install pyzbar).")
    
    
#----Controle Véhicule---

    def create_controle_vehicule_tab(self):
        """
        Crée les widgets pour l'onglet "Contrôle Véhicule".
        """
        
        self.controle_vehicule_tab.grid_columnconfigure(0, weight=1)
        input_frame = tk.LabelFrame(self.controle_vehicule_tab, text="Rapport d'Inspection Véhicule",
                                     bg=self.bg_color_dashboard, fg=self.fg_color_text,
                                     font=self.font_subtitle, bd=2, relief="groove")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.inspection_entries = {}
        self.inspection_checkbox_vars = {}

        # Véhicule (Dropdown)
        vehicle_label = tk.Label(input_frame, text="Véhicule:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        vehicle_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")

        self.inspection_vehicle_options = []
        self.inspection_selected_vehicle_id = tk.StringVar()
        self.inspection_selected_vehicle_id.set(0)

        self.inspection_vehicle_option_menu = ttk.Combobox(input_frame, textvariable=self.inspection_selected_vehicle_id, state="readonly", font=self.font_label)
        self.inspection_vehicle_option_menu.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.inspection_vehicle_option_menu.bind("<<ComboboxSelected>>", self.on_inspection_vehicle_selected)
        self.populate_inspection_vehicle_options()

        # Date Inspection
        date_label = tk.Label(input_frame, text="Date Inspection:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        date_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        date_entry = DateEntry(input_frame, width=12, background="darkblue", foreground="white", borderwidth=2,
                               font=self.font_label, date_pattern='yyyy-mm-dd')
        date_entry.set_date(datetime.now().date())
        date_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.inspection_entries['date_inspection'] = date_entry

        # Kilométrage
        km_label = tk.Label(input_frame, text="Kilométrage:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        km_label.grid(row=2, column=0, padx=5, pady=2, sticky="w")
        km_entry = tk.Entry(input_frame, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text)
        km_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        self.inspection_entries['kilometrage'] = km_entry

        # État Général (Dropdown)
        etat_general_label = tk.Label(input_frame, text="État Général:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        etat_general_label.grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.etat_general_var = tk.StringVar()
        self.etat_general_combobox = ttk.Combobox(input_frame, textvariable=self.etat_general_var, values=self.etat_general_options, state="readonly", font=self.font_label)
        self.etat_general_combobox.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        if self.etat_general_options:
            self.etat_general_combobox.set(self.etat_general_options[0])

        # Niveau Carburant (%)
        carb_label = tk.Label(input_frame, text="Niveau Carburant (%):", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        carb_label.grid(row=4, column=0, padx=5, pady=2, sticky="w")
        carb_entry = tk.Entry(input_frame, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text)
        carb_entry.grid(row=4, column=1, padx=5, pady=2, sticky="ew")
        self.inspection_entries['niveau_carburant'] = carb_entry

        # Checkboxes pour les éléments à vérifier
        self.checkbox_items_config = [ # Stocker la configuration pour la validation
            ("Niveau d'huile OK", "huile_ok"),
            ("Liquide de refroidissement OK", "refroidissement_ok"),
            ("Feux avant/arrière OK", "feux_ok"),
            ("Clignotants OK", "clignotants_ok"),
            ("Pneus OK", "pneus_ok"),
            ("Carrosserie OK", "carrosserie_ok")
        ]
        row_idx = 5
        for text, key in self.checkbox_items_config:
            var = tk.BooleanVar(value=True) # Par défaut, tout est OK
            chk = tk.Checkbutton(input_frame, text=text, variable=var, bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label, selectcolor="#D5DBDB")
            chk.grid(row=row_idx, column=0, columnspan=2, padx=5, pady=2, sticky="w")
            self.inspection_checkbox_vars[key] = var
            row_idx += 1

        # Observations
        obs_label = tk.Label(input_frame, text="Observations:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        obs_label.grid(row=row_idx, column=0, padx=5, pady=2, sticky="w")
        obs_text = tk.Text(input_frame, height=3, width=30, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text)
        obs_text.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
        self.inspection_entries['observations'] = obs_text
        row_idx += 1

        button_frame = tk.Frame(self.controle_vehicule_tab, bg=self.bg_color_dashboard)
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        add_button = tk.Button(button_frame, text="Ajouter Rapport", command=self.add_inspection_report, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        update_button = tk.Button(button_frame, text="Modifier Rapport", command=self.update_inspection_report, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        delete_button = tk.Button(button_frame, text="Supprimer Incident", command=self.delete_inspection_report, font=self.font_button_text, bg="#E74C3C", fg=self.button_fg)
        clear_button = tk.Button(button_frame, text="Effacer", command=self.clear_inspection_fields, font=self.font_button_text, bg="#7F8C8D", fg=self.button_fg)

        add_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        update_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        delete_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        clear_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        self.inspection_tree = ttk.Treeview(self.controle_vehicule_tab, columns=(
                "ID", "Véhicule", "Date", "KM", "État Général", "Carburant", "Huile", "Refroid.", "Feux", "Clign.", "Pneus", "Carrosserie", "Observations"
        ), show="headings")
        self.inspection_tree.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        for col in self.inspection_tree["columns"]:
            self.inspection_tree.heading(col, text=col, anchor="center")
            self.inspection_tree.column(col, width=60, anchor="center")
        self.inspection_tree.column("ID", width=30)
        self.inspection_tree.column("Observations", width=120)
        self.inspection_tree.column("État Général", width=80)
        self.inspection_tree.column("Carburant", width=70)

        inspection_scrollbar = ttk.Scrollbar(self.controle_vehicule_tab, orient="vertical", command=self.inspection_tree.yview)
        inspection_scrollbar.grid(row=0, column=2, rowspan=2, sticky="ns")
        self.inspection_tree.configure(yscrollcommand=inspection_scrollbar.set)
        self.inspection_tree.bind("<<TreeviewSelect>>", self.load_inspection_into_fields)

        self.populate_inspection_treeview()

    def populate_inspection_vehicle_options(self):
        """
        Remplit le menu déroulant des véhicules avec les véhicules attribués au chauffeur connecté.
        """
        active_vehicles = get_active_vehicles()
        self.inspection_vehicle_options = []
        if active_vehicles:
            for veh_id, immatriculation in active_vehicles: # Assurez-vous que get_active_vehicles retourne (id, immat)
                self.inspection_vehicle_options.append((veh_id, immatriculation))
            
            self.inspection_vehicle_option_menu['values'] = [opt[1] for opt in self.inspection_vehicle_options]
            if self.inspection_vehicle_options:
                # Sélectionnez le premier véhicule par défaut si disponible
                self.inspection_selected_vehicle_id.set(self.inspection_vehicle_options[0][0])
                self.inspection_vehicle_option_menu.set(self.inspection_vehicle_options[0][1])
            else:
                self.inspection_selected_vehicle_id.set(0)
                self.inspection_vehicle_option_menu.set("Aucun véhicule disponible")
        else:
            self.inspection_vehicle_option_menu['values'] = []
            self.inspection_selected_vehicle_id.set(0)
            self.inspection_vehicle_option_menu.set("Aucun véhicule disponible")

    def on_inspection_vehicle_selected(self, event):
        """
        Met à jour l'ID du véhicule sélectionné pour l'inspection.
        """
        selected_immat = self.inspection_vehicle_option_menu.get()
        found_id = None
        for veh_id, veh_immat in self.inspection_vehicle_options:
            if veh_immat == selected_immat:
                found_id = veh_id
                break
        if found_id is not None:
            self.inspection_selected_vehicle_id.set(found_id)
        else:
            self.inspection_selected_vehicle_id.set(0)
            # Afficher une alerte si le véhicule n'est pas trouvé (cas peu probable si le combobox est readonly)
            messagebox.showwarning("Erreur de sélection", "Le véhicule sélectionné n'a pas pu être identifié.")

    def _format_date_for_treeview(self, date_raw):
        """Formate une date pour l'affichage dans le Treeview."""
        if isinstance(date_raw, datetime):
            return date_raw.strftime("%Y-%m-%d")
        elif isinstance(date_raw, str):
            try:
                # Tente de parser la chaîne si elle n'est pas déjà au bon format
                return datetime.strptime(date_raw, "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError:
                return str(date_raw) # Retourne la chaîne brute si le format est inattendu
        return ""

    def populate_inspection_treeview(self):
        """
        Remplit le Treeview des rapports d'inspection.
        """
        for item in self.inspection_tree.get_children():
            self.inspection_tree.delete(item)
        
        inspection_reports = get_all_vehicle_inspection_reports() 
        if inspection_reports:
            for report in inspection_reports:
                num_cols = len(report)
                
                # Assurez-vous que l'ordre des colonnes correspond à celui de votre base de données
                # et à la définition du Treeview. L'ordre dans votre DB semble être:
                # ID, user_id, vehicle_id, date, etat_general, carburant, observations,
                # huile, refroidissement, feux, clignotants, pneus, carrosserie, kilometrage
                report_id = report[0] if num_cols > 0 else ""
                vehicle_id_report = report[2] if num_cols > 2 else None
                date_inspection_raw = report[3] if num_cols > 3 else None
                etat_general = report[4] if num_cols > 4 else ""
                niveau_carburant = report[5] if num_cols > 5 else ""
                observations = report[6] if num_cols > 6 else ""
                huile_ok = report[7] if num_cols > 7 else False
                refroidissement_ok = report[8] if num_cols > 8 else False
                feux_ok = report[9] if num_cols > 9 else False
                clignotants_ok = report[10] if num_cols > 10 else False
                pneus_ok = report[11] if num_cols > 11 else False
                carrosserie_ok = report[12] if num_cols > 12 else False
                kilometrage = report[13] if num_cols > 13 else ""

                veh_immat = "N/A"
                if vehicle_id_report is not None:
                    vehicle_info = get_vehicle_by_id(vehicle_id_report)
                    veh_immat = vehicle_info[1] if vehicle_info and len(vehicle_info) > 1 else f"ID:{vehicle_id_report} (Introuvable)"

                formatted_date = self._format_date_for_treeview(date_inspection_raw)

                values_for_tree = (
                    report_id,
                    veh_immat,
                    formatted_date,
                    kilometrage,
                    etat_general,
                    niveau_carburant,
                    "Oui" if huile_ok else "Non",
                    "Oui" if refroidissement_ok else "Non",
                    "Oui" if feux_ok else "Non",
                    "Oui" if clignotants_ok else "Non",
                    "Oui" if pneus_ok else "Non",
                    "Oui" if carrosserie_ok else "Non",
                    observations
                )
                self.inspection_tree.insert("", "end", values=values_for_tree)

    def load_inspection_into_fields(self, event):
        """
        Charge les détails du rapport d'inspection sélectionné dans les champs de saisie.
        """
        selected_item = self.inspection_tree.focus()
        if not selected_item:
            # Réinitialiser si rien n'est sélectionné
            self.clear_inspection_fields() # Efface les champs si la sélection est perdue
            return

        values = self.inspection_tree.item(selected_item, 'values')
        self.selected_inspection_id = values[0] # L'ID du rapport est la première colonne

        self.clear_inspection_fields() # Efface avant de charger pour éviter les doublons

        vehicle_immatriculation = values[1]
        for veh_id, veh_immat in self.inspection_vehicle_options:
            if veh_immat == vehicle_immatriculation:
                self.inspection_selected_vehicle_id.set(veh_id)
                self.inspection_vehicle_option_menu.set(vehicle_immatriculation)
                break
        else: # Si l'immatriculation n'est pas trouvée (véhicule supprimé/désactivé)
            self.inspection_selected_vehicle_id.set(0)
            self.inspection_vehicle_option_menu.set(vehicle_immatriculation) # Affiche l'immat même si non sélectionnable
            messagebox.showwarning("Véhicule Inconnu", f"Le véhicule '{vehicle_immatriculation}' n'est plus disponible ou n'existe pas.")
        
        try:
            if values[2]: # Date
                self.inspection_entries['date_inspection'].set_date(datetime.strptime(values[2], "%Y-%m-%d").date())
            else:
                self.inspection_entries['date_inspection'].set_date(None)
        except ValueError:
            self.inspection_entries['date_inspection'].set_date(None)
            messagebox.showwarning("Erreur de Date", f"La date '{values[2]}' est invalide. Veuillez vérifier le format.")

        self.inspection_entries['kilometrage'].insert(0, values[3]) # Kilométrage
        self.etat_general_combobox.set(values[4]) # État Général
        self.inspection_entries['niveau_carburant'].insert(0, values[5]) # Niveau Carburant
        
        # Checkboxes
        self.inspection_checkbox_vars['huile_ok'].set(True if values[6] == "Oui" else False)
        self.inspection_checkbox_vars['refroidissement_ok'].set(True if values[7] == "Oui" else False)
        self.inspection_checkbox_vars['feux_ok'].set(True if values[8] == "Oui" else False)
        self.inspection_checkbox_vars['clignotants_ok'].set(True if values[9] == "Oui" else False)
        self.inspection_checkbox_vars['pneus_ok'].set(True if values[10] == "Oui" else False)
        self.inspection_checkbox_vars['carrosserie_ok'].set(True if values[11] == "Oui" else False)
        
        self.inspection_entries['observations'].delete("1.0", tk.END)
        self.inspection_entries['observations'].insert("1.0", values[12]) # Observations

    def validate_inspection_inputs(self):
        """
        Valide tous les champs de saisie et les checkboxes.
        Retourne True et les valeurs si valides, False et un message d'erreur sinon.
        """
        vehicle_id = self.inspection_selected_vehicle_id.get()
        date_inspection = self.inspection_entries['date_inspection'].get_date()
        kilometrage = self.inspection_entries['kilometrage'].get()
        etat_general = self.etat_general_var.get()
        niveau_carburant = self.inspection_entries['niveau_carburant'].get()
        observations = self.inspection_entries['observations'].get("1.0", tk.END).strip()

        # Validation des champs obligatoires non-checkbox
        if not vehicle_id or vehicle_id == "0": # Assurez-vous que 0 est la valeur par défaut pour "aucun véhicule"
            return False, "Veuillez sélectionner un véhicule."
        if not date_inspection:
            return False, "Veuillez sélectionner une date d'inspection."
        if not kilometrage:
            return False, "Veuillez entrer le kilométrage."
        if not etat_general:
            return False, "Veuillez sélectionner l'état général."
        if not niveau_carburant:
            return False, "Veuillez entrer le niveau de carburant."

        try:
            kilometrage = int(kilometrage)
            if kilometrage < 0:
                return False, "Le kilométrage ne peut pas être négatif."
        except ValueError:
            return False, "Le kilométrage doit être un nombre entier valide."
        
        try:
            niveau_carburant = int(niveau_carburant)
            if not (0 <= niveau_carburant <= 100):
                return False, "Le niveau de carburant doit être entre 0 et 100."
        except ValueError:
            return False, "Le niveau de carburant doit être un nombre entier valide."
        
        # Validation des checkboxes (vérifie si elles sont toutes cochées "OK")
        missing_checks = []
        for text, key in self.checkbox_items_config:
            if not self.inspection_checkbox_vars[key].get():
                missing_checks.append(text)
        
        if missing_checks:
            message = "Les contrôles suivants ne sont pas cochés comme 'OK' :\n" + "\n".join(missing_checks)
            messagebox.showwarning("Vérifications manquantes", message)
            # Décision: on laisse l'utilisateur valider s'il le souhaite, ou on bloque ?
            # Pour l'instant, je vais demander confirmation pour les enregistrer tel quel.
            if not messagebox.askyesno("Confirmer l'enregistrement", "Certains contrôles ne sont pas 'OK'. Voulez-vous quand même enregistrer ce rapport ?"):
                return False, "Opération annulée par l'utilisateur."
        
        # Récupération des valeurs des checkboxes
        huile_ok = self.inspection_checkbox_vars['huile_ok'].get()
        refroidissement_ok = self.inspection_checkbox_vars['refroidissement_ok'].get()
        feux_ok = self.inspection_checkbox_vars['feux_ok'].get()
        clignotants_ok = self.inspection_checkbox_vars['clignotants_ok'].get()
        pneus_ok = self.inspection_checkbox_vars['pneus_ok'].get()
        carrosserie_ok = self.inspection_checkbox_vars['carrosserie_ok'].get()

        return True, {
            "vehicle_id": vehicle_id,
            "date_inspection": date_inspection,
            "kilometrage": kilometrage,
            "etat_general": etat_general,
            "niveau_carburant": niveau_carburant,
            "observations": observations,
            "huile_ok": huile_ok,
            "refroidissement_ok": refroidissement_ok,
            "feux_ok": feux_ok,
            "clignotants_ok": clignotants_ok,
            "pneus_ok": pneus_ok,
            "carrosserie_ok": carrosserie_ok
        }

    def add_inspection_report(self):
        """
        Ajoute un nouveau rapport d'inspection à la base de données.
        """
        is_valid, data_or_message = self.validate_inspection_inputs()
        if not is_valid:
            messagebox.showwarning("Validation échouée", data_or_message)
            return

        # Si la validation réussit, data_or_message contient le dictionnaire de données
        data = data_or_message

        # Mettre à jour le kilométrage du véhicule (avant l'ajout du rapport)
        update_vehicle_km(data['vehicle_id'], data['kilometrage']) 

        success, message = add_vehicle_inspection_report(
            self.logged_in_user_id, data['vehicle_id'], data['date_inspection'], data['etat_general'],
            data['niveau_carburant'], data['observations'], data['huile_ok'], data['refroidissement_ok'],
            data['feux_ok'], data['clignotants_ok'], data['pneus_ok'], data['carrosserie_ok'], data['kilometrage']
        )
        if success:
            messagebox.showinfo("Succès", message)
            self.populate_inspection_treeview()
            self.clear_inspection_fields()
        else:
            messagebox.showerror("Erreur", message)

    def update_inspection_report(self):
        """
        Met à jour un rapport d'inspection existant.
        """
        if not hasattr(self, 'selected_inspection_id') or not self.selected_inspection_id:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner un rapport d'inspection à modifier.")
            return

        is_valid, data_or_message = self.validate_inspection_inputs()
        if not is_valid:
            messagebox.showwarning("Validation échouée", data_or_message)
            return
        
        data = data_or_message
        report_id = self.selected_inspection_id

        # Mettre à jour le kilométrage du véhicule
        update_vehicle_km(data['vehicle_id'], data['kilometrage'])

        success, message = update_vehicle_inspection_report(
            report_id, self.logged_in_user_id, data['vehicle_id'], data['date_inspection'],
            data['etat_general'], data['niveau_carburant'], data['observations'],
            data['huile_ok'], data['refroidissement_ok'], data['feux_ok'],
            data['clignotants_ok'], data['pneus_ok'], data['carrosserie_ok'], data['kilometrage']
        )
        if success:
            messagebox.showinfo("Succès", message)
            self.populate_inspection_treeview()
            self.clear_inspection_fields()
        else:
            messagebox.showerror("Erreur", message)

    def delete_inspection_report(self):
        """
        Supprime un rapport d'inspection.
        """
        if not hasattr(self, 'selected_inspection_id') or not self.selected_inspection_id:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner un rapport d'inspection à supprimer.")
            return

        if messagebox.askyesno("Confirmer la suppression", "Êtes-vous sûr de vouloir supprimer ce rapport d'inspection ? Cette action est irréversible."):
            success, message = delete_vehicle_inspection_report(self.selected_inspection_id)
            if success:
                messagebox.showinfo("Succès", message)
                self.populate_inspection_treeview()
                self.clear_inspection_fields()
                 # Réinitialiser l'ID sélectionné
            else:
                messagebox.showerror("Erreur", message)

    def clear_inspection_fields(self):
        """
        Efface les champs de saisie de l'onglet Contrôle Véhicule.
        """
        self.populate_inspection_vehicle_options() # Pour réinitialiser le combobox du véhicule
        self.inspection_entries['date_inspection'].set_date(datetime.now().date())
        self.inspection_entries['kilometrage'].delete(0, tk.END)
        if self.etat_general_options:
            self.etat_general_combobox.set(self.etat_general_options[0])
        else:
            self.etat_general_combobox.set("")
        self.inspection_entries['niveau_carburant'].delete(0, tk.END)
        self.inspection_entries['niveau_carburant'].insert(0, "100") # Valeur par défaut
        self.inspection_entries['observations'].delete("1.0", tk.END)
        for key in self.inspection_checkbox_vars:
            self.inspection_checkbox_vars[key].set(True) # Réinitialiser toutes les checkboxes à "OK"
         # Réinitialiser l'ID sélectionné

     # --- Onglet Déclaration de Problème ---
    def create_declaration_probleme_tab(self):
        """
        Crée les widgets pour l'onglet "Déclaration de Problème".
        """
        self.declaration_probleme_tab.grid_columnconfigure(0, weight=1)
        frame = tk.Frame(self.declaration_probleme_tab)

        input_frame = tk.LabelFrame(self.declaration_probleme_tab, text="Déclarer un Incident",
                            bg=self.bg_color_dashboard, fg=self.fg_color_text,
                            font=self.font_subtitle, bd=2, relief="groove")

        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.incident_entries = {}

        vehicle_label = tk.Label(input_frame, text="Véhicule:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        vehicle_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        
        self.incident_vehicle_options = []
        self.incident_selected_vehicle_id = tk.StringVar()
        self.incident_selected_vehicle_id.set(0)

        self.incident_vehicle_option_menu = ttk.Combobox(input_frame, textvariable=self.incident_selected_vehicle_id, state="readonly", font=self.font_label)
        self.incident_vehicle_option_menu.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.incident_vehicle_option_menu.bind("<<ComboboxSelected>>", self.on_incident_vehicle_selected)
        self.populate_incident_vehicle_options()

        type_incident_label = tk.Label(input_frame, text="Type d'incident:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        type_incident_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.incident_type_var = tk.StringVar()
        self.incident_type_combobox = ttk.Combobox(input_frame, textvariable=self.incident_type_var, values=self.incident_types, state="readonly", font=self.font_label)
        self.incident_type_combobox.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        if self.incident_types:
            self.incident_type_combobox.set(self.incident_types[0])

        gravite_label = tk.Label(input_frame, text="Gravité:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        gravite_label.grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.incident_gravite_var = tk.StringVar()
        self.incident_gravite_combobox = ttk.Combobox(input_frame, textvariable=self.incident_gravite_var, values=["Mineure", "Modérée", "Majeure", "Critique"], state="readonly", font=self.font_label)
        self.incident_gravite_combobox.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        if ["Mineure", "Modérée", "Majeure", "Critique"]:
            self.incident_gravite_combobox.set("Mineure")


        fields = [
            ("Date de l'incident:", "date_incident", True),
            ("Description:", "description", False, "text"),
            ("Kilométrage incident:", "kilometrage_incident", False)
        ]
        
        row_idx = 3
        for label_text, key, *args in fields:
            lbl = tk.Label(input_frame, text=label_text, bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
            lbl.grid(row=row_idx, column=0, padx=5, pady=2, sticky="w")
            
            if "True" in [str(a) for a in args]:
                entry = DateEntry(input_frame, width=12, background="darkblue", foreground="white", borderwidth=2,
                                  font=self.font_label, date_pattern='yyyy-mm-dd')
                entry.set_date(datetime.now().date())
                entry.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
                self.incident_entries[key] = entry
            elif "text" in args:
                entry = tk.Text(input_frame, height=3, width=30, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text)
                entry.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
                self.incident_entries[key] = entry
            else:
                entry = tk.Entry(input_frame, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text)
                entry.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
                self.incident_entries[key] = entry
            row_idx += 1

        button_frame = tk.Frame(self.declaration_probleme_tab, bg=self.bg_color_dashboard)
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        add_button = tk.Button(button_frame, text="Ajouter Incident", command=self.add_incident_report, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        update_button = tk.Button(button_frame, text="Modifier Incident", command=self.update_incident_report, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        delete_button = tk.Button(button_frame, text="Supprimer Incident", command=self.delete_incident_report, font=self.font_button_text, bg="#E74C3C", fg=self.button_fg)
        clear_button = tk.Button(button_frame, text="Effacer", command=self.clear_incident_fields, font=self.font_button_text, bg="#7F8C8D", fg=self.button_fg)

        add_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        update_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        delete_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        clear_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        self.incident_tree = ttk.Treeview(self.declaration_probleme_tab, columns=(
            "ID", "Véhicule", "Date", "Type", "Description", "Gravité", "KM Incident"
        ), show="headings")
        self.incident_tree.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        for col in self.incident_tree["columns"]:
            self.incident_tree.heading(col, text=col, anchor="center")
            self.incident_tree.column(col, width=80, anchor="center")
        self.incident_tree.column("ID", width=30)
        self.incident_tree.column("Description", width=150)

        incident_scrollbar = ttk.Scrollbar(self.declaration_probleme_tab, orient="vertical", command=self.incident_tree.yview)
        incident_scrollbar.grid(row=0, column=2, rowspan=2, sticky="ns")
        self.incident_tree.configure(yscrollcommand=incident_scrollbar.set)
        self.incident_tree.bind("<<TreeviewSelect>>", self.load_incident_report_into_fields)
        self.populate_incident_reports_treeview()

    def populate_incident_vehicle_options(self):
        """
        Remplit le menu déroulant des véhicules pour l'onglet Incident avec les véhicules attribués au chauffeur.
        """
        # Pour le chauffeur, on pourrait limiter aux véhicules qui lui sont actuellement attribués
        # Pour cet exemple, on utilise tous les véhicules actifs, comme dans le ResponsableDashboard
        active_vehicles = get_active_vehicles()
        self.incident_vehicle_options = []
        if active_vehicles:
            for veh_id, immatriculation, *rest in active_vehicles:
                self.incident_vehicle_options.append((veh_id, immatriculation))
            
            self.incident_vehicle_option_menu['values'] = [opt[1] for opt in self.incident_vehicle_options]
            if self.incident_vehicle_options:
                self.incident_selected_vehicle_id.set(self.incident_vehicle_options[0][0])
                self.incident_vehicle_option_menu.set(self.incident_vehicle_options[0][1])
            else:
                self.incident_selected_vehicle_id.set(0)
                self.incident_vehicle_option_menu.set("Aucun véhicule disponible")
        else:
            self.incident_vehicle_option_menu['values'] = []
            self.incident_selected_vehicle_id.set(0)
            self.incident_vehicle_option_menu.set("Aucun véhicule disponible")

    def on_incident_vehicle_selected(self, event):
        """
        Met à jour l'ID du véhicule sélectionné pour l'incident.
        """
        selected_immat = self.incident_vehicle_option_menu.get()
        found_id = None
        for veh_id, veh_immat in self.incident_vehicle_options:
            if veh_immat == selected_immat:
                found_id = veh_id
                break
        if found_id is not None:
            self.incident_selected_vehicle_id.set(found_id)
        else:
            self.incident_selected_vehicle_id.set(0)

    def populate_incident_reports_treeview(self):
        """
        Remplit le Treeview des rapports d'incident pour le chauffeur connecté.
        """
        for item in self.incident_tree.get_children():
            self.incident_tree.delete(item)
        
        # Filtrer les incidents par l'utilisateur connecté
        all_incident_reports = get_all_incident_reports()
        
        # DEBUG: Print all incident reports to check order
        print(f"DEBUG: All incident reports from DB: {all_incident_reports}")

        chauffeur_incident_reports = [
            report for report in all_incident_reports if report[1] == self.logged_in_user_id
        ]

        if chauffeur_incident_reports:
            for report in chauffeur_incident_reports:
                num_cols = len(report)

                # db_manager returns: ir.id (0), ir.user_id (1), ir.vehicle_id (2), ir.date_incident (3), ir.type_probleme (4), ir.description (5), ir.gravite (6), ir.kilometrage_incident (7)
                ir_id = report[0]
                # user_id_ir = report[1] # Not displayed
                vehicle_id_ir = report[2]
                date_incident_raw = report[3]
                type_probleme = report[4]
                description_ir = report[5]
                gravite = report[6]
                kilometrage_incident = report[7]
                
                veh_immat = "N/A"
                if vehicle_id_ir is not None:
                    vehicle_info = get_vehicle_by_id(vehicle_id_ir)
                    veh_immat = vehicle_info[1] if vehicle_info and len(vehicle_info) > 1 else f"ID:{vehicle_id_ir} (Introuvable)"

                formatted_date = self._format_date_for_treeview(date_incident_raw)

                values_for_tree = (
                    ir_id,
                    veh_immat,
                    formatted_date,
                    type_probleme,
                    description_ir,
                    gravite,
                    kilometrage_incident
                )
                self.incident_tree.insert("", "end", values=values_for_tree)
        else:
            print("Aucun rapport d'incident trouvé pour ce chauffeur.")


    def load_incident_report_into_fields(self, event):
        """
        Charge les détails du rapport d'incident sélectionné dans les champs de saisie
        en récupérant les données complètes de la base de données.
        """
        selected_item = self.incident_tree.focus()
        if not selected_item:
            return

        values_from_tree = self.incident_tree.item(selected_item, 'values')
        print(f"DEBUG: Selected incident ID from Treeview: {values_from_tree[0]}") # New print
        self.selected_incident_id = values_from_tree[0] # L'ID est toujours le premier élément
        print(f"DEBUG: self.selected_incident_id set to: {self.selected_incident_id}") # New print

        # Récupérer l'entrée complète de la base de données pour assurer la cohérence
        incident_report_data = get_incident_report_by_id(self.selected_incident_id)
        print(f"DEBUG: Data fetched by get_incident_report_by_id for ID {self.selected_incident_id}: {incident_report_data}") # New print

        if not incident_report_data:
            messagebox.showwarning("Données introuvables", "Impossible de récupérer les détails de ce rapport d'incident.")
            self.clear_incident_fields()
            return
        
        # Assurez-vous que l'ordre des éléments dans incident_report_data correspond à votre schéma de base de données
        # Exemple d'ordre attendu de get_incident_report_by_id:
        # (id, user_id, vehicle_id, date_incident, type_probleme, description, gravite, kilometrage_incident)

        self.clear_incident_fields() # Effacer avant de charger

        vehicle_id_from_db = incident_report_data[2]
        veh_immat = "N/A"
        for veh_id, immat in self.incident_vehicle_options:
            if veh_id == vehicle_id_from_db:
                veh_immat = immat
                break
        self.incident_selected_vehicle_id.set(vehicle_id_from_db)
        self.incident_vehicle_option_menu.set(veh_immat)
        
        try:
            date_incident_db = incident_report_data[3]
            if date_incident_db:
                self.incident_entries['date_incident'].set_date(self._format_date_for_treeview(date_incident_db))
            else:
                self.incident_entries['date_incident'].set_date(None)
        except ValueError:
            self.incident_entries['date_incident'].set_date(None)
            print(f"Warning: Impossible de convertir la chaîne de date '{incident_report_data[3]}' pour date_incident. Réinitialisation à vide.")

        self.incident_type_combobox.set(incident_report_data[4])
        self.incident_entries['description'].delete("1.0", tk.END)
        self.incident_entries['description'].insert("1.0", incident_report_data[5])
        self.incident_gravite_combobox.set(incident_report_data[6])
        self.incident_entries['kilometrage_incident'].delete(0, tk.END)
        self.incident_entries['kilometrage_incident'].insert(0, str(incident_report_data[7]))

    def add_incident_report(self):
        """
        Ajoute un nouveau rapport d'incident à la base de données.
        """
        if self.logged_in_user_id is None:
            messagebox.showerror("Erreur d'utilisateur", "ID utilisateur non disponible. Veuillez vous reconnecter.")
            return

        vehicle_id = self.incident_selected_vehicle_id.get()
        date_incident = self.incident_entries['date_incident'].get_date()
        type_incident = self.incident_type_combobox.get()
        description = self.incident_entries['description'].get("1.0", tk.END).strip()
        gravite = self.incident_gravite_combobox.get()
        kilometrage_incident_str = self.incident_entries['kilometrage_incident'].get()
        kilometrage_incident = int(kilometrage_incident_str) if kilometrage_incident_str else None

        if not all([vehicle_id, date_incident, type_incident, description, gravite]):
            messagebox.showwarning("Champs requis", "Veuillez remplir tous les champs obligatoires.")
            return

        try:
            success, message = add_incident_report_to_db(
                self.logged_in_user_id, vehicle_id, date_incident, type_incident, description, gravite,
                kilometrage_incident
            )

            if success:
                messagebox.showinfo("Succès", message)
                self.populate_incident_reports_treeview()
                self.clear_incident_fields()
            else:
                messagebox.showerror("Erreur", message)
        except Exception as e:
            messagebox.showerror("Erreur d'ajout d'incident", f"Une erreur est survenue lors de l'ajout: {e}")


    def update_incident_report(self):
        """
        Met à jour un rapport d'incident existant dans la base de données.
        """
        if self.selected_incident_id is None:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner un rapport d'incident à modifier.")
            return
        incident_id = self.selected_incident_id
        print(f"DEBUG: Attempting to update incident report with ID: {incident_id}") # New print

        if self.logged_in_user_id is None:
            messagebox.showerror("Erreur d'utilisateur", "ID utilisateur non disponible. Veuillez vous reconnecter.")
            return

        vehicle_id = self.incident_selected_vehicle_id.get()
        date_incident = self.incident_entries['date_incident'].get_date()
        type_incident = self.incident_type_combobox.get()
        description = self.incident_entries['description'].get("1.0", tk.END).strip()
        gravite = self.incident_gravite_combobox.get()
        kilometrage_incident_str = self.incident_entries['kilometrage_incident'].get()
        kilometrage_incident = int(kilometrage_incident_str) if kilometrage_incident_str else None
        
        if not all([vehicle_id, date_incident, type_incident, description, gravite]):
            messagebox.showwarning("Champs requis", "Veuillez remplir tous les champs obligatoires.")
            return
        
        try:
            success, message = update_incident_report_in_db(
                incident_id, self.logged_in_user_id, vehicle_id, date_incident, type_incident, description, gravite,
                kilometrage_incident
            )

            if success:
                messagebox.showinfo("Succès", message)
                self.populate_incident_reports_treeview()
                self.clear_incident_fields()
            else:
                messagebox.showerror("Erreur", message)
        except Exception as e:
            messagebox.showerror("Erreur de modification d'incident", f"Une erreur est survenue lors de la modification: {e}")

    def delete_incident_report(self):
        """
        Supprime un rapport d'incident de la base de données.
        """
        if self.selected_incident_id is None:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner un rapport d'incident à supprimer.")
            return
        incident_id = self.selected_incident_id
        print(f"DEBUG: Attempting to delete incident report with ID: {incident_id}") # New print
        if messagebox.askyesno("Confirmer la suppression", f"Êtes-vous sûr de vouloir supprimer le rapport d'incident (ID: {incident_id})?"):
            try:
                success, message = delete_incident_report_from_db(incident_id)
                if success:
                    messagebox.showinfo("Succès", message)
                    self.populate_incident_reports_treeview()
                    self.clear_incident_fields()
                    
                else:
                    messagebox.showerror("Erreur", message)
            except Exception as e:
                messagebox.showerror("Erreur de suppression", f"Une erreur est survenue lors de la suppression: {e}")

    def clear_incident_fields(self):
        """
        Efface les champs de saisie de l'onglet Déclaration de Problème.
        """
        self.populate_incident_vehicle_options()
        self.incident_entries['date_incident'].set_date(datetime.now().date())
        
        if self.incident_types:
            self.incident_type_combobox.set(self.incident_types[0])
        else:
            self.incident_type_combobox.set("")

        self.incident_entries['description'].delete("1.0", tk.END)
        
        if ["Mineure", "Modérée", "Majeure", "Critique"]:
            self.incident_gravite_combobox.set("Mineure")
        
        self.incident_entries['kilometrage_incident'].delete(0, tk.END)
        

    # --- Onglet Alertes Documents ---
    def create_alertes_documents_tab(self):
        """
        Crée les widgets pour l'onglet "Alertes Documents".
        """
        self.alertes_documents_tab.grid_columnconfigure(0, weight=1)
        self.alertes_documents_tab.grid_rowconfigure(0, weight=0)
        self.alertes_documents_tab.grid_rowconfigure(1, weight=1)

        filter_frame = tk.LabelFrame(self.alertes_documents_tab, text="Recherche Documents",
                                     bg=self.bg_color_dashboard, fg=self.fg_color_text,
                                     font=self.font_label, bd=2, relief="groove")
        filter_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        filter_frame.grid_columnconfigure(1, weight=1)

        tk.Label(filter_frame, text="ID Véhicule:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label).grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.document_search_vehicle_id_entry = tk.Entry(filter_frame, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text)
        self.document_search_vehicle_id_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        search_button = tk.Button(filter_frame, text="Rechercher Documents", command=self.search_vehicle_documents, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        search_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Cadre pour les alertes
        alerts_label_frame = tk.LabelFrame(self.alertes_documents_tab, text="Alertes Documents Expirant Bientôt",
                                            bg=self.bg_color_dashboard, fg=self.fg_color_text,
                                            font=self.font_subtitle, bd=2, relief="groove")
        alerts_label_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        alerts_label_frame.grid_columnconfigure(0, weight=1)
        alerts_label_frame.grid_rowconfigure(0, weight=1)

        self.alerts_tree = ttk.Treeview(alerts_label_frame, columns=(
            "Véhicule", "Type Document", "Date Expiration", "Jours Restants"
        ), show="headings")
        self.alerts_tree.grid(row=0, column=0, sticky="nsew")

        for col in self.alerts_tree["columns"]:
            self.alerts_tree.heading(col, text=col, anchor="center")
            self.alerts_tree.column(col, width=100, anchor="center")
        self.alerts_tree.column("Date Expiration", width=120)
        self.alerts_tree.column("Jours Restants", width=100)

        alerts_scrollbar = ttk.Scrollbar(alerts_label_frame, orient="vertical", command=self.alerts_tree.yview)
        alerts_scrollbar.grid(row=0, column=1, sticky="ns")
        self.alerts_tree.configure(yscrollcommand=alerts_scrollbar.set)

        self.populate_document_alerts()

    def populate_document_alerts(self):
        """
        Popule le Treeview des alertes de documents.
        """
        for item in self.alerts_tree.get_children():
            self.alerts_tree.delete(item)
        
        all_vehicles = get_active_vehicles() # Gets (id, immatriculation)
        
        for veh_id, immatriculation in all_vehicles:
            # Call the specific function to get expiry dates for this vehicle
            document_dates = get_vehicle_document_expiry_dates(veh_id) 
            
            if document_dates:
                # document_dates is (date_assurance, date_visite_technique, date_carte_rose, immatriculation_from_db)
                # We already have immatriculation from all_vehicles, so we use document_dates[0], [1], [2]
                doc_types_map = {
                    "Assurance": document_dates[0],
                    "Visite Technique": document_dates[1],
                    "Carte Rose": document_dates[2]
                }

                for doc_type, expiry_date_raw in doc_types_map.items():
                    if expiry_date_raw:
                        try:
                            # Ensure expiry_date_raw is a date object or string parsable to date
                            if isinstance(expiry_date_raw, date):
                                expiry_date = expiry_date_raw
                            elif isinstance(expiry_date_raw, datetime):
                                expiry_date = expiry_date_raw.date()
                            else: # Assume it's a string, try to parse
                                expiry_date = datetime.strptime(str(expiry_date_raw), "%Y-%m-%d").date()
                            
                            today = date.today()
                            days_left = (expiry_date - today).days

                            expiry_date_str = expiry_date.strftime("%Y-%m-%d")

                            if 0 <= days_left <= 30: # Alerte si moins de 30 jours restants
                                self.alerts_tree.insert("", "end", values=(
                                    immatriculation, doc_type, expiry_date_str, f"{days_left} jours"
                                ), tags=('alert',))
                            elif days_left < 0: # Expiré
                                self.alerts_tree.insert("", "end", values=(
                                    immatriculation, doc_type, expiry_date_str, "Expiré"
                                ), tags=('expired',))
                            else: # Plus de 30 jours restants
                                self.alerts_tree.insert("", "end", values=(
                                    immatriculation, doc_type, expiry_date_str, f"{days_left} jours"
                                ))
                        except ValueError:
                            print(f"Warning: Could not parse expiry date for {doc_type} of {immatriculation}: {expiry_date_raw}")
                            self.alerts_tree.insert("", "end", values=(
                                immatriculation, doc_type, str(expiry_date_raw), "Date invalide"
                            ), tags=('error',))
                    else:
                        self.alerts_tree.insert("", "end", values=(
                            immatriculation, doc_type, "N/A", "Non renseigné"
                        ))
        
        # Appliquer des tags pour le style (ex: couleur rouge pour expiré)
        self.alerts_tree.tag_configure('alert', background='#FADBD8', foreground='#C0392B') # Rouge clair pour alerte
        self.alerts_tree.tag_configure('expired', background='#F1948A', foreground='#7B241C', font=self.font_button_text) # Rouge plus foncé pour expiré
        self.alerts_tree.tag_configure('error', background='#F5B7B1', foreground='#641E16') # Rouge pour erreur de parsing

    def search_vehicle_documents(self):
        """
        Recherche et affiche les documents d'un véhicule spécifique.
        """
        vehicle_id_to_search = self.document_search_vehicle_id_entry.get().strip()
        if not vehicle_id_to_search:
            messagebox.showwarning("Champ vide", "Veuillez entrer un ID de véhicule.")
            return
        
        try:
            vehicle_id_to_search = int(vehicle_id_to_search)
        except ValueError:
            messagebox.showwarning("ID Invalide", "L'ID du véhicule doit être un nombre.")
            return

        vehicle_info = get_vehicle_by_id(vehicle_id_to_search)
        if not vehicle_info:
            messagebox.showinfo("Véhicule introuvable", f"Aucun véhicule trouvé avec l'ID: {vehicle_id_to_search}")
            return
        
        # Effacer les résultats précédents
        for item in self.alerts_tree.get_children():
            self.alerts_tree.delete(item)

        # Directement appeler la fonction pour un seul véhicule
        document_dates = get_vehicle_document_expiry_dates(vehicle_id_to_search) 

        if document_dates:
            veh_immat = vehicle_info[1] # Use immatriculation from vehicle_info, not document_dates[3] as it might be None if document_dates is from a different source.
            
            doc_types_map = {
                "Assurance": document_dates[0],
                "Visite Technique": document_dates[1],
                "Carte Rose": document_dates[2]
            }

            for doc_type, expiry_date_raw in doc_types_map.items():
                if expiry_date_raw:
                    try:
                        if isinstance(expiry_date_raw, date):
                            expiry_date = expiry_date_raw
                        elif isinstance(expiry_date_raw, datetime):
                            expiry_date = expiry_date_raw.date()
                        else:
                            expiry_date = datetime.strptime(str(expiry_date_raw), "%Y-%m-%d").date()
                        
                        today = date.today()
                        days_left = (expiry_date - today).days
                        expiry_date_str = expiry_date.strftime("%Y-%m-%d")

                        status = f"{days_left} jours restants"
                        tag = ''
                        if days_left < 0:
                            status = "Expiré"
                            tag = 'expired'
                        elif 0 <= days_left <= 30:
                            tag = 'alert'

                        self.alerts_tree.insert("", "end", values=(
                            veh_immat, doc_type, expiry_date_str, status
                        ), tags=(tag,))
                    except ValueError:
                        self.alerts_tree.insert("", "end", values=(
                            veh_immat, doc_type, str(expiry_date_raw), "Date invalide"
                        ), tags=('error',))
                else:
                    self.alerts_tree.insert("", "end", values=(
                        veh_immat, doc_type, "N/A", "Non renseigné"
                    ))
            self.alerts_tree.tag_configure('error', background='#F5B7B1', foreground='#641E16') # Rouge pour erreur de parsing
        else:
            messagebox.showinfo("Aucun document", f"Aucun document trouvé pour le véhicule ID: {vehicle_id_to_search}")

    def clear_document_search_fields(self):
        """
        Efface les champs de recherche de documents et rafraîchit les alertes.
        """
        self.document_search_vehicle_id_entry.delete(0, tk.END)
        self.populate_document_alerts() # Recharger toutes les alertes

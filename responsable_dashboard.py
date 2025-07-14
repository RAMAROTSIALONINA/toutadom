import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import tkinter.font as tkFont
from tkcalendar import DateEntry
from datetime import datetime, date, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import os
from tkinter import filedialog
from PIL import Image, ImageTk # Assurez-vous que Pillow est importé
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np # Utile pour certains types de données, mais pas toujours obligatoire
import csv
import tempfile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader



# Import des fonctions nécessaires de db_manager (assurez-vous que db_manager.py est à jour et contient toutes ces fonctions)
from db_manager import (
    get_all_chauffeurs_and_responsables, get_active_vehicles,
    add_attribution_to_db, end_attribution_in_db, get_all_attributions, get_attribution_by_id,
    update_attribution_in_db,
    add_maintenance_to_db, get_all_maintenances, update_maintenance_in_db, delete_maintenance_from_db, get_maintenance_by_id,
    add_fuel_entry_to_db, get_all_fuel_entries, update_fuel_entry_in_db, delete_fuel_entry_from_db, get_fuel_entry_by_id,
    add_incident_report_to_db, get_all_incident_reports, update_incident_report_in_db, delete_incident_report_from_db, get_incident_report_by_id,
    get_vehicle_by_id, get_user_by_id,
    update_vehicle_status_and_km,
    get_all_vehicles,
    get_all_vehicle_inspection_reports,
    get_attribution_by_chauffeur_id
)

class ResponsableDashboard:
    def __init__(self, master, parent_frame, app_manager_instance, user_id, username, user_role, user_fullname):
        self.parent_frame = parent_frame
        self.app_manager_instance = app_manager_instance
        self.master = master
        
        self.logged_in_user_id = user_id
        self.logged_in_username = username
        self.logged_in_user_role = user_role
        self.logged_in_user_fullname = user_fullname
        self.stat_driver_var = tk.StringVar(value="Tous")

        # Polices
        self.font_title = tkFont.Font(family="Helvetica", size=20, weight="bold")
        self.font_subtitle = tkFont.Font(family="Helvetica", size=14, weight="bold")
        self.font_label = tkFont.Font(family="Helvetica", size=10)
        self.font_button_text = tkFont.Font(family="Helvetica", size=10, weight="bold")
        self.font_welcome_title = tkFont.Font(family="Helvetica", size=24, weight="bold")

        # Thème clair (blanc)
        self.bg_color_main = "#F0F0F0" # Couleur de fond principale, comme un gris très clair
        self.bg_color_dashboard = "#FFFFFF" # Couleur de fond pour le tableau de bord / onglets
        self.fg_color_text = "#2C3E50" # Couleur du texte (texte foncé sur fond clair)
        self.entry_bg = "#F8F9F9" # Fond des champs de saisie
        self.entry_fg = "#2C3E50" # Texte des champs de saisie
        self.button_bg = "#E0E0E0" # Fond des boutons
        self.button_fg = "#000000" # Texte des boutons
        self.highlight_color = "#3498DB" # Bleu pour les surlignages, sélections actives
        self.accent_color = "#E74C3C" # Rouge pour les boutons d'action importants ou pour exporter

        self.selected_item_bg = "#D6EAF8" # Utilisé pour les Treeviews ou listes
        # Assurez-vous également que cette partie de configuration de style TTK est présente
        # et correctement placée dans votre __init__
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=self.bg_color_main)
        style.configure('TLabel', background=self.bg_color_main, foreground=self.fg_color_text, font=self.font_label)
        style.configure('TButton', background=self.button_bg, foreground=self.button_fg, font=self.font_button_text, borderwidth=1)
        style.map('TButton', background=[('active', self.highlight_color)])
        style.configure('TCombobox', fieldbackground=self.entry_bg, background=self.entry_bg, foreground=self.entry_fg, font=self.font_label)
        style.map('TCombobox', fieldbackground=[('readonly', self.entry_bg)], selectbackground=[('readonly', self.highlight_color)], selectforeground=[('readonly', self.entry_fg)])
        style.configure('TNotebook', background=self.bg_color_main, tabposition='wn')
        style.configure('TNotebook.Tab', background=self.button_bg, foreground=self.button_fg, font=self.font_button_text, padding=[10, 5])
        style.map('TNotebook.Tab', background=[('selected', self.highlight_color)], foreground=[('selected', self.button_fg)])

       

        # Répertoire pour les exports PDF
        self.pdf_export_dir = os.path.join(self.app_manager_instance.app_root_dir, "PDF_Exports") 
        os.makedirs(self.pdf_export_dir, exist_ok=True) 

        # Chemin vers le logo pour le PDF et l'interface
        script_dir = os.path.dirname(__file__)
        self.logo_path = os.path.join(script_dir, "Toutadom.png") 
        if not os.path.exists(self.logo_path):
            messagebox.showwarning("Fichier manquant", f"Le fichier logo 'Toutadom.png' est introuvable à l'emplacement : {self.logo_path}")
            self.logo_path = None

        self.maintenance_types = ["Vidange", "Freins", "Pneus", "Moteur", "Carrosserie", "Climatisation", "Autre"]
        self.incident_types = ["Panne mécanique", "Accident", "Problème électrique", "Pneu crevé", "Vandalisme", "Autre"]
        self.gravite_types = ["Mineure", "Modérée", "Majeure", "Critique"]
        self.fuel_types = ["Essence", "Diesel", "GPL", "Électrique", "Autre"]
        self.etat_general_options = ["Excellent", "Bon", "Moyen", "Mauvais"]

        self.vehicles_data = []
    
        self.maintenance_selected_vehicle_id = tk.StringVar()
        self.maintenance_selected_vehicle_id.set("") 
        self.selected_maintenance_id =None


        # IMPORTANT: Initialisation des variables Tkinter pour l'onglet Historique DÉPLACÉE ICI
        self.history_selected_vehicle_display = tk.StringVar(value="Tous les véhicules") # <--- DÉPLACÉ
        self.history_selected_vehicle_id = tk.StringVar(value="Tous")                   # <--- DÉPLACÉ
        self.history_event_types = ["Tous", "Attribution", "Maintenance", "Carburant", "Incident", "Inspection"]
        self.history_selected_event_type = tk.StringVar(value="Tous") 
        self.history_filter_date_obj = None 


        # Variables pour la gestion des véhicules et chauffeurs dans les formulaires
        self.vehicles_for_combobox = []
        self.chauffeurs_for_combobox = []

        # Variables pour le formulaire d'Attribution
        self.attribution_selected_vehicle_id = tk.IntVar()
        self.attribution_selected_vehicle_id.set(0)
        self.attribution_selected_vehicle_display = tk.StringVar(value="")

        self.attribution_selected_chauffeur_id = tk.IntVar()
        self.attribution_selected_chauffeur_id.set(0)
        self.attribution_selected_chauffeur_display = tk.StringVar(value="")

        # Appel à la fonction pour créer l'en-tête (doit être appelée avant create_widgets)
        self.create_header() 
        
        # Le problème n'est pas l'appel à cette méthode en soi, mais l'état des variables avant cet appel.
        self.create_widgets() 

        
    def _format_date_for_treeview(self, date_value):
        """
        Formate une valeur de date pour l'affichage dans le Treeview et les exports.
        Accepte None, une chaîne (divers formats) ou un objet date/datetime.
        Retourne une chaîne vide si la date est manquante ou invalide.
        """
        if date_value is None or str(date_value).strip() == "":
            return ""

        if isinstance(date_value, (datetime, date)):
            return date_value.strftime("%Y-%m-%d")

        if isinstance(date_value, str):
            try:
                parsed_date = datetime.strptime(date_value, "%Y-%m-%d")
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                pass
            try:
                parsed_date = datetime.strptime(date_value, "%d/%m/%Y")
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                pass
            try:
                parsed_date = datetime.strptime(date_value, "%Y/%m/%d")
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                pass
            
            return ""
        return ""

    def _safe_parse_date(self, date_string):
        """
        Tente de convertir une chaîne de date au format YYYY-MM-DD en objet datetime.date pour le tri.
        Retourne datetime.date.min si la conversion échoue.
        """
        if date_string:
            try:
                return datetime.strptime(str(date_string), "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return date.min
        return date.min
    def _get_vehicle_options_for_stats(self):
        """
        Récupère la liste des véhicules pour le combobox des statistiques.
        Assurez-vous que get_all_vehicles() est accessible ici.
        """
        # Assurez-vous que get_all_vehicles() est importée ou définie globalement
        # Si get_all_vehicles est une méthode de la classe, ce serait self.get_all_vehicles()
        # Mais d'après votre structure, elle semble être une fonction globale.
        vehicles = get_all_vehicles()
        options = ["Tous"]
        for v in vehicles:
            options.append(f"{v[0]} - {v[1]}") # Assuming v[0] is ID, v[1] is License Plate
        return options

    def _safe_parse_date(self, date_str):
        """
        Convertit une chaîne de date en objet date, gère les erreurs.
        """
        from datetime import datetime, date # Assurez-vous que datetime et date sont importés
        if isinstance(date_str, date):
            return date_str
        try:
            return datetime.strptime(str(date_str), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return date.min

    def _is_date_in_range(self, current_date, start_date, end_date):
        """
        Vérifie si une date est dans la plage spécifiée.
        """
        from datetime import date # Assurez-vous que date est importé
        if current_date == date.min:
            return False
        if start_date and current_date < start_date:
            return False
        if end_date and current_date > end_date:
            return False
        return True

    
    def create_header(self):
        header_frame = tk.Frame(self.parent_frame, bg=self.bg_color_dashboard)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=3)
        header_frame.grid_columnconfigure(2, weight=1)

        if self.logo_path and os.path.exists(self.logo_path):
            try:
                from PIL import Image, ImageTk
                pil_image = Image.open(self.logo_path)
                pil_image = pil_image.resize((80, 80), Image.LANCZOS)
                self.tk_logo = ImageTk.PhotoImage(pil_image)
                
                logo_label = tk.Label(header_frame, image=self.tk_logo, bg=self.bg_color_dashboard)
                logo_label.grid(row=0, column=0, sticky="w", padx=10)
            except ImportError:
                messagebox.showwarning("Librairie manquante", "Pillow n'est pas installée. Le logo ne sera pas affiché. Installez-la avec 'pip install Pillow'.")
            except Exception as e:
                messagebox.showerror("Erreur Logo", f"Erreur lors du chargement du logo: {e}")
        
        welcome_label = tk.Label(header_frame, text="GESTION  RESPONSABLE", font=self.font_welcome_title,
                                 bg=self.bg_color_dashboard, fg=self.fg_color_text)
        welcome_label.grid(row=0, column=1, sticky="nsew", padx=10)

        


    # La méthode create_widgets DOIT être définie ici, au même niveau d'indentation que create_header
    def create_widgets(self):
        """
        Crée et organise tous les widgets principaux du tableau de bord.
        Utilise un `ttk.Notebook` pour gérer les différents onglets.
        """
        self.parent_frame.grid_columnconfigure(0, weight=1)
        self.parent_frame.grid_rowconfigure(0, weight=0)
        self.parent_frame.grid_rowconfigure(1, weight=1)

        self.notebook = ttk.Notebook(self.parent_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.attribution_frame = tk.Frame(self.notebook, bg=self.bg_color_dashboard)
        self.notebook.add(self.attribution_frame, text="Attributions")
        self.create_attribution_tab()

        self.maintenance_frame = tk.Frame(self.notebook, bg=self.bg_color_dashboard)
        self.notebook.add(self.maintenance_frame, text="Maintenance")
        self.create_maintenance_tab()

        self.fuel_frame = tk.Frame(self.notebook, bg=self.bg_color_dashboard)
        self.notebook.add(self.fuel_frame, text="Carburant")
        self.create_fuel_tab()

        self.incident_frame = tk.Frame(self.notebook, bg=self.bg_color_dashboard)
        self.notebook.add(self.incident_frame, text="Rapports d'Incident")
        self.create_incident_tab()

        self.history_frame = tk.Frame(self.notebook, bg=self.bg_color_dashboard)
        self.notebook.add(self.history_frame, text="Historique")
        self.create_history_tab()

        self.statistics_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.statistics_frame, text="Statistiques")
        self.create_statistics_tab()


    
        # --- Onglet Attributions ---
    
    def create_attribution_tab(self):
        self.attribution_frame.grid_columnconfigure(0, weight=1)
        self.attribution_frame.grid_columnconfigure(1, weight=2)
        self.attribution_frame.grid_rowconfigure(0, weight=1)
        self.attribution_frame.grid_rowconfigure(1, weight=0)

        input_frame = tk.LabelFrame(self.attribution_frame, text="Nouvelle Attribution / Clôture",
                                     bg=self.bg_color_dashboard, fg=self.fg_color_text,
                                     font=self.font_subtitle, bd=2, relief="groove")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.attribution_entries = {}

        # Chauffeur (Dropdown)
        chauffeur_label = tk.Label(input_frame, text="Chauffeur:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        chauffeur_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        
        self.chauffeur_options = [] # (id, display_name)
        
        # Utiliser tk.StringVar pour le texte affiché dans le Combobox
        self.attribution_selected_chauffeur_display = tk.StringVar() 
        # Utiliser tk.IntVar pour l'ID numérique réel du chauffeur
        self.attribution_selected_chauffeur_id = tk.IntVar() 
        self.attribution_selected_chauffeur_id.set(0) # Valeur par défaut 0 ou ID valide initial

        self.chauffeur_option_menu = ttk.Combobox(input_frame, textvariable=self.attribution_selected_chauffeur_display, state="readonly", font=self.font_label)
        self.chauffeur_option_menu.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.chauffeur_option_menu.bind("<<ComboboxSelected>>", self.on_chauffeur_selected)

        self.populate_chauffeur_options()


        # Véhicule (Dropdown)
        vehicle_label = tk.Label(input_frame, text="Véhicule:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        vehicle_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        
        self.vehicle_options = [] # (id, immatriculation)
        # Utiliser tk.StringVar pour le texte affiché dans le Combobox
        self.attribution_selected_vehicle_display = tk.StringVar()
        # Utiliser tk.IntVar pour l'ID numérique réel du véhicule
        self.attribution_selected_vehicle_id = tk.IntVar() 
        self.attribution_selected_vehicle_id.set(0)

        self.vehicle_option_menu = ttk.Combobox(input_frame, textvariable=self.attribution_selected_vehicle_display, state="readonly", font=self.font_label)
        self.vehicle_option_menu.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.vehicle_option_menu.bind("<<ComboboxSelected>>", self.on_vehicle_selected)
        
        self.populate_vehicle_options()


        fields = [
            ("Date début:", "date_debut", True),
            ("Date fin prévue:", "date_fin_prevue", True),
            ("Date fin réelle:", "date_fin_reelle", True),
            ("KM initial:", "etat_initial_km", False),
            ("KM final:", "etat_final_km", False),
            ("Carburant initial (%):", "etat_initial_carburant", False),
            ("Carburant final (%):", "etat_final_carburant", False),
            ("Observations:", "observations", False, "text") # Champ pour les observations de clôture
        ]

        row_idx = 2
        for label_text, key, is_date, *args in fields:
            lbl = tk.Label(input_frame, text=label_text, bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
            lbl.grid(row=row_idx, column=0, padx=5, pady=2, sticky="w")
            
            if is_date:
                entry = DateEntry(input_frame, width=12, background="darkblue", foreground="white", borderwidth=2,
                                  font=self.font_label, date_pattern='yyyy-mm-dd')
                entry.set_date(datetime.now().date())
                entry.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
                self.attribution_entries[key] = entry
            elif "text" in args: # Pour le champ observations (Tkinter Text widget)
                entry = tk.Text(input_frame, height=3, width=30, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text)
                entry.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
                self.attribution_entries[key] = entry
            else: # Pour les champs Entry standards
                entry = tk.Entry(input_frame, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text)
                entry.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
                self.attribution_entries[key] = entry
            row_idx += 1

        # Cadre des boutons d'action (attribution)
        button_frame = tk.Frame(self.attribution_frame, bg=self.bg_color_dashboard)
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        add_button = tk.Button(button_frame, text="Ajouter Attribution", command=self.add_attribution, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        end_button = tk.Button(button_frame, text="Clôturer Attribution", command=self.end_attribution, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        clear_button = tk.Button(button_frame, text="Effacer", command=self.clear_attribution_fields, font=self.font_button_text, bg="#7F8C8D", fg=self.button_fg)

        add_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        end_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        clear_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        # Treeview pour afficher les attributions
        self.attribution_tree = ttk.Treeview(self.attribution_frame, columns=(
            "ID", "Chauffeur", "Véhicule", "Début", "Fin Prévue", "Fin Réelle",
            "KM Init", "KM Fin", "Carb Init", "Carb Fin", "Statut", "Observations"
        ), show="headings")
        self.attribution_tree.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        # Configuration des colonnes
        for col in self.attribution_tree["columns"]:
            self.attribution_tree.heading(col, text=col, anchor="center")
            self.attribution_tree.column(col, width=80, anchor="center")
        
        self.attribution_tree.column("ID", width=30)
        self.attribution_tree.column("Observations", width=150) # Plus large pour les observations

        attribution_scrollbar = ttk.Scrollbar(self.attribution_frame, orient="vertical", command=self.attribution_tree.yview)
        attribution_scrollbar.grid(row=0, column=2, rowspan=2, sticky="ns")
        self.attribution_tree.configure(yscrollcommand=attribution_scrollbar.set)
        self.attribution_tree.bind("<<TreeviewSelect>>", self.load_attribution_into_fields)

        self.populate_attributions_treeview()

    def populate_chauffeur_options(self):
        chauffeurs_data = get_all_chauffeurs_and_responsables()
        self.chauffeur_options = [] # Stocke (id, display_name)
        if chauffeurs_data:
            for chf_id, chf_username, chf_nom, chf_prenom, chf_role in chauffeurs_data:
                if chf_role == 'chauffeur': # Filtrer pour les chauffeurs seulement
                    display_name = f"{chf_prenom} {chf_nom} ({chf_username})"
                    self.chauffeur_options.append((chf_id, display_name))
            
            # Mettre à jour les valeurs affichées dans le combobox
            self.chauffeur_option_menu['values'] = [opt[1] for opt in self.chauffeur_options]
            if self.chauffeur_options:
                # Définir le texte affiché dans le combobox
                self.attribution_selected_chauffeur_display.set(self.chauffeur_options[0][1])
                # Définir l'ID numérique du chauffeur sélectionné
                self.attribution_selected_chauffeur_id.set(self.chauffeur_options[0][0])
            else:
                self.chauffeur_option_menu.set("Aucun chauffeur")
                self.attribution_selected_chauffeur_id.set(0) # Réinitialiser l'ID
        else:
            self.chauffeur_option_menu['values'] = []
            self.chauffeur_option_menu.set("Aucun chauffeur")
            self.attribution_selected_chauffeur_id.set(0) # Réinitialiser l'ID


    def populate_vehicle_options(self):
        vehicles = get_active_vehicles() # Seuls les véhicules disponibles/en service
        self.vehicle_options = [] # Stocke (id, immatriculation)
        if vehicles:
            for veh_id, veh_immat, *rest in vehicles: 
                self.vehicle_options.append((veh_id, veh_immat))
            
            self.vehicle_option_menu['values'] = [opt[1] for opt in self.vehicle_options]
            if self.vehicle_options:
                # Définir le texte affiché dans le combobox
                self.attribution_selected_vehicle_display.set(self.vehicle_options[0][1])
                # Définir l'ID numérique du véhicule sélectionné
                self.attribution_selected_vehicle_id.set(self.vehicle_options[0][0])
            else:
                self.vehicle_option_menu.set("Aucun véhicule")
                self.attribution_selected_vehicle_id.set(0) # Réinitialiser l'ID
        else:
            self.vehicle_option_menu['values'] = []
            self.vehicle_option_menu.set("Aucun véhicule")
            self.attribution_selected_vehicle_id.set(0) # Réinitialiser l'ID


    def on_chauffeur_selected(self, event):
        # Récupérer le texte affiché par le combobox (le nom du chauffeur)
        selected_display_name = self.attribution_selected_chauffeur_display.get() 
        for chf_id, display_name in self.chauffeur_options:
            if display_name == selected_display_name:
                # Définir l'ID numérique correspondant
                self.attribution_selected_chauffeur_id.set(chf_id)
                break
    
    def on_vehicle_selected(self, event):
        # Récupérer le texte affiché par le combobox (l'immatriculation)
        selected_immat = self.attribution_selected_vehicle_display.get() 
        found_id = None
        for veh_id, veh_immat in self.vehicle_options:
            if veh_immat == selected_immat:
                found_id = veh_id
                break
        
        if found_id is not None:
            # Assigner l'ID numérique à la variable Tkinter IntVar
            self.attribution_selected_vehicle_id.set(found_id)
        else:
            self.attribution_selected_vehicle_id.set(0) # Réinitialiser si non trouvé


    def populate_attributions_treeview(self):
        for item in self.attribution_tree.get_children():
            self.attribution_tree.delete(item)
        
        attributions = get_all_attributions()
        if attributions:
            print(f"DEBUG DB: get_all_attributions - Success: True, Results count: {len(attributions)}")
            for attr in attributions:
                self_attr = list(attr) # Convertir en liste pour modification
                
                # Indices pour les dates dans le tuple attr: 3 (début), 4 (fin prévue), 5 (fin réelle)
                for i in [3, 4, 5]: 
                    date_value = attr[i]
                    if date_value: # Si la valeur de la date n'est ni None ni vide
                        if isinstance(date_value, (datetime, date)): # Si c'est un objet datetime.datetime ou datetime.date
                            self_attr[i] = date_value.strftime("%Y-%m-%d")
                        elif isinstance(date_value, str):
                            # Si c'est déjà une chaîne, l'utiliser telle quelle
                            # Vous pouvez ajouter une validation ou reformatage si le format de la chaîne n'est pas "%Y-%m-%d"
                            self_attr[i] = date_value
                        else:
                            self_attr[i] = "" # Gérer d'autres types inattendus en les mettant à vide
                    else:
                        self_attr[i] = "" # Garder la chaîne vide si la valeur est None ou vide

                self.attribution_tree.insert("", "end", values=self_attr)

    def load_attribution_into_fields(self, event):
        selected_item = self.attribution_tree.focus()
        if not selected_item:
            return

        values = self.attribution_tree.item(selected_item, 'values')
        # values: (ID, Chauffeur, Véhicule, Début, Fin Prévue, Fin Réelle, KM Init, KM Fin, Carb Init, Carb Fin, Statut, Observations)
        
        self.clear_attribution_fields()

        # Charger les valeurs dans les champs
        # Pour les dropdowns, trouver l'ID et définir la variable
        chauffeur_display_name = values[1] 
        found_chauffeur = False
        for chf_id, display_name in self.chauffeur_options:
            if display_name == chauffeur_display_name:
                self.attribution_selected_chauffeur_id.set(chf_id)
                self.attribution_selected_chauffeur_display.set(display_name) # Mettre à jour le StringVar
                found_chauffeur = True
                break
        if not found_chauffeur:
            # Cas où le nom affiché dans l'arbre ne correspond pas exactement
            # ou si un ancien format d'utilisateur est encore présent dans l'arbre.
            # Cela est moins probable avec les corrections précédentes, mais peut servir de fallback.
            messagebox.showwarning("Chauffeur non trouvé", f"Le chauffeur '{chauffeur_display_name}' n'a pas été trouvé dans la liste actuelle. Veuillez le sélectionner manuellement.")
            self.attribution_selected_chauffeur_id.set(0) # Réinitialiser l'ID
            self.attribution_selected_chauffeur_display.set("Sélectionnez un chauffeur")


        vehicle_immatriculation = values[2]
        found_vehicle = False
        for veh_id, veh_immat in self.vehicle_options:
            if veh_immat == vehicle_immatriculation:
                self.attribution_selected_vehicle_id.set(veh_id)
                self.attribution_selected_vehicle_display.set(vehicle_immatriculation) # Mettre à jour le StringVar
                found_vehicle = True
                break
        if not found_vehicle:
            messagebox.showwarning("Véhicule non trouvé", f"Le véhicule '{vehicle_immatriculation}' n'a pas été trouvé dans la liste actuelle. Veuillez le sélectionner manuellement.")
            self.attribution_selected_vehicle_id.set(0) # Réinitialiser l'ID
            self.attribution_selected_vehicle_display.set("Sélectionnez un véhicule")


        # Charger les dates - IMPORTANT : ajouter des vérifications pour les chaînes vides
        # values[3] est 'Date début'
        if values[3]: 
            try:
                self.attribution_entries['date_debut'].set_date(datetime.strptime(str(values[3]), "%Y-%m-%d").date())
            except ValueError:
                messagebox.showerror("Erreur de date", f"Impossible de lire la date de début: '{values[3]}'. Format attendu YYYY-MM-DD.")
                self.attribution_entries['date_debut'].set_date(datetime.now().date()) # Réinitialiser à la date actuelle
        else:
            self.attribution_entries['date_debut'].set_date(datetime.now().date())

        # values[4] est 'Date fin prévue'
        if values[4]:
            try:
                self.attribution_entries['date_fin_prevue'].set_date(datetime.strptime(str(values[4]), "%Y-%m-%d").date())
            except ValueError:
                messagebox.showerror("Erreur de date", f"Impossible de lire la date de fin prévue: '{values[4]}'. Format attendu YYYY-MM-DD.")
                self.attribution_entries['date_fin_prevue'].set_date(datetime.now().date())
        else:
            self.attribution_entries['date_fin_prevue'].set_date(datetime.now().date())

        # values[5] est 'Date fin réelle'
        if values[5]:
            try:
                self.attribution_entries['date_fin_reelle'].set_date(datetime.strptime(str(values[5]), "%Y-%m-%d").date())
            except ValueError:
                messagebox.showerror("Erreur de date", f"Impossible de lire la date de fin réelle: '{values[5]}'. Format attendu YYYY-MM-DD.")
                self.attribution_entries['date_fin_reelle'].set_date(datetime.now().date())
        else:
            self.attribution_entries['date_fin_reelle'].set_date(datetime.now().date())
        
        # Charger les autres champs
        self.attribution_entries['etat_initial_km'].insert(0, values[6])
        self.attribution_entries['etat_final_km'].insert(0, values[7])
        self.attribution_entries['etat_initial_carburant'].insert(0, values[8])
        self.attribution_entries['etat_final_carburant'].insert(0, values[9])
        
        # Pour le champ Text 'observations'
        self.attribution_entries['observations'].delete("1.0", tk.END)
        self.attribution_entries['observations'].insert("1.0", values[11])


    def add_attribution(self):
        chauffeur_id = self.attribution_selected_chauffeur_id.get() # Récupère l'ID numérique
        vehicle_id = self.attribution_selected_vehicle_id.get()   # Récupère l'ID numérique
        date_debut = self.attribution_entries['date_debut'].get_date()
        date_fin_prevue = self.attribution_entries['date_fin_prevue'].get_date()
        
        try:
            etat_initial_km = float(self.attribution_entries['etat_initial_km'].get())
            etat_initial_carburant = float(self.attribution_entries['etat_initial_carburant'].get())
        except ValueError:
            messagebox.showwarning("Entrée Invalide", "Les champs KM initial et Carburant initial doivent être des nombres.")
            return

        if not all([chauffeur_id, vehicle_id, date_debut, etat_initial_km, etat_initial_carburant]):
            messagebox.showwarning("Champs requis", "Veuillez remplir les champs obligatoires (Chauffeur, Véhicule, Date début, KM initial, Carburant initial).")
            return
        
        # Mettre à jour le statut du véhicule à 'en service'
        success_status, msg_status = update_vehicle_status_and_km(vehicle_id, 'en service', etat_initial_km)
        if not success_status:
            messagebox.showerror("Erreur", f"Impossible de mettre à jour le statut du véhicule: {msg_status}")
            return

        success, message = add_attribution_to_db(chauffeur_id, vehicle_id, date_debut, date_fin_prevue, etat_initial_km, etat_initial_carburant)
        if success:
            messagebox.showinfo("Succès", message)
            self.populate_attributions_treeview()
            self.populate_vehicle_options() # Rafraîchir les véhicules disponibles
            self.clear_attribution_fields()
        else:
            messagebox.showerror("Erreur", message)


    def end_attribution(self):
        selected_item = self.attribution_tree.focus()
        if not selected_item:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner une attribution à clôturer.")
            return
        
        attribution_id = self.attribution_tree.item(selected_item, 'values')[0]
        current_status = self.attribution_tree.item(selected_item, 'values')[10]

        if current_status == 'terminee':
            messagebox.showinfo("Information", "Cette attribution est déjà terminée.")
            return
        
        date_fin_reelle = self.attribution_entries['date_fin_reelle'].get_date()
        
        try:
            etat_final_km = float(self.attribution_entries['etat_final_km'].get())
            etat_final_carburant = float(self.attribution_entries['etat_final_carburant'].get())
        except ValueError:
            messagebox.showwarning("Entrée Invalide", "Les champs KM final et Carburant final doivent être des nombres.")
            return

        observations = self.attribution_entries['observations'].get("1.0", tk.END).strip()

        if not all([date_fin_reelle, etat_final_km, etat_final_carburant]):
            messagebox.showwarning("Champs requis", "Veuillez remplir les champs de clôture (Date fin réelle, KM final, Carburant final).")
            return
        
        attribution_data = get_attribution_by_id(attribution_id)
        if not attribution_data:
            messagebox.showerror("Erreur", "Attribution non trouvée dans la base de données.")
            return
        
        vehicle_id = attribution_data[2] # vehicle_id from attribution_data (check your DB schema for exact index)
        initial_km = attribution_data[6] # etat_initial_km (check your DB schema for exact index)

        if etat_final_km < initial_km:
            messagebox.showwarning("Kilométrage invalide", "Le kilométrage final ne peut pas être inférieur au kilométrage initial.")
            return

        # Mettre à jour l'attribution
        success, message = end_attribution_in_db(attribution_id, date_fin_reelle, etat_final_km, etat_final_carburant, observations)
        if success:
            # Mettre à jour le statut du véhicule à 'disponible' et son kilométrage
            success_status, msg_status = update_vehicle_status_and_km(vehicle_id, 'disponible', etat_final_km)
            if success_status:
                messagebox.showinfo("Succès", "Attribution clôturée avec succès et statut/kilométrage du véhicule mis à jour.")
                self.populate_attributions_treeview()
                self.populate_vehicle_options() # Rafraîchir les véhicules disponibles
                self.clear_attribution_fields()
            else:
                messagebox.showerror("Erreur", f"Attribution clôturée, mais erreur lors de la mise à jour du statut du véhicule: {msg_status}")
        else:
            messagebox.showerror("Erreur", message)


    def clear_attribution_fields(self):
        # Réinitialiser les ComboBox
        self.populate_chauffeur_options()
        self.populate_vehicle_options()
        
        # Réinitialiser les DateEntry à la date actuelle
        self.attribution_entries['date_debut'].set_date(datetime.now().date())
        self.attribution_entries['date_fin_prevue'].set_date(datetime.now().date())
        self.attribution_entries['date_fin_reelle'].set_date(datetime.now().date())
        
        # Effacer les champs Entry
        for key in ['etat_initial_km', 'etat_final_km', 'etat_initial_carburant', 'etat_final_carburant']:
            self.attribution_entries[key].delete(0, tk.END)
        
        # Effacer le champ Text
        self.attribution_entries['observations'].delete("1.0", tk.END)

        #----ongle Maintenance-----

    def create_maintenance_tab(self):
        """
        Crée les widgets pour l'onglet "Maintenance", y compris les champs de saisie,
        les boutons d'action et le Treeview pour afficher les maintenances.
        """
        self.maintenance_frame.grid_columnconfigure(0, weight=1)
        self.maintenance_frame.grid_columnconfigure(1, weight=2)
        self.maintenance_frame.grid_rowconfigure(0, weight=1)
        self.maintenance_frame.grid_rowconfigure(1, weight=0)

        input_frame = tk.LabelFrame(self.maintenance_frame, text="Détails Maintenance",
                                     bg=self.bg_color_dashboard, fg=self.fg_color_text,
                                     font=self.font_subtitle, bd=2, relief="groove")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.maintenance_entries = {}

        vehicle_label = tk.Label(input_frame, text="Véhicule:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        vehicle_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")

        self.maintenance_vehicle_options = []
        # self.maintenance_selected_vehicle_id est déjà un tk.IntVar() ou tk.StringVar() du __init__
        # self.maintenance_selected_vehicle_id = tk.StringVar() # Pas besoin de redéfinir ici
        # self.maintenance_selected_vehicle_id.set(0) # Pas besoin de redéfinir ici

        self.maintenance_vehicle_option_menu = ttk.Combobox(input_frame, textvariable=self.maintenance_selected_vehicle_id, state="readonly", font=self.font_label)
        self.maintenance_vehicle_option_menu.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.maintenance_vehicle_option_menu.bind("<<ComboboxSelected>>", self.on_maintenance_vehicle_selected)

        self.populate_maintenance_vehicle_options()

        type_maintenance_label = tk.Label(input_frame, text="Type de maintenance:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        type_maintenance_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.maintenance_type_var = tk.StringVar()
        self.maintenance_type_combobox = ttk.Combobox(input_frame, textvariable=self.maintenance_type_var, values=self.maintenance_types, state="readonly", font=self.font_label)
        self.maintenance_type_combobox.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        if self.maintenance_types:
            self.maintenance_type_combobox.set(self.maintenance_types[0])


        fields = [
            ("Date maintenance:", "date_maintenance", True),
            ("Coût:", "cout"),
            ("Description:", "description", False, "text"),
            ("Prochaine maintenance (KM):", "prochaine_maintenance_km"),
            ("Prochaine maintenance (Date):", "prochaine_maintenance_date", True)
        ]

        row_idx = 2
        for label_text, key, *args in fields:
            lbl = tk.Label(input_frame, text=label_text, bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
            lbl.grid(row=row_idx, column=0, padx=5, pady=2, sticky="w")

            if "True" in [str(a) for a in args]:
                entry = DateEntry(input_frame, width=12, background="darkblue", foreground="white", borderwidth=2,
                                  font=self.font_label, date_pattern='yyyy-mm-dd')
                entry.set_date(datetime.now().date())
                entry.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
                self.maintenance_entries[key] = entry
            elif "text" in args:
                entry = tk.Text(input_frame, height=3, width=30, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text)
                entry.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
                self.maintenance_entries[key] = entry
            else:
                entry = tk.Entry(input_frame, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text)
                entry.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
                self.maintenance_entries[key] = entry
            row_idx += 1

        button_frame = tk.Frame(self.maintenance_frame, bg=self.bg_color_dashboard)
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        add_button = tk.Button(button_frame, text="Ajouter Maintenance", command=self.add_maintenance, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        update_button = tk.Button(button_frame, text="Modifier Maintenance", command=self.update_maintenance, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        delete_button = tk.Button(button_frame, text="Supprimer Maintenance", command=self.delete_maintenance, font=self.font_button_text, bg="#E74C3C", fg=self.button_fg)
        clear_button = tk.Button(button_frame, text="Effacer", command=self.clear_maintenance_fields, font=self.font_button_text, bg="#7F8C8D", fg=self.button_fg)

        add_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        update_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        delete_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        clear_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        self.maintenance_tree = ttk.Treeview(self.maintenance_frame, columns=(
            "ID", "Véhicule", "Type", "Date", "Coût", "Description", "Proch. KM", "Proch. Date"
        ), show="headings")
        self.maintenance_tree.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        for col in self.maintenance_tree["columns"]:
            self.maintenance_tree.heading(col, text=col, anchor="center")
            self.maintenance_tree.column(col, width=80, anchor="center")
        self.maintenance_tree.column("ID", width=30)
        self.maintenance_tree.column("Description", width=150)

        maintenance_scrollbar = ttk.Scrollbar(self.maintenance_frame, orient="vertical", command=self.maintenance_tree.yview)
        maintenance_scrollbar.grid(row=0, column=2, rowspan=2, sticky="ns")
        self.maintenance_tree.configure(yscrollcommand=maintenance_scrollbar.set)
        self.maintenance_tree.bind("<<TreeviewSelect>>", self.load_maintenance_into_fields)

        self.populate_maintenances_treeview()

    def populate_maintenance_vehicle_options(self):
        """
        Remplit le menu déroulant des véhicules pour l'onglet Maintenance.
        """
        vehicles = get_all_vehicles()
        self.maintenance_vehicle_options = []
        if vehicles:
            for veh_id, veh_immat, *rest in vehicles:
                self.maintenance_vehicle_options.append((veh_id, veh_immat))

            self.maintenance_vehicle_option_menu['values'] = [opt[1] for opt in self.maintenance_vehicle_options]
            if self.maintenance_vehicle_options:
                # Convertir l'ID en int si self.maintenance_selected_vehicle_id est un tk.IntVar
                self.maintenance_selected_vehicle_id.set(int(self.maintenance_vehicle_options[0][0]))
                self.maintenance_vehicle_option_menu.set(self.maintenance_vehicle_options[0][1])
            else:
                self.maintenance_selected_vehicle_id.set(0)
                self.maintenance_vehicle_option_menu.set("Aucun véhicule")
        else:
            self.maintenance_vehicle_option_menu['values'] = []
            self.maintenance_selected_vehicle_id.set(0)
            self.maintenance_vehicle_option_menu.set("Aucun véhicule")

    def on_maintenance_vehicle_selected(self, event):
        """
        Met à jour l'ID du véhicule sélectionné pour la maintenance.
        """
        selected_immat = self.maintenance_vehicle_option_menu.get()
        found_id = 0
        for veh_id, veh_immat in self.maintenance_vehicle_options:
            if veh_immat == selected_immat:
                found_id = veh_id
                break

        if found_id != 0:
            # Convertir found_id en int si self.maintenance_selected_vehicle_id est un tk.IntVar
            self.maintenance_selected_vehicle_id.set(int(found_id))
        else:
            self.maintenance_selected_vehicle_id.set(0)

    # VÉRIFIEZ L'INDENTATION À PARTIR D'ICI POUR TOUTES LES MÉTHODES SUIVANTES !
    # ELLES DOIVENT ÊTRE AU MÊME NIVEAU D'INDENTATION QUE create_maintenance_tab et on_maintenance_vehicle_selected

    def populate_maintenances_treeview(self):
        for item in self.maintenance_tree.get_children():
            self.maintenance_tree.delete(item)

        maintenances = get_all_maintenances()
        if maintenances:
          for maint in maintenances:
            # Debug: Afficher la structure complète des données
            print(f"DEBUG - Données maintenance brute: {maint}")
            
            values_for_tree = (
                str(maint[0]),  # ID - conversion explicite en string
                maint[1],        # Immatriculation véhicule
                maint[2],        # Type maintenance
                self._format_date_for_treeview(maint[3]),  # Date maintenance
                f"{maint[4]:.2f}" if maint[4] is not None else "0.00",  # Coût formaté
                maint[5] if maint[5] else "",  # Description
                str(maint[9]) if len(maint) > 9 and maint[9] is not None else "",  # Proch. KM
                self._format_date_for_treeview(maint[8]) if len(maint) > 8 and maint[8] else ""  # Proch. Date
            )
            print(f"DEBUG - Valeurs pour Treeview: {values_for_tree}")
            self.maintenance_tree.insert("", "end", values=values_for_tree)
    def load_maintenance_into_fields(self, event):
        """
        Charge les détails de la maintenance sélectionnée dans les champs de saisie.
        """
        selected_item = self.maintenance_tree.focus()
        if not selected_item:
            return

        values = self.maintenance_tree.item(selected_item, 'values')
        if not values or len(values) < 8:
                print(f"ERREUR: Valeurs incomplètes: {values}")
                return

        try:
                self.selected_maintenance_id = int(values[0])  # Conversion en int
                print(f"DEBUG - Maintenance chargée - ID: {self.selected_maintenance_id}")
        except (ValueError, IndexError) as e:
                print(f"ERREUR: ID maintenance invalide: {values[0]} - {str(e)}")
                return

        if values[3]: # Date maintenance
            self.maintenance_entries['date_maintenance'].set_date(datetime.strptime(values[3], "%Y-%m-%d").date())
        else:
            self.maintenance_entries['date_maintenance'].set_date(datetime.now().date())

        self.maintenance_entries['cout'].insert(0, values[4])
        self.maintenance_entries['description'].delete("1.0", tk.END)
        self.maintenance_entries['description'].insert("1.0", values[5])

        self.maintenance_entries['prochaine_maintenance_km'].insert(0, values[6]) # values[6] vient du Treeview (Proch. KM)

        if values[7]: # values[7] vient du Treeview (Proch. Date)
            self.maintenance_entries['prochaine_maintenance_date'].set_date(datetime.strptime(values[7], "%Y-%m-%d").date())
        else:
            self.maintenance_entries['prochaine_maintenance_date'].set_date(datetime.now().date())

    def add_maintenance(self):
        """
        Ajoute une nouvelle entrée de maintenance à la base de données.
        """
        # Étape 1: Récupérer l'ID numérique du véhicule directement
        selected_vehicle_id_str = self.maintenance_selected_vehicle_id.get().strip()

        if not selected_vehicle_id_str: # Vérifie si la chaîne est vide
            messagebox.showwarning("Sélection invalide", "Veuillez sélectionner un véhicule.")
            return

        try:
            vehicle_id = int(selected_vehicle_id_str)
        except ValueError:
            messagebox.showwarning("Sélection invalide", "L'ID du véhicule n'est pas un nombre valide.")
            return

        # Optionnel mais recommandé : Vérifier si l'ID existe réellement dans votre liste de véhicules
        # C'est une bonne pratique de s'assurer que l'ID sélectionné correspond à un véhicule réel.
        # Pour cela, vous auriez besoin d'une liste simple d'IDs de véhicules valides, ou de faire un appel à la base de données.
        # Si get_all_vehicles() est déjà appelé et stocké (par ex. self.all_vehicle_ids), vous pouvez vérifier contre ça.
        # Sinon, vous pouvez appeler get_vehicle_by_id(vehicle_id) ici pour valider.
        
        # Exemple de vérification (supposons que self.maintenance_vehicle_options contient (id, immatriculation) )
        valid_vehicle_ids = [opt[0] for opt in self.maintenance_vehicle_options]
        if vehicle_id not in valid_vehicle_ids:
             messagebox.showwarning("Sélection invalide", "Le véhicule sélectionné n'est pas valide.")
             return
        
        # Le reste de votre code est bon, vehicle_id est maintenant l'ID numérique attendu.
        type_maintenance = self.maintenance_type_var.get()
        date_maintenance = self.maintenance_entries['date_maintenance'].get_date()
        description = self.maintenance_entries['description'].get("1.0", tk.END).strip()

        try:
            cout = float(self.maintenance_entries['cout'].get())
        except ValueError:
            messagebox.showwarning("Entrée invalide", "Le coût doit être un nombre.")
            return

        prochaine_maintenance_km_str = self.maintenance_entries['prochaine_maintenance_km'].get().strip()
        prochaine_maintenance_km = int(prochaine_maintenance_km_str) if prochaine_maintenance_km_str else None

        prochaine_maintenance_date = self.maintenance_entries['prochaine_maintenance_date'].get_date()

        if not all([vehicle_id, type_maintenance, date_maintenance, cout is not None]):
            messagebox.showwarning("Champs requis", "Veuillez remplir au minimum le Véhicule, Type, Date et Coût de la maintenance.")
            return

        success, message = add_maintenance_to_db(
            vehicle_id, # C'est maintenant l'ID numérique
            type_maintenance,
            date_maintenance,
            cout,
            description,
            'Terminée',
            None, # kilometrage_maintenance
            prochaine_maintenance_date,
            prochaine_maintenance_km
        )
        if success:
            messagebox.showinfo("Succès", message)
            self.populate_maintenances_treeview()
            self.clear_maintenance_fields()
        else:
            messagebox.showerror("Erreur", message)

    def update_maintenance(self):
      """
      Met à jour une entrée de maintenance dans la base de données.
      Contrôles :
      - Vérification de la sélection
      - Validation des données
      - Gestion robuste des erreurs
      - Mise à jour de l'interface
      """
      # Vérification de la sélection
      if not hasattr(self, 'selected_maintenance_id') or not self.selected_maintenance_id:
        messagebox.showwarning("Sélection requise", "Veuillez sélectionner une maintenance à modifier.")
        return

      print(f"DEBUG - Tentative modification ID: {self.selected_maintenance_id}")

      try:
        # Validation des données obligatoires
        vehicle_id = int(self.maintenance_selected_vehicle_id.get())
        cout = float(self.maintenance_entries['cout'].get())
        date_maint = self.maintenance_entries['date_maintenance'].get_date()
        
        # Données optionnelles
        proch_km = self.maintenance_entries['prochaine_maintenance_km'].get().strip()
        proch_km = int(proch_km) if proch_km else None
        
        notes = self.maintenance_entries['description'].get("1.0", tk.END).strip()
        print(f"DEBUG - Notes: {notes}")

        # Construction des paramètres
        params = {
            'maintenance_id': self.selected_maintenance_id,
            'vehicle_id': vehicle_id,
            'type_maintenance': self.maintenance_type_var.get(),
            'date_maintenance': date_maint,
            'cout': cout,
            'notes': notes,
            'statut': 'Terminée',  # Paramètre manquant ajouté
            'kilometrage_maintenance': None,
            'date_prochain_entretien': self.maintenance_entries['prochaine_maintenance_date'].get_date(),
            'kilometrage_prochain_entretien': proch_km
        }
        print(f"DEBUG - Paramètres envoyés: {params}")

        # Appel à la fonction de mise à jour
        success, message = update_maintenance_in_db(**params)
        
        if success:
            messagebox.showinfo("Succès", message)
            self.populate_maintenances_treeview()
            self.clear_maintenance_fields()
        else:
            messagebox.showerror("Erreur", message)
            
      except ValueError as e:
        messagebox.showerror("Erreur de validation", f"Donnée invalide: {str(e)}")
      except Exception as e:
        messagebox.showerror(
            "Erreur inattendue", 
            f"Une erreur est survenue lors de la modification:\n{str(e)}"
        )
        

    def delete_maintenance(self):
      """
      Supprime une entrée de maintenance de la base de données de manière sécurisée.
      Contrôles :
      - Vérification de l'existence de l'ID
      - Confirmation explicite
      - Gestion robuste des erreurs
      - Protection contre les suppressions massives
      """
      # Vérification de la sélection
      if not hasattr(self, 'selected_maintenance_id') or not self.selected_maintenance_id:
        messagebox.showwarning("Sélection requise", "Veuillez sélectionner une maintenance à supprimer.")
        return

      try:
        # Conversion sécurisée de l'ID
        maintenance_id = int(self.selected_maintenance_id)
        print(f"DEBUG - Tentative suppression de l'ID: {maintenance_id}")
        
        # Protection contre les ID invalides
        if maintenance_id <= 0:
            raise ValueError("ID de maintenance invalide (doit être positif)")

        # Confirmation utilisateur explicite
        confirmation = messagebox.askyesno(
            "Confirmation de suppression",
            f"Êtes-vous sûr de vouloir supprimer définitivement la maintenance #{maintenance_id}?\n"
            "Cette action est irréversible.",
            icon='warning'
        )
        if not confirmation:
            print("DEBUG - Suppression annulée par l'utilisateur")
            return

        # Appel à la base de données avec timeout
        success, message = delete_maintenance_from_db(maintenance_id)
        
        if success:
            # Mise à jour de l'interface
            messagebox.showinfo("Succès", message)
            self.populate_maintenances_treeview()
            self.clear_maintenance_fields()
            
            # Nettoyage de la sélection
            if hasattr(self, 'selected_maintenance_id'):
                del self.selected_maintenance_id
        else:
            messagebox.showerror("Échec", f"La suppression a échoué : {message}")

      except ValueError as e:
        messagebox.showerror("Erreur", f"ID invalide : {str(e)}")
      except Exception as e:
        messagebox.showerror(
            "Erreur critique", 
            f"Une erreur inattendue est survenue :\n{str(e)}\n\n"
            "Aucune donnée n'a été modifiée."
        )
       
    def clear_maintenance_fields(self):
        """
        Efface tous les champs de saisie de l'onglet Maintenance.
        """
        self.populate_maintenance_vehicle_options()
        if self.maintenance_types:
            self.maintenance_type_combobox.set(self.maintenance_types[0])
        else:
            self.maintenance_type_combobox.set("")
        self.maintenance_entries['date_maintenance'].set_date(datetime.now().date())
        self.maintenance_entries['cout'].delete(0, tk.END)
        self.maintenance_entries['description'].delete("1.0", tk.END)
        self.maintenance_entries['prochaine_maintenance_km'].delete(0, tk.END)
        self.maintenance_entries['prochaine_maintenance_date'].set_date(datetime.now().date())
        if hasattr(self, 'selected_maintenance_id'):
            del self.selected_maintenance_id

    # Ajoutez ici la méthode _format_date_for_treeview si elle n'existe pas déjà
    def _format_date_for_treeview(self, date_obj):
        """
        Formate un objet date (ou une chaîne de date) en chaîne 'YYYY-MM-DD' pour le Treeview.
        """
        if date_obj:
            if isinstance(date_obj, datetime):
                return date_obj.strftime("%Y-%m-%d")
            elif isinstance(date_obj, date): # if using from datetime import date
                return date_obj.strftime("%Y-%m-%d")
            elif isinstance(date_obj, str):
                try:
                    # Tenter de parser la chaîne si elle n'est pas déjà au bon format
                    return datetime.strptime(date_obj, "%Y-%m-%d").strftime("%Y-%m-%d")
                except ValueError:
                    return str(date_obj) # Retourne tel quel si impossible à parser
            return str(date_obj) # Fallback pour tout autre type
        return ""
    
    # --- Onglet Carburant ---
    
    def create_fuel_tab(self):
        """
        Crée les widgets pour l'onglet "Carburant".
        """
        self.fuel_frame.grid_columnconfigure(0, weight=1)
        self.fuel_frame.grid_columnconfigure(1, weight=2)
        self.fuel_frame.grid_rowconfigure(0, weight=1)
        self.fuel_frame.grid_rowconfigure(1, weight=0)

        input_frame = tk.LabelFrame(self.fuel_frame, text="Enregistrer un Plein de Carburant",
                                     bg=self.bg_color_dashboard, fg=self.fg_color_text,
                                     font=self.font_subtitle, bd=2, relief="groove")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.fuel_entries = {}

        vehicle_label = tk.Label(input_frame, text="Véhicule:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        vehicle_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        
        self.fuel_vehicle_options = [] # Ex: [(1, 'ABC-123-D'), (2, 'XYZ-789-E')]

        # MODIFICATION CLÉ : Utilisez IntVar pour l'ID et StringVar pour l'affichage du Combobox
        self.fuel_selected_vehicle_id = tk.IntVar() # Stockera l'ID numérique du véhicule
        self.fuel_selected_vehicle_id.set(0) # Initialisation à 0

        self.fuel_display_immat = tk.StringVar() # Stockera l'immatriculation affichée dans le Combobox
        self.fuel_display_immat.set("Aucun véhicule") # Valeur par défaut pour l'affichage

        self.fuel_vehicle_option_menu = ttk.Combobox(input_frame, textvariable=self.fuel_display_immat, state="readonly", font=self.font_label)
        self.fuel_vehicle_option_menu.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.fuel_vehicle_option_menu.bind("<<ComboboxSelected>>", self.on_fuel_vehicle_selected)
        self.populate_fuel_vehicle_options()

        type_carburant_label = tk.Label(input_frame, text="Type de carburant:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        type_carburant_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.fuel_type_var = tk.StringVar()
        self.fuel_type_combobox = ttk.Combobox(input_frame, textvariable=self.fuel_type_var, values=self.fuel_types, state="readonly", font=self.font_label)
        self.fuel_type_combobox.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        if self.fuel_types:
            self.fuel_type_combobox.set(self.fuel_types[0])


        fields = [
            ("Date du plein:", "date_entree", True),
            ("Quantité (Litres):", "quantite_litres"),
            ("Prix total (MGA):", "cout_total"),
            ("Kilométrage relevé:", "kilometrage_releve"),
            ("Kilométrage au départ (optionnel):", "kilometrage_depart"),
            ("Lieu:", "lieu"),
            ("Notes:", "notes", False, "text")
        ]
        
        row_idx = 2
        for label_text, key, *args in fields:
            lbl = tk.Label(input_frame, text=label_text, bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
            lbl.grid(row=row_idx, column=0, padx=5, pady=2, sticky="w")
            
            if "True" in [str(a) for a in args]:
                entry = DateEntry(input_frame, width=12, background="darkblue", foreground="white", borderwidth=2,
                                  font=self.font_label, date_pattern='yyyy-mm-dd')
                entry.set_date(datetime.now().date())
                entry.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
                self.fuel_entries[key] = entry
            elif "text" in args:
                entry = tk.Text(input_frame, height=3, width=30, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text)
                entry.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
                self.fuel_entries[key] = entry
            else:
                entry = tk.Entry(input_frame, font=self.font_label, bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text)
                entry.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
                self.fuel_entries[key] = entry
            row_idx += 1

        button_frame = tk.Frame(self.fuel_frame, bg=self.bg_color_dashboard)
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        add_button = tk.Button(button_frame, text="Ajouter Carburant", command=self.add_fuel_entry, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        update_button = tk.Button(button_frame, text="Modifier Carburant", command=self.update_fuel_entry, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        delete_button = tk.Button(button_frame, text="Supprimer Carburant", command=self.delete_fuel_entry, font=self.font_button_text, bg="#E74C3C", fg=self.button_fg)
        clear_button = tk.Button(button_frame, text="Effacer", command=self.clear_fuel_fields, font=self.font_button_text, bg="#7F8C8D", fg=self.button_fg)

        add_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        update_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        delete_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        clear_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        self.fuel_tree = ttk.Treeview(self.fuel_frame, columns=(
            "ID", "Véhicule", "Date", "Type", "Quantité", "Coût", "KM Départ", "KM Relevé", "Lieu", "Notes"
        ), show="headings")
        self.fuel_tree.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        for col in self.fuel_tree["columns"]:
            self.fuel_tree.heading(col, text=col, anchor="center")
            self.fuel_tree.column(col, width=80, anchor="center")
        self.fuel_tree.column("ID", width=30)
        self.fuel_tree.column("Notes", width=150)

        fuel_scrollbar = ttk.Scrollbar(self.fuel_frame, orient="vertical", command=self.fuel_tree.yview)
        fuel_scrollbar.grid(row=0, column=2, rowspan=2, sticky="ns")
        self.fuel_tree.configure(yscrollcommand=fuel_scrollbar.set)
        self.fuel_tree.bind("<<TreeviewSelect>>", self.load_fuel_entry_into_fields)
        self.populate_fuel_entries_treeview()

    def populate_fuel_vehicle_options(self):
        vehicles = get_all_vehicles()
        self.fuel_vehicle_options = []
        if vehicles:
            for veh_id, veh_immat, *rest in vehicles:
                self.fuel_vehicle_options.append((veh_id, veh_immat))
            
            self.fuel_vehicle_option_menu['values'] = [opt[1] for opt in self.fuel_vehicle_options]
            
            if self.fuel_vehicle_options:
                # Définit l'ID interne (numérique)
                self.fuel_selected_vehicle_id.set(self.fuel_vehicle_options[0][0])
                # Définit la valeur affichée dans le Combobox (immatriculation)
                self.fuel_display_immat.set(self.fuel_vehicle_options[0][1])
            else:
                self.fuel_selected_vehicle_id.set(0)
                self.fuel_display_immat.set("Aucun véhicule") # Affichage par défaut si pas de véhicule
        else:
            self.fuel_vehicle_option_menu['values'] = []
            self.fuel_selected_vehicle_id.set(0)
            self.fuel_display_immat.set("Aucun véhicule") # Affichage par défaut si pas de véhicule

    def on_fuel_vehicle_selected(self, event):
        selected_immat = self.fuel_display_immat.get() # Obtient l'immatriculation affichée
        print(f"Debug: Combobox selected_immat from get() = {selected_immat}")
        found_id = None
        for veh_id, veh_immat in self.fuel_vehicle_options:
            if veh_immat == selected_immat:
                found_id = veh_id
                break
        if found_id is not None:
            self.fuel_selected_vehicle_id.set(found_id)
            print(f"Debug: fuel_selected_vehicle_id set to = {found_id}")
        else:
            self.fuel_selected_vehicle_id.set(0)
            print(f"Debug: No ID found for selected_immat '{selected_immat}', setting to 0")

    def populate_fuel_entries_treeview(self,):
    
        for item in self.fuel_tree.get_children():
            self.fuel_tree.delete(item)
        
        fuel_entries = get_all_fuel_entries()
        if fuel_entries:
            for entry in fuel_entries:
                num_cols = len(entry)

                # Assurez-vous que l'index 3 est bien l'immatriculation du véhicule dans votre base de données
                # L'ordre des colonnes dans le tuple 'entry' doit correspondre à votre requête SQL de get_all_fuel_entries()
                vehicle_immat = entry[3] if num_cols > 3 else ""
                formatted_date = self._format_date_for_treeview(entry[4]) if num_cols > 4 else ""

                values_for_tree = (
                    entry[0] if num_cols > 0 else "",  # ID
                    vehicle_immat,                     # Véhicule (Immatriculation)
                    formatted_date,                    # Date
                    entry[5] if num_cols > 5 else "",  # Type
                    entry[6] if num_cols > 6 else "",  # Quantité
                    entry[7] if num_cols > 7 else "",  # Coût
                    entry[8] if num_cols > 8 else "",  # KM Départ
                    entry[9] if num_cols > 9 else "",  # KM Relevé
                    entry[10] if num_cols > 10 else "", # Lieu
                    entry[11] if num_cols > 11 else ""  # Notes
                )
                self.fuel_tree.insert("", "end", values=values_for_tree)

    def load_fuel_entry_into_fields(self, event):
        selected_item = self.fuel_tree.focus()
        if not selected_item:
            return

        values = self.fuel_tree.item(selected_item, 'values')
        self.selected_fuel_entry_id = values[0]
        self.clear_fuel_fields()

        vehicle_immatriculation = values[1] # C'est l'immatriculation du véhicule depuis le Treeview
        found_id_for_load = None
        for veh_id, veh_immat in self.fuel_vehicle_options:
            if veh_immat == vehicle_immatriculation:
                found_id_for_load = veh_id
                break
        
        if found_id_for_load is not None:
            self.fuel_selected_vehicle_id.set(found_id_for_load)
            self.fuel_display_immat.set(vehicle_immatriculation) # Définit l'affichage du Combobox
        else:
            self.fuel_selected_vehicle_id.set(0)
            self.fuel_display_immat.set("Aucun véhicule") # Ou une autre valeur par défaut si non trouvé
            print(f"Warning: Véhicule '{vehicle_immatriculation}' du Treeview non trouvé dans les options. Réinitialisation à 'Aucun véhicule'.")


        try:
            if values[2]:
                self.fuel_entries['date_entree'].set_date(datetime.strptime(values[2], "%Y-%m-%d").date())
            else:
                self.fuel_entries['date_entree'].set_date(None)
        except ValueError:
            self.fuel_entries['date_entree'].set_date(None)
            print(f"Warning: Impossible de convertir la chaîne de date '{values[2]}' pour date_entree. Réinitialisation à vide.")

        self.fuel_type_combobox.set(values[3])
        self.fuel_entries['quantite_litres'].insert(0, values[4])
        self.fuel_entries['cout_total'].insert(0, values[5])
        self.fuel_entries['kilometrage_depart'].insert(0, values[6])
        self.fuel_entries['kilometrage_releve'].insert(0, values[7])
        self.fuel_entries['lieu'].insert(0, values[8])
        self.fuel_entries['notes'].delete("1.0", tk.END)
        self.fuel_entries['notes'].insert("1.0", values[9])

    def add_fuel_entry(self):
        # Récupère l'ID numérique directement depuis la variable de contrôle
        vehicle_id = self.fuel_selected_vehicle_id.get() 
        selected_immat_for_debug = self.fuel_display_immat.get() # Pour le débogage seulement

        print("→ Véhicule sélectionné (affichage) :", selected_immat_for_debug)
        print("→ ID correspondant (réel) :", vehicle_id)

        # Si l'ID est 0 (valeur par défaut) ou si l'utilisateur n'a rien sélectionné de valide
        if vehicle_id == 0 or selected_immat_for_debug == "Aucun véhicule": # Ajoutez cette vérification pour l'affichage
            messagebox.showwarning("Sélection Invalide", "Veuillez sélectionner un véhicule valide.")
            return

        # Lecture des champs
        try:
            date_entree = self.fuel_entries['date_entree'].get_date()
            type_carburant = self.fuel_type_combobox.get()
            quantite_litres = float(self.fuel_entries['quantite_litres'].get())
            cout_total = float(self.fuel_entries['cout_total'].get())
            kilometrage_releve = int(self.fuel_entries['kilometrage_releve'].get())
            
            kilometrage_depart_str = self.fuel_entries['kilometrage_depart'].get()
            kilometrage_depart = int(kilometrage_depart_str) if kilometrage_depart_str else None

            lieu = self.fuel_entries['lieu'].get()
            notes = self.fuel_entries['notes'].get("1.0", tk.END).strip()
        except ValueError:
            messagebox.showwarning("Entrée Invalide", "Vérifiez que tous les champs numériques sont valides (Quantité, Coût, Kilométrage).")
            return
        except Exception as e:
            messagebox.showwarning("Entrée Invalide", f"Une erreur inattendue est survenue lors de la lecture des champs: {e}")
            print("Erreur de parsing:", e)
            return

        if not all([date_entree, type_carburant, quantite_litres, cout_total, kilometrage_releve, lieu]):
            messagebox.showwarning("Champs requis", "Veuillez remplir tous les champs obligatoires.")
            return

        success, message = add_fuel_entry_to_db(
            self.logged_in_user_id, vehicle_id, date_entree, type_carburant,
            quantite_litres, cout_total, kilometrage_depart, kilometrage_releve,
            lieu, notes
        )

        if success:
            messagebox.showinfo("Succès", message)
            self.populate_fuel_entries_treeview()
            self.clear_fuel_fields()
        else:
            messagebox.showerror("Erreur", message)


    def update_fuel_entry(self):
        selected_item = self.fuel_tree.focus()
        if not selected_item:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner une entrée de carburant à modifier.")
            return
        fuel_entry_id = self.fuel_tree.item(selected_item, 'values')[0]

        # Récupère l'ID numérique directement depuis la variable de contrôle
        vehicle_id = self.fuel_selected_vehicle_id.get()
        selected_immat_for_debug = self.fuel_display_immat.get() # Pour le débogage seulement

        print("→ Véhicule sélectionné (affichage) :", selected_immat_for_debug)
        print("→ ID correspondant (réel) :", vehicle_id)
        
        if vehicle_id == 0 or selected_immat_for_debug == "Aucun véhicule":
            messagebox.showwarning("Sélection Invalide", "Veuillez sélectionner un véhicule valide.")
            return

        date_entree = self.fuel_entries['date_entree'].get_date()
        type_carburant = self.fuel_type_combobox.get()
        lieu = self.fuel_entries['lieu'].get()
        notes = self.fuel_entries['notes'].get("1.0", tk.END).strip()

        try:
            quantite_litres = float(self.fuel_entries['quantite_litres'].get())
            cout_total = float(self.fuel_entries['cout_total'].get())
            kilometrage_releve = int(self.fuel_entries['kilometrage_releve'].get())
            
            kilometrage_depart_str = self.fuel_entries['kilometrage_depart'].get()
            kilometrage_depart = int(kilometrage_depart_str) if kilometrage_depart_str else None
        except ValueError:
            messagebox.showwarning("Entrée Invalide", "Quantité, coût et kilométrage doivent être des nombres valides.")
            return

        if not all([vehicle_id, date_entree, type_carburant, quantite_litres, cout_total, kilometrage_releve, lieu]):
            messagebox.showwarning("Champs requis", "Veuillez remplir tous les champs obligatoires.")
            return
        
        success, message = update_fuel_entry_in_db(
            fuel_entry_id, self.logged_in_user_id, vehicle_id, date_entree, type_carburant, quantite_litres, cout_total,
            kilometrage_depart, kilometrage_releve, lieu, notes
        )

        if success:
            messagebox.showinfo("Succès", message)
            self.populate_fuel_entries_treeview()
            self.clear_fuel_fields()
        else:
            messagebox.showerror("Erreur", message)

    def delete_fuel_entry(self):
        selected_item = self.fuel_tree.focus()
        if not selected_item:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner une entrée de carburant à supprimer.")
            return
        fuel_entry_id = self.fuel_tree.item(selected_item, 'values')[0]

        if messagebox.askyesno("Confirmer la suppression", f"Êtes-vous sûr de vouloir supprimer cette entrée de carburant (ID: {fuel_entry_id})?"):
            success, message = delete_fuel_entry_from_db(fuel_entry_id)
            if success:
                messagebox.showinfo("Succès", message)
                self.populate_fuel_entries_treeview()
                self.clear_fuel_fields()
                if hasattr(self, 'selected_fuel_entry_id'):
                    del self.selected_fuel_entry_id
            else:
                messagebox.showerror("Erreur", message)

    def clear_fuel_fields(self):
        self.populate_fuel_vehicle_options() # Réinitialise le Combobox et l'ID
        self.fuel_entries['date_entree'].set_date(datetime.now().date())
        if self.fuel_types:
            self.fuel_type_combobox.set(self.fuel_types[0])
        else:
            self.fuel_type_combobox.set("")
        self.fuel_entries['quantite_litres'].delete(0, tk.END)
        self.fuel_entries['cout_total'].delete(0, tk.END)
        self.fuel_entries['kilometrage_depart'].delete(0, tk.END)
        self.fuel_entries['kilometrage_releve'].delete(0, tk.END)
        self.fuel_entries['lieu'].delete(0, tk.END)
        self.fuel_entries['notes'].delete("1.0", tk.END)
        if hasattr(self, 'selected_fuel_entry_id'):
            del self.selected_fuel_entry_id


    # --- Onglet Rapports d'Incident ---
    def create_incident_tab(self):
        """
        Crée les widgets pour l'onglet "Rapports d'Incident".
        """
        self.incident_frame.grid_columnconfigure(0, weight=1)
        self.incident_frame.grid_columnconfigure(1, weight=2)
        self.incident_frame.grid_rowconfigure(0, weight=1)
        self.incident_frame.grid_rowconfigure(1, weight=0)

        input_frame = tk.LabelFrame(self.incident_frame, text="Déclarer un Incident",
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
        self.incident_gravite_combobox = ttk.Combobox(input_frame, textvariable=self.incident_gravite_var, values=self.gravite_types, state="readonly", font=self.font_label)
        self.incident_gravite_combobox.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        if self.gravite_types:
            self.incident_gravite_combobox.set(self.gravite_types[0])


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

        button_frame = tk.Frame(self.incident_frame, bg=self.bg_color_dashboard)
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        add_button = tk.Button(button_frame, text="Ajouter Incident", command=self.add_incident_report, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        update_button = tk.Button(button_frame, text="Modifier Incident", command=self.update_incident_report, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        delete_button = tk.Button(button_frame, text="Supprimer Incident", command=self.delete_incident_report, font=self.font_button_text, bg="#E74C3C", fg=self.button_fg)
        clear_button = tk.Button(button_frame, text="Effacer", command=self.clear_incident_fields, font=self.font_button_text, bg="#7F8C8D", fg=self.button_fg)

        add_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        update_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        delete_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        clear_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        self.incident_tree = ttk.Treeview(self.incident_frame, columns=(
            "ID", "Véhicule", "Date", "Type", "Description", "Gravité", "KM Incident"
        ), show="headings")
        self.incident_tree.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        for col in self.incident_tree["columns"]:
            self.incident_tree.heading(col, text=col, anchor="center")
            self.incident_tree.column(col, width=80, anchor="center")
        self.incident_tree.column("ID", width=30)
        self.incident_tree.column("Description", width=150)

        incident_scrollbar = ttk.Scrollbar(self.incident_frame, orient="vertical", command=self.incident_tree.yview)
        incident_scrollbar.grid(row=0, column=2, rowspan=2, sticky="ns")
        self.incident_tree.configure(yscrollcommand=incident_scrollbar.set)
        self.incident_tree.bind("<<TreeviewSelect>>", self.load_incident_report_into_fields)
        self.populate_incident_reports_treeview()

    def populate_incident_vehicle_options(self):
        """
        Remplit le menu déroulant des véhicules pour l'onglet Incident avec les véhicules attribués au chauffeur.
        """
        vehicles = get_all_vehicles()
        self.incident_vehicle_options = []
        if vehicles:
            for veh_id, immatriculation, *rest in vehicles:
                if (veh_id, immatriculation) not in self.incident_vehicle_options:
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
        
        incident_reports = get_all_incident_reports()
        if incident_reports:
            for report in incident_reports:
                num_cols = len(report)

                ir_id = report[0] if num_cols > 0 else ""
                vehicle_id_ir = report[2] if num_cols > 2 else None
                date_incident_raw = report[3] if num_cols > 3 else None
                type_probleme = report[4] if num_cols > 4 else ""
                description_ir = report[5] if num_cols > 5 else ""
                gravite = report[6] if num_cols > 6 else ""
                kilometrage_incident = report[7] if num_cols > 7 else ""
                
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

    def load_incident_report_into_fields(self, event):
        """
        Load les détails du rapport d'incident sélectionné dans les champs de saisie.
        """
        selected_item = self.incident_tree.focus()
        if not selected_item:
            return

        values = self.incident_tree.item(selected_item, 'values')
        self.selected_incident_id = values[0] 
        self.clear_incident_fields()

        vehicle_immatriculation = values[1]
        for veh_id, veh_immat in self.incident_vehicle_options:
            if veh_immat == vehicle_immatriculation:
                self.incident_selected_vehicle_id.set(veh_id)
                self.incident_vehicle_option_menu.set(vehicle_immatriculation)
                break
        
        try:
            if values[2]:
                self.incident_entries['date_incident'].set_date(datetime.strptime(values[2], "%Y-%m-%d").date())
            else:
                self.incident_entries['date_incident'].set_date(None)
        except ValueError:
            self.incident_entries['date_incident'].set_date(None)
            print(f"Warning: Impossible de convertir la chaîne de date '{values[2]}' pour date_incident. Réinitialisation à vide.")

        self.incident_type_combobox.set(values[3])
        self.incident_entries['description'].delete("1.0", tk.END)
        self.incident_entries['description'].insert("1.0", values[4])
        self.incident_gravite_combobox.set(values[5])
        self.incident_entries['kilometrage_incident'].delete(0, tk.END)
        self.incident_entries['kilometrage_incident'].insert(0, values[6])

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

    def update_incident_report(self):
        """
        Met à jour un rapport d'incident existant dans la base de données.
        """
        selected_item = self.incident_tree.focus()
        if not selected_item:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner un rapport d'incident à modifier.")
            return
        incident_id = self.incident_tree.item(selected_item, 'values')[0]

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

    def delete_incident_report(self):
        """
        Supprime un rapport d'incident de la base de données.
        """
        selected_item = self.incident_tree.focus()
        if not selected_item:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner un rapport d'incident à supprimer.")
            return
        incident_id = self.incident_tree.item(selected_item, 'values')[0]
        if messagebox.askyesno("Confirmer la suppression", f"Êtes-vous sûr de vouloir supprimer le rapport d'incident (ID: {incident_id})?"):
            success, message = delete_incident_report_from_db(incident_id)
            if success:
                messagebox.showinfo("Succès", message)
                self.populate_incident_reports_treeview()
                self.clear_incident_fields()
            else:
                messagebox.showerror("Erreur", message)

    def clear_incident_fields(self):
        """
        Efface les champs de saisie de l'onglet Rapports d'Incident.
        """
        self.populate_incident_vehicle_options()
        self.incident_entries['date_incident'].set_date(datetime.now().date())
        
        if self.incident_types:
            self.incident_type_combobox.set(self.incident_types[0])
        else:
            self.incident_type_combobox.set("")

        self.incident_entries['description'].delete("1.0", tk.END)
        
        if self.gravite_types:
            self.incident_gravite_combobox.set(self.gravite_types[0])
        else:
            self.incident_gravite_combobox.set("")
        
        self.incident_entries['kilometrage_incident'].delete(0, tk.END)
        if hasattr(self, 'selected_incident_id'):
            del self.selected_incident_id

   #-----Historique---
    def create_history_tab(self):
        self.history_frame.grid_columnconfigure(0, weight=1)
        self.history_frame.grid_rowconfigure(0, weight=0)
        self.history_frame.grid_rowconfigure(1, weight=1)
        self.history_frame.grid_rowconfigure(2, weight=0)

        # Cadre pour les filtres
        filter_frame = tk.LabelFrame(self.history_frame, text="Filtres Historique",
                                     bg=self.bg_color_dashboard, fg=self.fg_color_text,
                                     font=self.font_label, bd=2, relief="groove")
        filter_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        filter_frame.grid_columnconfigure(1, weight=1)

        # --- MODIFICATION ICI: Filtre Véhicule - Passage de Combobox à Entry

        
        # Filtre Type d'Événement (aucune modification)
        tk.Label(filter_frame, text="Type d'Événement:", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label).grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.history_event_types = ["Tous", "Attribution", "Maintenance", "Carburant", "Incident", "Inspection"]
        self.history_selected_event_type = tk.StringVar(value="Tous")
        self.history_event_type_combobox = ttk.Combobox(filter_frame, textvariable=self.history_selected_event_type,
                                                         values=self.history_event_types, state="readonly", font=self.font_label)
        self.history_event_type_combobox.grid(row=1, column=1, padx=5, pady=2, sticky="ew")


        # Filtre Date (aucune modification)
        tk.Label(filter_frame, text="Date (exacte):", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label).grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.history_filter_date_entry = DateEntry(filter_frame, width=12, background="darkblue", foreground="white", borderwidth=2,
                                                     font=self.font_label, date_pattern='yyyy-mm-dd')
        self.history_filter_date_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        self.history_filter_date_entry.set_date(None)

        # Boutons de filtre (aucune modification)
        filter_buttons_frame = tk.Frame(filter_frame, bg=self.bg_color_dashboard)
        filter_buttons_frame.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")
        tk.Button(filter_buttons_frame, text="Rechercher", command=self.apply_history_filters, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg).pack(side="left", padx=5, expand=True)
        tk.Button(filter_buttons_frame, text="Réinitialiser Filtres", command=self.clear_history_filters, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg).pack(side="left", padx=5, expand=True)

        self.export_pdf_button = tk.Button(filter_buttons_frame, text="Exporter Historique en PDF",
                                             command=self.export_history_to_pdf, font=self.font_button_text,
                                             bg=self.button_bg, fg=self.button_fg)
        self.export_pdf_button.pack(side="left", padx=5, expand=True)
        
        self.show_detailed_history_button = tk.Button(
            filter_buttons_frame, # Utilisez le même cadre que les autres boutons de filtre
            text="Afficher Historique Détaillé", # Ou un texte plus pertinent
            command=self.show_single_vehicle_history,
            font=self.font_button_text,
            bg=self.button_bg,
            fg=self.button_fg
        )
        self.show_detailed_history_button.pack(side="left", padx=5, expand=True)

        # Conteneur pour le Treeview et le Text (pour basculer l'affichage)
        self.history_display_container = tk.Frame(self.history_frame, bg=self.bg_color_dashboard)
        self.history_display_container.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.history_display_container.grid_columnconfigure(0, weight=1)
        self.history_display_container.grid_rowconfigure(0, weight=1)

        # Treeview pour l'affichage tabulaire (aucune modification)
        self.history_tree = ttk.Treeview(self.history_display_container, columns=(
            "Type", "ID", "Véhicule", "Date", "Description/Détails"
        ), show="headings")
        self.history_tree.grid(row=0, column=0, sticky="nsew")

        for col in self.history_tree["columns"]:
            self.history_tree.heading(col, text=col, anchor="center")
            self.history_tree.column(col, width=120, anchor="center")
        self.history_tree.column("ID", width=50)
        self.history_tree.column("Description/Détails", width=300, anchor="w")

        history_scrollbar = ttk.Scrollbar(self.history_display_container, orient="vertical", command=self.history_tree.yview)
        history_scrollbar.grid(row=0, column=1, sticky="ns")
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)

        # Zone de texte pour l'affichage détaillé d'un seul véhicule (aucune modification)
        self.single_vehicle_history_text = tk.Text(self.history_display_container, wrap="word", font=self.font_label,
                                                     bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text)
        self.single_vehicle_history_text.grid(row=0, column=0, sticky="nsew")
        self.single_vehicle_history_text.grid_remove()

        # Bouton pour revenir au tableau (aucune modification)
        self.back_to_table_button = tk.Button(self.history_frame, text="Retour au Tableau", command=self.show_history_table,
                                                 font=self.font_button_text, bg=self.button_bg, fg=self.button_fg)
        self.back_to_table_button.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.back_to_table_button.grid_remove()

    def on_history_vehicle_selected(self, event=None): # Garder event=None pour la compatibilité
        """
        Cette méthode n'est plus pertinente car le filtre véhicule est un Entry.
        La valeur de self.history_selected_vehicle_id est déjà mise à jour automatiquement par l'Entry.
        """
        pass

    def apply_history_filters(self):
        self.show_history_table() # Assurez-vous que le mode tableau est activé
        
        # selected_veh_id est maintenant directement l'ID saisi dans l'Entry
        selected_veh_id = self.history_selected_vehicle_id.get().strip()
        if selected_veh_id == "": # Traiter le champ vide comme "Tous"
            selected_veh_id = "Tous"

        selected_event_type = self.history_selected_event_type.get()
        selected_date_obj = self.history_filter_date_entry.get_date()
        self.history_filter_date_obj = selected_date_obj

        # Conversion de l'ID véhicule en int si ce n'est pas "Tous"
        filter_veh_id_for_populate = None
        if selected_veh_id != "Tous":
            try:
                filter_veh_id_for_populate = int(selected_veh_id)
            except ValueError:
                messagebox.showwarning("Erreur de saisie", "L'ID Véhicule doit être un nombre entier ou laissé vide pour 'Tous'.")
                return # Arrête l'application des filtres si l'ID est invalide

        self.populate_history_treeview(
            vehicle_id=filter_veh_id_for_populate,
            event_type=selected_event_type if selected_event_type != "Tous" else None,
            filter_date=selected_date_obj
        )

    def clear_history_filters(self):
        self.history_selected_vehicle_id.set("") # Vide le champ de saisie
        # self.history_vehicle_combobox.set("Tous les véhicules") # Cette ligne est supprimée
        self.history_selected_event_type.set("Tous")
        self.history_filter_date_entry.set_date(None)
        self.history_filter_date_obj = None
        self.populate_history_treeview()

    def show_single_vehicle_history(self):
        selected_veh_id_val = self.history_selected_vehicle_id.get().strip()
        
        # Vérifier si l'ID est vide, "Tous" ou non numérique
        if not selected_veh_id_val or selected_veh_id_val == "Tous" or not selected_veh_id_val.isdigit():
            messagebox.showwarning("Sélection requise", "Veuillez saisir un ID de véhicule valide (numérique) pour afficher l'historique détaillé.")
            return

        selected_veh_id_int = int(selected_veh_id_val)

        self.history_tree.grid_remove()
        self.single_vehicle_history_text.grid()
        self.back_to_table_button.grid()
        
        # Gérer les boutons Afficher/Exporter en mode détaillé
        self.export_pdf_button.pack(side="left", padx=5, expand=True) 
        self.show_detailed_history_button.pack_forget() 

        self.single_vehicle_history_text.config(state=tk.NORMAL)
        self.single_vehicle_history_text.delete("1.0", tk.END)

        vehicle_info = get_vehicle_by_id(selected_veh_id_int)
        if not vehicle_info:
            self.single_vehicle_history_text.insert(tk.END, f"Aucun détail trouvé pour le véhicule ID: {selected_veh_id_int}\n")
            self.single_vehicle_history_text.config(state=tk.DISABLED)
            return

        veh_immat = vehicle_info[1]
        self.single_vehicle_history_text.insert(tk.END, f"--- Historique Détaillé du Véhicule: {veh_immat} (ID: {selected_veh_id_int}) ---\n\n")

        user_map = {u[0]: f"{u[4]} {u[3]}" for u in get_all_chauffeurs_and_responsables()}

        attributions = get_all_attributions()
        vehicle_attributions = sorted([a for a in attributions if len(a) > 2 and a[2] == selected_veh_id_int], 
                                     key=lambda x: self._safe_parse_date(x[4]), reverse=True) 
        if vehicle_attributions:
            self.single_vehicle_history_text.insert(tk.END, "ATTRIBUTIONS:\n")
            for attr in vehicle_attributions:
                chauffeur_name = user_map.get(attr[1], "Chauffeur inconnu")
                self.single_vehicle_history_text.insert(tk.END, f"  - ID: {attr[0]}, Chauffeur: {chauffeur_name}, Début: {self._format_date_for_treeview(attr[4])}, Fin Prévue: {self._format_date_for_treeview(attr[5])}, Fin Réelle: {self._format_date_for_treeview(attr[6]) if len(attr)>6 and attr[6] else 'N/A'}, KM Init: {attr[7] if len(attr)>7 else 'N/A'}, KM Fin: {attr[8] if len(attr)>8 and attr[8] is not None else 'N/A'}, Statut: {attr[12] if len(attr)>12 else 'N/A'}, Obs: {attr[11] if len(attr)>11 and attr[11] else 'N/A'}\n")
            self.single_vehicle_history_text.insert(tk.END, "\n")

        maintenances = get_all_maintenances()
        vehicle_maintenances = sorted([m for m in maintenances if len(m) > 10 and m[10] == selected_veh_id_int],
                                     key=lambda x: self._safe_parse_date(x[3]), reverse=True)
        if vehicle_maintenances:
            self.single_vehicle_history_text.insert(tk.END, "MAINTENANCES:\n")
            for maint in vehicle_maintenances:
                self.single_vehicle_history_text.insert(tk.END, f"  - ID: {maint[0]}, Type: {maint[2]}, Date: {self._format_date_for_treeview(maint[3])}, Coût: {maint[4]} MGA, Desc: {maint[5]}, Proch. KM: {maint[7]}, Proch. Date: {self._format_date_for_treeview(maint[8])}\n")
            self.single_vehicle_history_text.insert(tk.END, "\n")

        fuel_entries = get_all_fuel_entries()
        vehicle_fuel_entries = sorted([f for f in fuel_entries if len(f) > 13 and f[13] == selected_veh_id_int],
                                     key=lambda x: self._safe_parse_date(x[4]), reverse=True)
        if vehicle_fuel_entries:
            self.single_vehicle_history_text.insert(tk.END, "CARBURANT:\n")
            for entry in vehicle_fuel_entries:
                user_name = user_map.get(entry[12], "Inconnu")
                self.single_vehicle_history_text.insert(tk.END, f"  - ID: {entry[0]}, Par: {user_name}, Date: {self._format_date_for_treeview(entry[4])}, Type: {entry[5]}, Qté: {entry[6]} L, Coût: {entry[7]} MGA, KM Relevé: {entry[9]}, Lieu: {entry[10]}, Notes: {entry[11]}\n")
            self.single_vehicle_history_text.insert(tk.END, "\n")

        incident_reports = get_all_incident_reports()
        vehicle_incident_reports = sorted([i for i in incident_reports if len(i) > 2 and i[2] == selected_veh_id_int],
                                         key=lambda x: self._safe_parse_date(x[3]), reverse=True)
        if vehicle_incident_reports:
            self.single_vehicle_history_text.insert(tk.END, "RAPPORTS D'INCIDENT:\n")
            for report in vehicle_incident_reports:
                user_name = user_map.get(report[1], "Inconnu")
                self.single_vehicle_history_text.insert(tk.END, f"  - ID: {report[0]}, Par: {user_name}, Date: {self._format_date_for_treeview(report[3])}, Type: {report[4]}, Gravité: {report[6]}, KM: {report[7]}, Desc: {report[5]}\n")
            self.single_vehicle_history_text.insert(tk.END, "\n")
        
        inspection_reports = get_all_vehicle_inspection_reports()
        vehicle_inspection_reports = sorted([i for i in inspection_reports if len(i) > 2 and i[2] == selected_veh_id_int],
                                             key=lambda x: self._safe_parse_date(x[3]), reverse=True)
        if vehicle_inspection_reports:
            self.single_vehicle_history_text.insert(tk.END, "RAPPORTS D'INSPECTION:\n")
            for report in vehicle_inspection_reports:
                user_name = user_map.get(report[1], "Inconnu")
                self.single_vehicle_history_text.insert(tk.END, f"  - ID: {report[0]}, Par: {user_name}, Date: {self._format_date_for_treeview(report[3])}, État Général: {report[4]}, Carburant: {report[5]}%, Huile OK: {'Oui' if report[7] else 'Non'}, Refroid. OK: {'Oui' if report[8] else 'Non'}, Feux OK: {'Oui' if report[9] else 'Non'}, Clign. OK: {'Oui' if report[10] else 'Non'}, Pneus OK: {'Oui' if report[11] else 'Non'}, Carrosserie OK: {'Oui' if report[12] else 'Non'}, Obs: {report[6]}\n")
            self.single_vehicle_history_text.insert(tk.END, "\n")

        if not (vehicle_attributions or vehicle_maintenances or vehicle_fuel_entries or vehicle_incident_reports or vehicle_inspection_reports):
            self.single_vehicle_history_text.insert(tk.END, "Aucune opération trouvée pour ce véhicule.\n")
        
        self.single_vehicle_history_text.config(state=tk.DISABLED)

    def show_history_table(self):
        self.single_vehicle_history_text.grid_remove()
        self.back_to_table_button.grid_remove()
        
        self.history_tree.grid()
        
        self.export_pdf_button.pack(side="left", padx=5, expand=True)
        self.show_detailed_history_button.pack(side="left", padx=5, expand=True)
        
        # Pour le retour au tableau, assurez-vous que les filtres sont réappliqués correctement
        # L'ID véhicule provient maintenant de l'Entry, non d'un combobox
        selected_veh_id = self.history_selected_vehicle_id.get().strip()
        filter_veh_id_for_populate = None
        if selected_veh_id and selected_veh_id != "Tous":
            try:
                filter_veh_id_for_populate = int(selected_veh_id)
            except ValueError:
                # Si l'ID est invalide, on ne filtre pas par véhicule.
                # Ou on pourrait afficher un message d'erreur.
                filter_veh_id_for_populate = None 

        self.populate_history_treeview(
            vehicle_id=filter_veh_id_for_populate,
            event_type=self.history_selected_event_type.get() if self.history_selected_event_type.get() != "Tous" else None,
            filter_date=self.history_filter_date_entry.get_date()
        )

    def populate_history_treeview(self, vehicle_id=None, event_type=None, filter_date=None):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        all_entries = []

        filter_vehicle_id_int = None
        if vehicle_id is not None and (isinstance(vehicle_id, int) or (isinstance(vehicle_id, str) and vehicle_id.isdigit())):
            try:
                filter_vehicle_id_int = int(vehicle_id)
            except ValueError:
                pass # L'ID est invalide, ne pas filtrer par ID véhicule

        vehicle_map = {v[0]: v[1] for v in get_all_vehicles()}
        user_map = {u[0]: f"{u[4]} {u[3]}" for u in get_all_chauffeurs_and_responsables()}

        # Attributions
        if event_type is None or event_type == "Attribution":
            attributions = get_all_attributions()
            for attr in attributions:
                if len(attr) < 13: continue 
                
                attr_db_vehicle_id = attr[2] 
                attr_date_start = attr[4]
                formatted_date_start = self._format_date_for_treeview(attr_date_start)

                if (filter_vehicle_id_int is None or attr_db_vehicle_id == filter_vehicle_id_int) and \
                   (filter_date is None or formatted_date_start == filter_date.strftime("%Y-%m-%d")):
                    
                    chauffeur_nom_complet = user_map.get(attr[1], "Chauffeur inconnu")
                    veh_immat_display = vehicle_map.get(attr_db_vehicle_id, "Véhicule inconnu") 
                    
                    details = f"Chauffeur: {chauffeur_nom_complet}, KM Init: {attr[7]}, KM Fin: {attr[8] if attr[8] is not None else 'N/A'}, Statut: {attr[12]}, Notes: {attr[11] if attr[11] else 'N/A'}"
                    all_entries.append(("Attribution", attr[0], veh_immat_display, formatted_date_start, details))
                    
                    if attr[6]: 
                        formatted_date_end_real = self._format_date_for_treeview(attr[6])
                        if (filter_date is None or formatted_date_end_real == filter_date.strftime("%Y-%m-%d")):
                            all_entries.append(("Attribution (Fin)", attr[0], veh_immat_display, formatted_date_end_real, f"Clôture. KM Final: {attr[8] if attr[8] is not None else 'N/A'}"))

        # Maintenances
        if event_type is None or event_type == "Maintenance":
            maintenances = get_all_maintenances()
            for maint in maintenances:
                if len(maint) < 11: continue 
                maint_db_vehicle_id = maint[10]
                maint_db_date = maint[3]

                formatted_maint_date = self._format_date_for_treeview(maint_db_date)

                if (filter_vehicle_id_int is None or maint_db_vehicle_id == filter_vehicle_id_int) and \
                   (filter_date is None or formatted_maint_date == filter_date.strftime("%Y-%m-%d")):

                    veh_immat_display = vehicle_map.get(maint_db_vehicle_id, "Véhicule inconnu") 
                    details = f"Type: {maint[2]}, Coût: {maint[4]} MGA, Description: {maint[5]}, Proch. KM: {maint[7] if maint[7] else 'N/A'}, Proch. Date: {self._format_date_for_treeview(maint[8]) if maint[8] else 'N/A'}"
                    all_entries.append(("Maintenance", maint[0], veh_immat_display, formatted_maint_date, details))

        # Carburant
        if event_type is None or event_type == "Carburant":
            fuel_entries = get_all_fuel_entries()
            for entry in fuel_entries:
                if len(entry) < 14: continue 
                fuel_db_vehicle_id = entry[13]
                fuel_db_date = entry[4]

                formatted_fuel_date = self._format_date_for_treeview(fuel_db_date)

                if (filter_vehicle_id_int is None or fuel_db_vehicle_id == filter_vehicle_id_int) and \
                   (filter_date is None or formatted_fuel_date == filter_date.strftime("%Y-%m-%d")):

                    veh_immat_display = vehicle_map.get(fuel_db_vehicle_id, "Véhicule inconnu") 
                    details = f"Type: {entry[5]}, Quantité: {entry[6]} L, Coût: {entry[7]} MGA, KM Relevé: {entry[9]}, Lieu: {entry[10]}, Notes: {entry[11]}"
                    all_entries.append(("Carburant", entry[0], veh_immat_display, formatted_fuel_date, details))

        # Incidents
        if event_type is None or event_type == "Incident":
            incident_reports = get_all_incident_reports()
            for report in incident_reports:
                if len(report) < 8: continue 
                incident_db_vehicle_id = report[2]
                incident_db_date = report[3]

                formatted_incident_date = self._format_date_for_treeview(incident_db_date)

                if (filter_vehicle_id_int is None or incident_db_vehicle_id == filter_vehicle_id_int) and \
                   (filter_date is None or formatted_incident_date == filter_date.strftime("%Y-%m-%d")):

                    veh_immat_display = vehicle_map.get(incident_db_vehicle_id, "Véhicule inconnu")
                    details = f"Type: {report[4]}, Gravité: {report[6]}, KM Incident: {report[7]}, Description: {report[5]}"
                    all_entries.append(("Incident", report[0], veh_immat_display, formatted_incident_date, details))

        # Inspections
        if event_type is None or event_type == "Inspection":
            inspection_reports = get_all_vehicle_inspection_reports()
            for report in inspection_reports:
                if len(report) < 13: continue 
                inspection_db_vehicle_id = report[2]
                inspection_db_date = report[3]

                formatted_inspection_date = self._format_date_for_treeview(inspection_db_date)

                if (filter_vehicle_id_int is None or inspection_db_vehicle_id == filter_vehicle_id_int) and \
                   (filter_date is None or formatted_inspection_date == filter_date.strftime("%Y-%m-%d")):

                    veh_immat_display = vehicle_map.get(inspection_db_vehicle_id, "Véhicule inconnu")

                    details = (
                        f"État Général: {report[4]}, Carburant: {report[5]}%, "
                        f"Huile OK: {'Oui' if report[7] else 'Non'}, Refroid. OK: {'Oui' if report[8] else 'Non'}, "
                        f"Feux OK: {'Oui' if report[9] else 'Non'}, Clign. OK: {'Oui' if report[10] else 'Non'}, "
                        f"Pneus OK: {'Oui' if report[11] else 'Non'}, Carrosserie OK: {'Oui' if report[12] else 'Non'}. "
                        f"Observations: {report[6] if report[6] else 'N/A'}"
                    )
                    all_entries.append(("Inspection", report[0], veh_immat_display, formatted_inspection_date, details))

        all_entries.sort(key=lambda x: self._safe_parse_date(x[3]), reverse=True)

        for entry in all_entries:
            self.history_tree.insert("", "end", values=entry)

    def export_history_to_pdf(self):
        """
        Exporte l'historique vers un fichier PDF.
        Si le mode détaillé d'un véhicule est activé, il exporte le texte détaillé.
        Sinon, il exporte le tableau général sous forme de texte brut.
        """
        # Ensure ReportLab is available
        if SimpleDocTemplate is None: 
            messagebox.showerror("Erreur", "Le module ReportLab n'est pas disponible. Veuillez l'installer pour exporter en PDF.")
            return

        filename_prefix = ""
        # Check if the detailed text widget is currently mapped (visible)
        if self.single_vehicle_history_text.winfo_ismapped(): 
            selected_veh_id_val = self.history_selected_vehicle_id.get().strip()
            if selected_veh_id_val and selected_veh_id_val.isdigit():
                vehicle_info = get_vehicle_by_id(int(selected_veh_id_val))
                if vehicle_info:
                    filename_prefix = f"Historique_Vehicule_{vehicle_info[1].replace(' ', '_').replace('/', '_')}_Detaille"
                else:
                    filename_prefix = "Historique_Detaille_Inconnu"
            else:
                filename_prefix = "Historique_Detaille_Vehicule_Non_Selectionne"
        else: # Table mode (Treeview is visible)
            filter_parts = []
            
            # Utiliser la valeur de l'Entry pour le nom du fichier
            current_vehicle_id_filter = self.history_selected_vehicle_id.get().strip()
            if current_vehicle_id_filter and current_vehicle_id_filter != "Tous":
                 # Tenter de trouver l'immatriculation pour le nom du fichier
                try:
                    veh_info = get_vehicle_by_id(int(current_vehicle_id_filter))
                    if veh_info:
                        filter_parts.append(f"Vehicule_{veh_info[1].replace(' ', '_').replace('/', '_')}")
                    else:
                        filter_parts.append(f"Vehicule_ID_{current_vehicle_id_filter}")
                except ValueError: # Si ce n'est pas un nombre
                    filter_parts.append(f"Vehicule_ID_{current_vehicle_id_filter.replace(' ', '_')}")
            
            if self.history_selected_event_type.get() != "Tous":
                filter_parts.append(f"Type_{self.history_selected_event_type.get()}")
            if self.history_filter_date_obj:
                filter_parts.append(f"Date_{self.history_filter_date_obj.strftime('%Y%m%d')}")
            
            filename_prefix = "_".join(filter_parts) if filter_parts else "Historique_Global_Tableau" # Nom mis à jour

        suggested_filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        file_path = filedialog.asksaveasfilename(
            initialdir=getattr(self, 'pdf_export_dir', os.path.expanduser("~")), 
            initialfile=suggested_filename,
            defaultextension=".pdf",
            filetypes=[("Fichiers PDF", "*.pdf"), ("Tous les fichiers", "*.*")],
            title="Enregistrer l'historique en PDF"
        )
        if not file_path:
            return

        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        if hasattr(self, 'logo_path') and self.logo_path and os.path.exists(self.logo_path):
            try:
                # Assurez-vous que l'image est ouverte correctement par PIL avant de passer à ReportLab
                pil_image = Image.open(self.logo_path)
                # Redimensionner l'image si nécessaire pour l'affichage dans le PDF
                img_width, img_height = pil_image.size
                aspect_ratio = img_height / img_width
                new_width = 50 # Taille fixe
                new_height = new_width * aspect_ratio
                
                img = Image(self.logo_path, width=new_width, height=new_height) 
                img.hAlign = 'RIGHT' 
                story.append(img)
                story.append(Spacer(1, 0.1 * inch))
            except Exception as e:
                print(f"Erreur lors de l'insertion du logo dans le PDF: {e}")
                messagebox.showwarning("Erreur PDF", f"Impossible d'ajouter le logo au PDF: {e}. Vérifiez le chemin et le format de l'image.")

        story.append(Paragraph(f"<b>Historique des Opérations de Flotte</b>", styles['h1']))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(f"Date de génération : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"Responsable : {self.logged_in_user_fullname}", styles['Normal']))
        story.append(Paragraph(f'Nom de la Société : <font color="#FF0000"><b>Toutadom</b></font>', styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

        # --- Logique pour l'exportation en mode texte ou tableau ---
        if self.single_vehicle_history_text.winfo_ismapped(): 
            history_content = self.single_vehicle_history_text.get("1.0", tk.END).strip()
            if not history_content:
                story.append(Paragraph("Aucun historique détaillé à exporter. Veuillez d'abord afficher l'historique d'un véhicule.", styles['Normal']))
            else:
                lines = history_content.split('\n')
                for line in lines:
                    # Utiliser le style 'Normal' pour un meilleur formatage, ou 'Code' si vous préférez une police mono
                    # Échapper les caractères spéciaux HTML
                    safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    story.append(Paragraph(safe_line, styles['Normal']))
        else: # Mode Tableau (Treeview est visible)
            filters_applied = []
            
            current_vehicle_id_filter = self.history_selected_vehicle_id.get().strip()
            if current_vehicle_id_filter and current_vehicle_id_filter != "Tous":
                 # Tenter de trouver l'immatriculation pour l'affichage
                try:
                    veh_info = get_vehicle_by_id(int(current_vehicle_id_filter))
                    if veh_info:
                        filters_applied.append(f"Véhicule: {veh_info[1]}")
                    else:
                        filters_applied.append(f"Véhicule (ID): {current_vehicle_id_filter}")
                except ValueError:
                    filters_applied.append(f"Véhicule (ID invalide): {current_vehicle_id_filter}")

            if self.history_selected_event_type.get() != "Tous":
                filters_applied.append(f"Type d'Événement: {self.history_selected_event_type.get()}")
            if self.history_filter_date_obj:
                filters_applied.append(f"Date: {self.history_filter_date_obj.strftime('%Y-%m-%d')}")
            
            if filters_applied:
                story.append(Paragraph("<b>Filtres Appliqués:</b> " + ", ".join(filters_applied), styles['Normal']))
                story.append(Spacer(1, 0.1 * inch))

            # Récupérer les données du Treeview
            data = [self.history_tree.item(item, 'values') for item in self.history_tree.get_children()]
            
            if not data:
                story.append(Paragraph("Aucune donnée d'historique disponible avec les filtres actuels pour l'exportation.", styles['Normal']))
            else:
                # Créer un texte formaté pour le PDF au lieu d'un tableau
                story.append(Paragraph("<b>Données de l'Historique:</b>", styles['h3']))
                story.append(Spacer(1, 0.1 * inch))

                for i, row_values in enumerate(data):
                    # Formater chaque ligne comme un paragraphe de texte
                    # Échapper les caractères spéciaux HTML
                    type_val = str(row_values[0]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    id_val = str(row_values[1]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    vehicle_val = str(row_values[2]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    date_val = str(row_values[3]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    details_val = str(row_values[4]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                    formatted_entry = f"<b>Événement {i+1}:</b><br/>" \
                                      f"  <b>Type:</b> {type_val}<br/>" \
                                      f"  <b>ID:</b> {id_val}<br/>" \
                                      f"  <b>Véhicule:</b> {vehicle_val}<br/>" \
                                      f"  <b>Date:</b> {date_val}<br/>" \
                                      f"  <b>Détails:</b> {details_val}<br/><br/>"
                    
                    story.append(Paragraph(formatted_entry, styles['Normal'])) # Utiliser style Normal pour le texte
                    story.append(Spacer(1, 0.05 * inch)) # Petit espace entre les entrées


        try:
            doc.build(story)
            messagebox.showinfo("Export PDF", f"L'historique a été exporté avec succès vers :\n{file_path}")
        except Exception as e:
            messagebox.showerror("Erreur Export PDF", f"Une erreur est survenue lors de l'exportation du PDF : {e}")

# --- NEW STATISTICS TAB CODE ---

    def create_statistics_tab(self):
        self.statistics_frame.grid_columnconfigure(0, weight=1)
        self.statistics_frame.grid_rowconfigure(0, weight=0)
        self.statistics_frame.grid_rowconfigure(1, weight=1)

        # Filters for statistics
        filter_frame = tk.LabelFrame(self.statistics_frame, text="Filtres Statistiques",
                                     bg=self.bg_color_dashboard, fg=self.fg_color_text,
                                     font=self.font_label, bd=2, relief="groove")
        filter_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        filter_frame.grid_columnconfigure(1, weight=1)

        tk.Label(filter_frame, text="Véhicule (ID/Immat.):", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label).grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.stat_vehicle_var = tk.StringVar(value="Tous")
        self.stat_vehicle_options = self._get_vehicle_options_for_stats()
        self.stat_vehicle_combobox = ttk.Combobox(filter_frame, textvariable=self.stat_vehicle_var,
                                                 values=self.stat_vehicle_options, state="readonly", font=self.font_label)
        self.stat_vehicle_combobox.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.stat_vehicle_combobox.bind("<<ComboboxSelected>>", self.populate_statistics_dashboard)

        
        # NOUVEAU: Choix de la période
        tk.Label(filter_frame, text="Période :", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label).grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.stat_period_var = tk.StringVar(value="Personnalisé")
        self.stat_period_combobox = ttk.Combobox(filter_frame, textvariable=self.stat_period_var,
                                                 values=["Jour", "Semaine", "Mois", "Personnalisé"], state="readonly", font=self.font_label)
        self.stat_period_combobox.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.stat_period_combobox.bind("<<ComboboxSelected>>", self._on_period_selected)

        # Champs de date de début et de fin (initialement visibles)
        self.start_date_label = tk.Label(filter_frame, text="Période (Début):", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        self.start_date_label.grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.stat_start_date_entry = DateEntry(filter_frame, width=12, background="darkblue", foreground="white", borderwidth=2,
                                                font=self.font_label, date_pattern='yyyy-mm-dd')
        self.stat_start_date_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        self.stat_start_date_entry.set_date(None)

        self.end_date_label = tk.Label(filter_frame, text="Période (Fin):", bg=self.bg_color_dashboard, fg=self.fg_color_text, font=self.font_label)
        self.end_date_label.grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.stat_end_date_entry = DateEntry(filter_frame, width=12, background="darkblue", foreground="white", borderwidth=2,
                                             font=self.font_label, date_pattern='yyyy-mm-dd')
        self.stat_end_date_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        self.stat_end_date_entry.set_date(None)

        button_frame = tk.Frame(filter_frame, bg=self.bg_color_dashboard)
        button_frame.grid(row=4, column=0, columnspan=2, pady=5, sticky="ew")
        tk.Button(button_frame, text="Appliquer Filtres", command=self.populate_statistics_dashboard, font=self.font_button_text, bg=self.button_bg, fg=self.button_fg).pack(side="left", padx=5, expand=True)
        tk.Button(button_frame, text="Réinitialiser Filtres", command=self.clear_statistics_filters, font=self.font_button_text, bg="#7F8C8D", fg=self.button_fg).pack(side="left", padx=5, expand=True)
        # NOUVEAU: Bouton Exporter en PDF
        tk.Button(button_frame, text="Exporter PDF", command=self.export_statistics_to_pdf, font=self.font_button_text, bg=self.accent_color, fg=self.button_fg).pack(side="left", padx=5, expand=True)


        # Statistics Display Area - Container for text and graphs
        self.stats_display_frame = tk.Frame(self.statistics_frame, bg=self.bg_color_dashboard)
        self.stats_display_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.stats_display_frame.grid_columnconfigure(0, weight=1)
        self.stats_display_frame.grid_rowconfigure(0, weight=1) # Row for Text Output
        self.stats_display_frame.grid_rowconfigure(1, weight=3) # Row for Graphs (gives more space)

        # Text output (existing)
        # Dans la méthode create_statistics_tab
        self.statistics_text_output = tk.Text(self.stats_display_frame, wrap="word", font=self.font_label,
                                     bg=self.entry_bg, fg=self.fg_color_text, insertbackground=self.fg_color_text)
        self.statistics_text_output.grid(row=0, column=0, sticky="nsew")
        self.statistics_text_output.config(state=tk.DISABLED)

        # Frame for Matplotlib Graphs (this will hold the canvas)
        self.graph_container_frame = tk.Frame(self.stats_display_frame, bg=self.bg_color_dashboard)
        self.graph_container_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.graph_container_frame.grid_columnconfigure(0, weight=1)
        self.graph_container_frame.grid_rowconfigure(0, weight=1)

        # Initialisation de la Figure Matplotlib avec des subplots
        self.fig, self.axes = plt.subplots(2, 2, figsize=(10, 8), facecolor=self.bg_color_dashboard)
        # self.axes est maintenant un tableau NumPy d'axes (subplots)
        # self.axes[0,0] pour le premier en haut à gauche
        # self.axes[0,1] pour le premier en haut à droite
        # self.axes[1,0] pour le premier en bas à gauche
        # self.axes[1,1] pour le premier en bas à droite

        # Ajuster les couleurs de fond de la figure pour correspondre au thème
        self.fig.set_facecolor(self.bg_color_dashboard)

        # Création du Canvas Tkinter pour la Figure Matplotlib
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_container_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Optionnel: Barre d'outils (zoom, pan, save)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.graph_container_frame)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Nettoyage initial des graphiques et message de chargement
        for ax in self.axes.flatten(): # Itérer sur tous les subplots
            ax.clear()
            ax.set_facecolor(self.entry_bg) # Couleur de fond du plot
            ax.tick_params(axis='x', colors=self.fg_color_text)
            ax.tick_params(axis='y', colors=self.fg_color_text)
            ax.spines['left'].set_color(self.fg_color_text)
            ax.spines['bottom'].set_color(self.fg_color_text)
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
        self.axes[0,0].text(0.5, 0.5, "Chargement des statistiques...",
                            horizontalalignment='center', verticalalignment='center',
                            transform=self.axes[0,0].transAxes, fontsize=10, color=self.fg_color_text)
        self.fig.tight_layout() # Ajuste la mise en page
        self.canvas.draw()

        # Appeler la fonction pour ajuster la visibilité au démarrage
        self._on_period_selected()


    def _on_period_selected(self, event=None):
        selected_period = self.stat_period_var.get()
        today = date.today()

        if selected_period == "Personnalisé":
            self.start_date_label.grid(row=2, column=0, padx=5, pady=2, sticky="w")
            self.stat_start_date_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
            self.end_date_label.grid(row=3, column=0, padx=5, pady=2, sticky="w")
            self.stat_end_date_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        else:
            self.start_date_label.grid_forget()
            self.stat_start_date_entry.grid_forget()
            self.end_date_label.grid_forget()
            self.stat_end_date_entry.grid_forget()

            # Définir les dates en fonction de la sélection
            if selected_period == "Jour":
                self.stat_start_date_entry.set_date(today)
                self.stat_end_date_entry.set_date(today)
            elif selected_period == "Semaine":
                # Début de la semaine (Lundi)
                start_of_week = today - timedelta(days=today.weekday())
                self.stat_start_date_entry.set_date(start_of_week)
                self.stat_end_date_entry.set_date(start_of_week + timedelta(days=6)) # Fin de semaine (Dimanche)
            elif selected_period == "Mois":
                start_of_month = today.replace(day=1)
                # Calcule le dernier jour du mois
                if today.month == 12:
                    end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
                self.stat_start_date_entry.set_date(start_of_month)
                self.stat_end_date_entry.set_date(end_of_month)

        # Optionnel: Appeler populate_statistics_dashboard si la période change
        # self.populate_statistics_dashboard() # <-- Cette ligne doit rester COMMENTÉE pour éviter l'erreur d'initialisation


    def populate_statistics_dashboard(self, event=None):
        """
        Calculates and displays various statistics based on filters.
        """
        self.statistics_text_output.config(state=tk.NORMAL)
        self.statistics_text_output.delete("1.0", tk.END)

        # Effacer tous les subplots avant de redessiner
        for ax in self.axes.flatten():
            ax.clear()
            ax.set_facecolor(self.entry_bg) # Reset background color for each subplot
            ax.tick_params(axis='x', colors=self.fg_color_text)
            ax.tick_params(axis='y', colors=self.fg_color_text)
            ax.spines['left'].set_color(self.fg_color_text)
            ax.spines['bottom'].set_color(self.fg_color_text)
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)


        selected_vehicle_str = self.stat_vehicle_var.get()
        filter_start_date = self.stat_start_date_entry.get_date()
        filter_end_date = self.stat_end_date_entry.get_date()

        target_vehicle_id = None
        if selected_vehicle_str != "Tous":
            try:
                target_vehicle_id = int(selected_vehicle_str.split(' - ')[0])
            except ValueError:
                messagebox.showwarning("Erreur de saisie", "Veuillez sélectionner un véhicule valide.")
                self.statistics_text_output.config(state=tk.DISABLED)
                self.axes[0,0].text(0.5, 0.5, "Sélection de véhicule invalide.",
                                 horizontalalignment='center', verticalalignment='center',
                                 transform=self.axes[0,0].transAxes, fontsize=12, color='red')
                self.fig.tight_layout()
                self.canvas.draw()
                return

        # --- Fetch Data ---
        all_attributions = get_all_attributions()
        all_maintenances = get_all_maintenances()
        all_fuel_entries = get_all_fuel_entries()
        all_incident_reports = get_all_incident_reports()
        all_vehicles = get_all_vehicles()

        # --- Filter Data ---
        filtered_vehicles = [v for v in all_vehicles if target_vehicle_id is None or v[0] == target_vehicle_id]
        filtered_attributions = []
        for attr in all_attributions:
            if len(attr) > 2:
                try:
                    # Conversion de date_attribution (index 3) et date_retour_reelle (index 5) si elles sont sous forme de chaîne
                    # Pour les attributions, nous filtrons généralement par date d'attribution ou de retour.
                    # Utilisons date_attribution (index 3) ici pour la cohérence avec les autres logs.
                    attr_date = self._safe_parse_date(attr[3]) # Attentions aux indices, l'exemple donnait [4] avant
                    vehicle_id_from_attr = int(attr[2])
                    if (target_vehicle_id is None or vehicle_id_from_attr == target_vehicle_id) \
                       and self._is_date_in_range(attr_date, filter_start_date, filter_end_date):
                        filtered_attributions.append(attr)
                except (ValueError, TypeError, IndexError):
                    print(f"DEBUG: Skipping invalid attribution entry (non-numeric vehicle ID or date error): {attr}")


        filtered_maintenances = []
        for maint in all_maintenances:
            if len(maint) > 10:
                try:
                    vehicle_id_from_maint = int(maint[8]) # Ajustez l'indice si nécessaire
                    maint_date = self._safe_parse_date(maint[3])
                    if (target_vehicle_id is None or vehicle_id_from_maint == target_vehicle_id) \
                       and self._is_date_in_range(maint_date, filter_start_date, filter_end_date):
                        filtered_maintenances.append(maint)
                except (ValueError, TypeError, IndexError):
                    print(f"DEBUG: Skipping invalid maintenance entry (non-numeric vehicle ID or date error): {maint}")


        filtered_fuel_entries = []
        for fuel in all_fuel_entries:
            if len(fuel) > 13: # Adjust index based on your fuel entry structure
                try:
                    vehicle_id_from_fuel = int(fuel[2]) # Ajustez l'indice si nécessaire
                    fuel_date = self._safe_parse_date(fuel[4])
                    if (target_vehicle_id is None or vehicle_id_from_fuel == target_vehicle_id) \
                       and self._is_date_in_range(fuel_date, filter_start_date, filter_end_date):
                        filtered_fuel_entries.append(fuel)
                except (ValueError, TypeError, IndexError):
                    print(f"DEBUG: Skipping invalid fuel entry (non-numeric vehicle ID or date error): {fuel}")


        filtered_incident_reports = []
        for inc in all_incident_reports:
            if len(inc) > 2:
                try:
                    vehicle_id_from_inc = int(inc[2])
                    incident_date = self._safe_parse_date(inc[3])
                    if (target_vehicle_id is None or vehicle_id_from_inc == target_vehicle_id) \
                       and self._is_date_in_range(incident_date, filter_start_date, filter_end_date):
                        filtered_incident_reports.append(inc)
                except (ValueError, TypeError, IndexError):
                    print(f"DEBUG: Skipping invalid incident report entry (non-numeric vehicle ID or date error): {inc}")

        # --- General Statistics ---
        self.statistics_text_output.insert(tk.END, "--- Statistiques Générales ---\n\n")

        self.statistics_text_output.insert(tk.END, f"Nombre total de véhicules : {len(all_vehicles)}\n")
        self.statistics_text_output.insert(tk.END, f"Nombre de véhicules filtrés : {len(filtered_vehicles)}\n\n")

        # --- Mileage Statistics ---
        total_mileage_attributed = 0
        for attr in filtered_attributions:
            if len(attr) > 8 and attr[7] is not None and attr[8] is not None:
                try:
                    total_mileage_attributed += (attr[8] - attr[7])
                except TypeError:
                    print(f"DEBUG: Skipping mileage calculation for attribution due to non-numeric km: {attr}")
                    pass

        total_mileage_from_fuel = 0
        last_odometer_reading = {}
        # Ensure fuel_entry[9] (kilometrage) and fuel_entry[4] (date_plein) are correctly indexed
        # Assuming fuel data: (id, id_carburant, vehicule_id, chauffeur_id, date_plein, type_carburant, quantite, cout_total, lieu, kilometrage, type_paiement, num_facture, observations)
        for fuel_entry in sorted(filtered_fuel_entries, key=lambda x: self._safe_parse_date(x[4])):
            try:
                veh_id = int(fuel_entry[2]) # vehicle_id is at index 2
                current_odometer = fuel_entry[9] # kilometrage is at index 9
                if veh_id in last_odometer_reading and current_odometer is not None and last_odometer_reading[veh_id] is not None:
                    try:
                        total_mileage_from_fuel += (current_odometer - last_odometer_reading[veh_id])
                    except TypeError:
                        print(f"DEBUG: Skipping mileage calculation for fuel due to non-numeric odometer: {fuel_entry}")
                        pass
                last_odometer_reading[veh_id] = current_odometer
            except (ValueError, IndexError, TypeError):
                print(f"DEBUG: Skipping fuel entry for mileage calculation due to invalid data: {fuel_entry}")
                pass

        self.statistics_text_output.insert(tk.END, "--- Kilométrage ---\n")
        self.statistics_text_output.insert(tk.END, f"Kilométrage total des attributions filtrées : {total_mileage_attributed:.2f} KM\n")
        self.statistics_text_output.insert(tk.END, f"Kilométrage estimé (basé sur carburant) : {total_mileage_from_fuel:.2f} KM\n\n")


        # --- Fuel Consumption Statistics ---
        total_fuel_cost = 0
        total_fuel_quantity = 0
        # Assuming fuel data: (id, id_carburant, vehicule_id, chauffeur_id, date_plein, type_carburant, quantite, cout_total, lieu, kilometrage, type_paiement, num_facture, observations)
        for entry in filtered_fuel_entries:
            try:
                if len(entry) > 7 and entry[7] is not None: # cout_total is at index 7
                    total_fuel_cost += float(entry[7])
                if len(entry) > 6 and entry[6] is not None: # quantite is at index 6
                    total_fuel_quantity += float(entry[6])
            except (ValueError, TypeError):
                print(f"DEBUG: Skipping fuel cost/quantity calculation for entry due to non-numeric values: {entry}")
                pass

        self.statistics_text_output.insert(tk.END, "--- Consommation de Carburant ---\n")
        self.statistics_text_output.insert(tk.END, f"Coût total du carburant filtré : {total_fuel_cost:.2f} MGA\n")
        self.statistics_text_output.insert(tk.END, f"Quantité totale de carburant filtrée : {total_fuel_quantity:.2f} Litres\n")
        if total_mileage_from_fuel > 0 and total_fuel_quantity > 0:
            avg_consumption = (total_fuel_quantity / total_mileage_from_fuel) * 100 # Liters per 100 KM
            self.statistics_text_output.insert(tk.END, f"Consommation moyenne (L/100KM) : {avg_consumption:.2f} L/100KM\n")
        else:
            self.statistics_text_output.insert(tk.END, "Consommation moyenne : N/A (pas assez de données)\n")
        self.statistics_text_output.insert(tk.END, "\n")

        # --- Maintenance Statistics ---
        total_maintenance_cost = 0
        num_maintenances = len(filtered_maintenances)
        maintenance_by_type = {}
        # Assuming maintenance data: (id, id_maintenance, type_maintenance, date_maintenance, cout, description, statut, date_prochaine_maintenance, vehicule_id, personnel_id, fournisseur_id)
        for maint in filtered_maintenances:
            try:
                if len(maint) > 4 and maint[4] is not None: # cout is at index 4
                    total_maintenance_cost += float(maint[4])
                if len(maint) > 2: # type_maintenance is at index 2
                    maint_type = maint[2]
                    maintenance_by_type[maint_type] = maintenance_by_type.get(maint_type, 0) + 1
            except (ValueError, TypeError):
                print(f"DEBUG: Skipping maintenance cost/type calculation for entry due to invalid values: {maint}")
                pass

        self.statistics_text_output.insert(tk.END, "--- Maintenances ---\n")
        self.statistics_text_output.insert(tk.END, f"Coût total des maintenances filtrées : {total_maintenance_cost:.2f} MGA\n")
        self.statistics_text_output.insert(tk.END, f"Nombre de maintenances filtrées : {num_maintenances}\n")
        self.statistics_text_output.insert(tk.END, "Maintenances par type :\n")
        for m_type, count in maintenance_by_type.items():
            self.statistics_text_output.insert(tk.END, f"   - {m_type}: {count}\n")
        self.statistics_text_output.insert(tk.END, "\n")

        # --- Incident Statistics ---
        num_incidents = len(filtered_incident_reports)
        incidents_by_type = {}
        incidents_by_severity = {}
        # Assuming incident data: (id, id_incident, vehicule_id, date_incident, type_incident, description, gravite, cout_estime, statut, personnel_id, date_resolution)
        for inc in filtered_incident_reports:
            try:
                if len(inc) > 4: # type_incident is at index 4
                    inc_type = inc[4]
                    incidents_by_type[inc_type] = incidents_by_type.get(inc_type, 0) + 1
                if len(inc) > 6: # gravite is at index 6
                    inc_severity = inc[6]
                    incidents_by_severity[inc_severity] = incidents_by_severity.get(inc_severity, 0) + 1
            except IndexError:
                print(f"DEBUG: Skipping incident report entry due to missing type or severity: {inc}")
                pass

        self.statistics_text_output.insert(tk.END, "--- Incidents ---\n")
        self.statistics_text_output.insert(tk.END, f"Nombre total d'incidents filtrés : {num_incidents}\n")
        self.statistics_text_output.insert(tk.END, "Incidents par type :\n")
        for i_type, count in incidents_by_type.items():
            self.statistics_text_output.insert(tk.END, f"   - {i_type}: {count}\n")
        self.statistics_text_output.insert(tk.END, "Incidents par gravité :\n")
        for i_severity, count in incidents_by_severity.items():
            self.statistics_text_output.insert(tk.END, f"   - {i_severity}: {count}\n")
        self.statistics_text_output.insert(tk.END, "\n")


        # --- Génération des Graphiques ---
        # Nettoie tous les axes (subplots)
        for ax in self.axes.flatten():
            ax.clear()
            ax.set_facecolor(self.entry_bg) # Couleur de fond du plot
            ax.tick_params(axis='x', colors=self.fg_color_text)
            ax.tick_params(axis='y', colors=self.fg_color_text)
            ax.spines['left'].set_color(self.fg_color_text)
            ax.spines['bottom'].set_color(self.fg_color_text)
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)

        # Graphique 1 : Maintenances par type (Barres) - self.axes[0,0] (en haut à gauche)
        ax1 = self.axes[0,0]
        maint_types_labels = list(maintenance_by_type.keys())
        maint_counts_values = list(maintenance_by_type.values())

        if maint_types_labels:
            ax1.bar(maint_types_labels, maint_counts_values, color=self.highlight_color)
            ax1.set_title("Répartition des Maintenances", color=self.fg_color_text, fontsize=12)
            ax1.set_xlabel("Type", color=self.fg_color_text)
            ax1.set_ylabel("Nombre", color=self.fg_color_text)
            ax1.tick_params(axis='x', rotation=45)
        else:
            ax1.text(0.5, 0.5, "Aucune donnée de maintenance",
                             horizontalalignment='center', verticalalignment='center',
                             transform=ax1.transAxes, fontsize=10, color=self.fg_color_text)

        # Graphique 2 : Incidents par type (Circulaire) - self.axes[0,1] (en haut à droite)
        ax2 = self.axes[0,1]
        incident_types_labels = list(incidents_by_type.keys())
        incident_counts_values = list(incidents_by_type.values())

        if incident_types_labels:
            # Pour un pie chart, il est bon d'avoir des pourcentages
            total_incidents = sum(incident_counts_values)
            if total_incidents > 0:
                labels = [f'{l} ({int(c/total_incidents*100)}%)' for l, c in zip(incident_types_labels, incident_counts_values)]
                ax2.pie(incident_counts_values, labels=labels, autopct='', startangle=90,
                                colors=plt.cm.Paired.colors) # Utilisez une colormap pour des couleurs variées
                ax2.set_title("Répartition des Incidents par Type", color=self.fg_color_text, fontsize=12)
                ax2.axis('equal') # Assure que le cercle est rond
            else:
                ax2.text(0.5, 0.5, "Aucune donnée d'incident par type",
                                 horizontalalignment='center', verticalalignment='center',
                                 transform=ax2.transAxes, fontsize=10, color=self.fg_color_text)
        else:
            ax2.text(0.5, 0.5, "Aucune donnée d'incident",
                             horizontalalignment='center', verticalalignment='center',
                             transform=ax2.transAxes, fontsize=10, color=self.fg_color_text)


        # Graphique 3 : Coût du Carburant par Véhicule (Barres ou Courbe selon le détail) - self.axes[1,0] (en bas à gauche)
        # Pour ce graphique, nous allons calculer le coût total du carburant par véhicule
        fuel_cost_by_vehicle = {}
        for entry in filtered_fuel_entries:
            try:
                veh_id = int(entry[2]) # vehicule_id is at index 2
                cost = float(entry[7]) # cout_total is at index 7
                fuel_cost_by_vehicle[veh_id] = fuel_cost_by_vehicle.get(veh_id, 0.0) + cost
            except (ValueError, TypeError, IndexError):
                pass # Skip invalid entries

        ax3 = self.axes[1,0]
        vehicle_ids_for_fuel = list(fuel_cost_by_vehicle.keys())
        fuel_costs_values = list(fuel_cost_by_vehicle.values())

        if vehicle_ids_for_fuel:
            # Récupérer les plaques d'immatriculation pour les labels plus parlants
            vehicle_labels_map = {v[0]: v[1] for v in filtered_vehicles}
            labels_for_plot = [f"{veh_id} - {vehicle_labels_map.get(veh_id, 'Inconnu')}" for veh_id in vehicle_ids_for_fuel]

            ax3.bar(labels_for_plot, fuel_costs_values, color='lightcoral')
            ax3.set_title("Coût Carburant par Véhicule", color=self.fg_color_text, fontsize=12)
            ax3.set_xlabel("Véhicule", color=self.fg_color_text)
            ax3.set_ylabel("Coût (MGA)", color=self.fg_color_text)
            ax3.tick_params(axis='x', rotation=45) # Correction ici
        else:
            ax3.text(0.5, 0.5, "Aucune donnée de carburant par véhicule",
                             horizontalalignment='center', verticalalignment='center',
                             transform=ax3.transAxes, fontsize=10, color=self.fg_color_text)

        # Graphique 4 : Evolution du nombre d'attributions dans le temps (Courbe/Aires) - self.axes[1,1] (en bas à droite)
        ax4 = self.axes[1,1]
        attributions_by_date = {}
        for attr in filtered_attributions:
            try:
                attr_date = self._safe_parse_date(attr[3]) # date_attribution is at index 3
                if attr_date != date.min: # S'assurer que la date est valide
                    attributions_by_date[attr_date] = attributions_by_date.get(attr_date, 0) + 1
            except (ValueError, TypeError, IndexError):
                pass # Skip invalid entries

        if attributions_by_date:
            # Trier les dates pour un graphique temporel correct
            dates = sorted(attributions_by_date.keys())
            counts = [attributions_by_date[d] for d in dates]

            ax4.plot(dates, counts, marker='o', color='lightgreen', linestyle='-')
            ax4.fill_between(dates, counts, color='lightgreen', alpha=0.3) # Pour l'effet d'aire
            ax4.set_title("Nombre d'attributions par date", color=self.fg_color_text, fontsize=12)
            ax4.set_xlabel("Date", color=self.fg_color_text)
            ax4.set_ylabel("Nombre", color=self.fg_color_text)
            self.fig.autofmt_xdate(rotation=45, ha='right', ax=ax4) # Rotation des labels de l'axe X pour une meilleure lisibilité
        else:
            ax4.text(0.5, 0.5, "Aucune donnée d'attribution dans cette période",
                             horizontalalignment='center', verticalalignment='center',
                             transform=ax4.transAxes, fontsize=10, color=self.fg_color_text)


        # Ajustement final de la mise en page de la figure
        self.fig.tight_layout()
        self.canvas.draw() # Dessine tous les graphiques mis à jour

        self.statistics_text_output.config(state=tk.DISABLED)

    def clear_statistics_filters(self):
        self.stat_vehicle_var.set("Tous")
        self.stat_period_var.set("Personnalisé") # Réinitialise à Personnalisé
        self.stat_start_date_entry.set_date(None)
        self.stat_end_date_entry.set_date(None)
        self._on_period_selected() # Met à jour la visibilité des champs de date
        self.populate_statistics_dashboard()

    def export_statistics_to_pdf(self):
        """
        Exports the current statistics (text and graphs) to a PDF file.
        """
        # Obtenir le contenu de la sortie texte
        statistics_text = self.statistics_text_output.get("1.0", tk.END)

        # Demander à l'utilisateur où enregistrer le fichier
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialdir=self.pdf_export_dir,
            title="Exporter les statistiques au format PDF",
            filetypes=[("Fichiers PDF", "*.pdf")]
        )

        if not filename:
            return # L'utilisateur a annulé l'opération

        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Ajouter le logo (si le chemin est défini et le fichier existe)
        if hasattr(self, 'logo_path') and self.logo_path and os.path.exists(self.logo_path):
            try:
                # Ajuster la taille du logo pour le PDF
                img_logo = Image(self.logo_path, width=80, height=80)
                elements.append(img_logo)
                elements.append(Spacer(1, 0.2 * inch))
            except Exception as e:
                print(f"Erreur lors de l'ajout du logo au PDF: {e}")

        # Ajouter le titre
        elements.append(Paragraph("<b>Rapport de Statistiques des Véhicules</b>", styles['Title']))
        elements.append(Spacer(1, 0.2 * inch))

        # Ajouter la date de génération du rapport
        elements.append(Paragraph(f"<i>Généré le: {date.today().strftime('%Y-%m-%d')}</i>", styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))

        # Ajouter les filtres appliqués
        elements.append(Paragraph("<b>Filtres Appliqués :</b>", styles['h3']))
        elements.append(Paragraph(f"Véhicule : {self.stat_vehicle_var.get()}", styles['Normal']))
        elements.append(Paragraph(f"Chauffeur : {self.stat_driver_var.get()}", styles['Normal']))
        elements.append(Paragraph(f"Période : {self.stat_period_var.get()}", styles['Normal']))
        if self.stat_period_var.get() == "Personnalisé":
            start_date_str = self.stat_start_date_entry.get_date().strftime('%Y-%m-%d') if self.stat_start_date_entry.get_date() else "Non défini"
            end_date_str = self.stat_end_date_entry.get_date().strftime('%Y-%m-%d') if self.stat_end_date_entry.get_date() else "Non défini"
            elements.append(Paragraph(f"  Du : {start_date_str}", styles['Normal']))
            elements.append(Paragraph(f"  Au : {end_date_str}", styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))


        # Ajouter les statistiques textuelles
        elements.append(Paragraph("<b>Statistiques Récapitulatives :</b>", styles['h2']))
        # Split the text by lines and add as paragraphs, or a preformatted block
        for line in statistics_text.splitlines():
            elements.append(Paragraph(line, styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))


        # Ajouter les graphiques
        # Enregistrer la figure Matplotlib actuelle dans un fichier temporaire
        temp_img_path = os.path.join(tempfile.gettempdir(), "statistics_graphs.png")
        try:
            self.fig.savefig(temp_img_path, format='png', bbox_inches='tight', dpi=150) # DPI plus élevé pour meilleure qualité
        except Exception as e:
            messagebox.showerror("Erreur de sauvegarde d'image", f"Impossible de sauvegarder les graphiques pour le PDF : {e}")
            return # Ne continue pas si l'image ne peut pas être sauvegardée

        if os.path.exists(temp_img_path):
            try:
                # Calculer la taille de l'image pour qu'elle s'adapte à la largeur du PDF
                # A4 est d'environ 8.27 x 11.69 pouces.
                # La figure est de 10x8. Ajustons-la à une largeur de 7.5 pouces pour la marge.
                pdf_img_width = 7.5 * inch
                # Conserver le ratio d'aspect
                fig_width_inches, fig_height_inches = self.fig.get_size_inches()
                pdf_img_height = (pdf_img_width / fig_width_inches) * fig_height_inches

                img_graph = Image(temp_img_path, width=pdf_img_width, height=pdf_img_height)
                elements.append(Paragraph("<b>Visualisations Graphiques :</b>", styles['h2']))
                elements.append(Spacer(1, 0.1 * inch))
                elements.append(img_graph)
                elements.append(Spacer(1, 0.2 * inch))
            except Exception as e:
                print(f"Erreur lors de l'ajout des graphiques au PDF : {e}")
            finally:
                os.remove(temp_img_path) # Supprimer le fichier temporaire

        # Construire le PDF
        try:
            doc.build(elements)
            messagebox.showinfo("Exportation PDF", f"Le rapport PDF a été exporté avec succès vers :\n{filename}")
        except Exception as e:
            messagebox.showerror("Erreur d'Exportation PDF", f"Une erreur est survenue lors de la création du PDF : {e}")

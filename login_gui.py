import tkinter as tk
from tkinter import messagebox
import auth_manager
import tkinter.font as tkFont
from PIL import Image, ImageTk
import os

class LoginWindow(tk.Toplevel):
    def __init__(self, master, auth_manager_instance):
        super().__init__(master)
        self.master = master
        self.auth_manager = auth_manager_instance
        self.user_data = None

        # --- Base Configurations pour une fenêtre responsive ---
        self.title("GESTION LOGISTIQUE DE VEHICULE ")
        # NOUVEAU: Taille initiale de la fenêtre réajustée en hauteur
        self.geometry("450x650") # Augmenté de 650 à 700
        self.min_width = 400
        # NOUVEAU: Hauteur minimale de la fenêtre augmentée
        self.min_height = 600 # Augmenté de 550 à 600
        self.minsize(self.min_width, self.min_height)
        self.resizable(True, True)

        self.center_window() # Centre la fenêtre lors de son ouverture initiale

        self.transient(master)
        self.grab_set()
        self.master.withdraw()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # 2. Définition des couleurs de l'interface (Blanc et palette bleue)
        self.bg_color = "#FFFFFF"
        self.fg_color = "#333333"
        self.entry_bg = "#FFFFFF"
        self.button_bg = "#569FD3"
        self.button_fg = "#FFFFFF"
        self.title_color = "#407BBF"

        self.configure(bg=self.bg_color)

        # --- Gestion du Logo pour le redimensionnement dynamique ---
        script_dir = os.path.dirname(__file__)
        self.logo_path = os.path.join(script_dir, "Toutadom.png")

        self.original_logo_image = None
        try:
            self.original_logo_image = Image.open(self.logo_path)
            self.logo_aspect_ratio = self.original_logo_image.width / self.original_logo_image.height
        except FileNotFoundError:
            messagebox.showerror("Erreur de Fichier", f"Le fichier logo est introuvable : {self.logo_path}", parent=self)
            self.original_logo_image = Image.new('RGB', (200, 100), color='grey')
            self.logo_aspect_ratio = 200 / 100
        except Exception as e:
            messagebox.showerror("Erreur d'Image", f"Impossible de charger le logo : {e}", parent=self)
            self.original_logo_image = Image.new('RGB', (200, 100), color='grey')

        initial_logo_width = 200
        initial_logo_height = int(initial_logo_width / self.logo_aspect_ratio)
        resized_logo_image = self.original_logo_image.resize((initial_logo_width, initial_logo_height), Image.Resampling.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(resized_logo_image)

        # --- Layout avec Grid pour la réactivité ---
        # padx/pady réduits, mais adaptés pour la nouvelle taille
        main_frame = tk.Frame(self, bg=self.bg_color, padx=40, pady=20)
        main_frame.pack(fill="both", expand=True)

        main_frame.grid_columnconfigure(0, weight=1)

        # NOUVEAU: Réajustement des poids des lignes pour assurer la visibilité du bouton
        # Laissez les éléments importants (labels, entries, checkbutton) avec weight=0
        # Donnez des poids aux lignes "spacer" pour qu'elles absorbent l'espace supplémentaire.
        # Si le bouton est toujours caché, on peut donner un weight plus grand au spacer *avant* le bouton
        # ou réduire les paddings des éléments au-dessus.
        main_frame.grid_rowconfigure(0, weight=0) # Logo
        main_frame.grid_rowconfigure(1, weight=0) # Titre
        main_frame.grid_rowconfigure(2, weight=0) # Label nom d'utilisateur
        main_frame.grid_rowconfigure(3, weight=0) # Entrée nom d'utilisateur
        main_frame.grid_rowconfigure(4, weight=0) # Label mot de passe
        main_frame.grid_rowconfigure(5, weight=0) # Entrée mot de passe
        main_frame.grid_rowconfigure(6, weight=0) # Checkbutton
        main_frame.grid_rowconfigure(7, weight=1) # Espace flexible au-dessus du bouton (donne de l'air)
        main_frame.grid_rowconfigure(8, weight=0) # Bouton (ne s'étire pas verticalement lui-même)
        main_frame.grid_rowconfigure(9, weight=1) # Espace flexible sous le bouton

        # Styles des polices (maintenus)
        self.font_label = tkFont.Font(family="Helvetica", size=11, weight="bold")
        self.font_button_text = tkFont.Font(family="Helvetica", size=13, weight="bold")
        self.title_font = tkFont.Font(family="Helvetica", size=22, weight="bold")


        # --- Placement des Widgets en utilisant Grid ---
        row_idx = 0

        self.logo_label = tk.Label(main_frame, image=self.logo_photo, bg=self.bg_color, relief="flat", bd=0)
        self.logo_label.image = self.logo_photo
        # NOUVEAU: pady ajusté pour le logo pour économiser un peu de place
        self.logo_label.grid(row=row_idx, column=0, pady=(15, 15), sticky="n")
        row_idx += 1

        auth_message_label = tk.Label(main_frame, text="Veuillez vous authentifier :", font=self.title_font,
                                       bg=self.bg_color, fg=self.title_color)
        # NOUVEAU: pady ajusté pour le titre
        auth_message_label.grid(row=row_idx, column=0, pady=(10, 25), sticky="n")
        row_idx += 1

        tk.Label(main_frame, text="Nom d'utilisateur:", font=self.font_label,
                 bg=self.bg_color, fg=self.fg_color).grid(row=row_idx, column=0, pady=(2,1), sticky="w") # pady réduit
        row_idx += 1
        self.username_entry = tk.Entry(main_frame, font=self.font_label,
                                       bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color,
                                       relief="solid", bd=1)
        self.username_entry.grid(row=row_idx, column=0, pady=(1, 10), sticky="ew") # pady réduit
        self.username_entry.focus_set()
        row_idx += 1

        tk.Label(main_frame, text="Mot de passe:", font=self.font_label,
                 bg=self.bg_color, fg=self.fg_color).grid(row=row_idx, column=0, pady=(2,1), sticky="w") # pady réduit
        row_idx += 1
        self.password_entry = tk.Entry(main_frame, show="*", font=self.font_label,
                                       bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color,
                                       relief="solid", bd=1)
        self.password_entry.grid(row=row_idx, column=0, pady=(1, 10), sticky="ew") # pady réduit
        self.password_entry.bind("<Return>", lambda event: self.login())
        row_idx += 1

        self.show_password_var = tk.IntVar()
        tk.Checkbutton(
            main_frame,
            text="Afficher le mot de passe",
            variable=self.show_password_var,
            command=self.toggle_password_visibility,
            bg=self.bg_color,
            fg=self.fg_color,
            font=self.font_label,
            selectcolor=self.bg_color,
            activebackground=self.bg_color,
            activeforeground=self.fg_color,
            highlightbackground=self.bg_color,
            relief="flat",
            justify=tk.LEFT
        ).grid(row=row_idx, column=0, pady=(5, 20), sticky="w") # NOUVEAU: pady ajusté
        row_idx += 1

        # Spacer row before button to push it towards center/bottom
        # Le poids de cette ligne est important pour la distribution de l'espace
        tk.Frame(main_frame, bg=self.bg_color).grid(row=row_idx, column=0, sticky="nsew") # weight=1 défini ci-dessus
        row_idx += 1

        tk.Button(main_frame, text="Se Connecter", font=self.font_button_text,
                  bg=self.button_bg, fg=self.button_fg,
                  activebackground=self.title_color,
                  activeforeground=self.button_fg,
                  relief="flat", bd=0,
                  command=self.login).grid(row=row_idx, column=0, pady=30, sticky="ew", ipady=12) # NOUVEAU: pady ajusté
        row_idx += 1

        # Spacer row after button for final padding/expansion
        tk.Frame(main_frame, bg=self.bg_color).grid(row=row_idx, column=0, sticky="nsew") # weight=1 défini ci-dessus

        self.bind("<Configure>", self._on_window_resize)
        self._last_width = self.winfo_width()
        self._last_height = self.winfo_height()


    def _on_window_resize(self, event):
        if event.widget == self and (event.width != self._last_width or event.height != self._last_height):
            self._last_width = event.width
            self._last_height = event.height

            self.update_idletasks()
            usable_width = self.winfo_width() - (self.cget('padx') * 2)

            target_logo_width = int(usable_width * 0.70)
            if target_logo_width > 200:
                target_logo_width = 200
            elif target_logo_width < 80:
                target_logo_width = 80

            new_logo_height = int(target_logo_width / self.logo_aspect_ratio)

            try:
                resized_logo_image = self.original_logo_image.resize((target_logo_width, new_logo_height), Image.Resampling.LANCZOS)
                new_logo_photo = ImageTk.PhotoImage(resized_logo_image)

                self.logo_label.config(image=new_logo_photo)
                self.logo_label.image = new_logo_photo
            except Exception as e:
                pass

    def center_window(self):
        self.update_idletasks()
        # NOUVEAU: Utilise la nouvelle taille initiale pour le centrage
        w, h = 450, 650 # Match la géométrie initiale
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self._last_width = w
        self._last_height = h

    def toggle_password_visibility(self):
        self.password_entry.config(show="" if self.show_password_var.get() else "*")

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Champs requis", "Veuillez remplir tous les champs.", parent=self)
            return

        user_id, role, nom, prenom, username_retour = self.auth_manager.authenticate_user(username, password)
        if user_id:
            messagebox.showinfo("Connexion Réussie", f"Bienvenue, {prenom} {nom} ({role})!", parent=self)
            self.user_data = (user_id, role, nom, prenom, username_retour)
            self.grab_release(); self.master.deiconify(); self.destroy()
        else:
            messagebox.showerror("Échec de connexion", "Nom d'utilisateur ou mot de passe incorrect.", parent=self)
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.username_entry.focus_set()

    def _on_closing(self):
        if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter l'application ?"):
            self.user_data = (None, None, None, None, None)
            self.grab_release(); self.master.deiconify(); self.destroy()
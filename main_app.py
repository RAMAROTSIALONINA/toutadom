# main_app.py
import sys
import os
import tkinter as tk # Importe tkinter pour la fenêtre principale
from tkinter import messagebox # Pour les messages d'information/erreur
import db_manager
import auth_manager
# Importe la nouvelle fenêtre de connexion GUI
from login_gui import LoginWindow # Assurez-vous que login_gui.py est dans le même dossier

# Importe les classes de tableau de bord spécifiques
from admin_dashboard import AdminDashboard
from responsable_dashboard import ResponsableDashboard
from chauffeur_dashboard import ChauffeurDashboard

# Ensure the parent directory is in the path to be able to import modules
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

class AppManager:
    """
    Main class for the vehicle management application.
    Manages initialization and orchestration of various functionalities.
    """
    def __init__(self, app_root, ):
        self.app_root = app_root
        
        # Initialiser la fenêtre racine Tkinter
        self.root = tk.Tk()
        self.root.title("Système de Gestion de Flotte de Véhicules")
        self.root.geometry("1024x768") # Taille par défaut pour le tableau de bord
        # Nous ne cachons plus la fenêtre principale ici, login_gui.py le fera.
        # self.root.withdraw() 

        self.logged_in_user_id = None
        self.logged_in_username = None 
        self.logged_in_user_role = None 
        self.logged_in_user_fullname = None 
        self.auth_manager = auth_manager.AuthManager() # Initialise AuthManager

        self.current_dashboard = None # Pour stocker l'instance du tableau de bord actif
        self.app_root_dir = app_root_dir

        # Initialisation de la base de données
        db_init_success, db_init_message = db_manager.initialize_database()
        if not db_init_success:
            messagebox.showerror("Erreur de Base de Données", f"Impossible d'initialiser la base de données: {db_init_message}")
            sys.exit(1) # Quitte l'application si la DB ne peut pas être initialisée
        else:
            print(db_init_message) # Message de succès dans la console

        # Lancer le flux de connexion graphique au démarrage
        self.run_login_flow_gui()
        
        # Gérer la fermeture de la fenêtre principale
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def run_login_flow_gui(self):
        """
        Lance la fenêtre de connexion GUI et attend que l'utilisateur se connecte.
        Reste dans une boucle tant que l'authentification n'est pas réussie ou que l'application n'est pas explicitement quittée.
        """
        while True:
            # La fenêtre principale est masquée par LoginWindow.__init__
            login_window = LoginWindow(self.root, self.auth_manager)
            self.root.wait_window(login_window) # Attend que la fenêtre de login soit fermée

            # Récupère les données de l'utilisateur après la fermeture de la fenêtre de login
            # login_gui.py retourne (user_id, role, nom, prenom, username)
            user_id, role, nom, prenom, username_from_login = login_window.user_data
            
            if user_id is not None: # Vérifie si user_id n'est pas None (connexion réussie)
                self.logged_in_user_id = user_id
                self.logged_in_user_role = role
                self.logged_in_username = username_from_login
                self.logged_in_user_fullname = f"{prenom} {nom}" if nom and prenom else "Utilisateur Inconnu"

                # Si la connexion est réussie, affiche la fenêtre principale et le tableau de bord approprié
                self.start_application_menu()
                return # Sortir de la boucle de connexion car l'utilisateur est connecté
            else:
                # Si la connexion échoue ou est annulée, demande si l'utilisateur veut quitter
                # Si l'utilisateur clique sur 'Non' dans la messagebox, la boucle continue et la fenêtre de login réapparaît
                # Si l'utilisateur clique sur 'Oui', l'application se ferme
                if not messagebox.askyesno("Quitter l'application", "La connexion a échoué ou a été annulée. Voulez-vous quitter l'application ?"):
                    continue
                else:
                    # L'utilisateur a choisi de quitter
                    self.root.destroy()
                    sys.exit(0)

    def start_application_menu(self):
        """
        Affiche le tableau de bord approprié en fonction du rôle de l'utilisateur connecté.
        """
        # Efface tout contenu précédent dans la fenêtre principale
        for widget in self.root.winfo_children():
            widget.destroy()
         #Créer un cadre pour le tableau de bord principal
        self.dashboard_frame = tk.Frame(self.root, bg="#34495E") # Ou la couleur de fond de votre choix
        self.dashboard_frame.pack(fill="both", expand=True)

        if self.logged_in_user_role == "admin":
            self.current_dashboard = AdminDashboard(
                self.root, 
                self,
                
            )
        elif self.logged_in_user_role == "responsable":
            # Passer les informations de l'utilisateur au ResponsableDashboard
            self.current_dashboard = ResponsableDashboard(
                self.root, 
                self.dashboard_frame,
                self, 
                self.logged_in_user_id, 
                self.logged_in_username, 
                self.logged_in_user_role, 
                self.logged_in_user_fullname
            )
        elif self.logged_in_user_role == "chauffeur":
            # Passer toutes les informations de l'utilisateur au ChauffeurDashboard
            self.current_dashboard = ChauffeurDashboard(
                self.root, 
                self, 
                self.logged_in_user_id,
                self.logged_in_username,
                self.logged_in_user_role,
                self.logged_in_user_fullname
            )
        else:
            messagebox.showerror("Erreur de Rôle", "Rôle utilisateur non reconnu. Déconnexion.")
            self.logout()

    def logout(self):
        """
        Gère la déconnexion de l'utilisateur.
        """
        if messagebox.askyesno("Déconnexion", "Êtes-vous sûr de vouloir vous déconnecter ?"):
            self.logged_in_user_id = None
            self.logged_in_username = None
            self.logged_in_user_role = None
            self.logged_in_user_fullname = None
            if self.current_dashboard:
                # Détruire le tableau de bord actuel si nécessaire (peut varier selon l'implémentation)
                for widget in self.root.winfo_children():
                    widget.destroy()
                self.current_dashboard = None
            self.run_login_flow_gui() # Relance le flux de connexion graphique

    def _on_closing(self):
        """
        Gère l'événement de fermeture de la fenêtre principale.
        """
        if messagebox.askokcancel("Quitter l'application", "Voulez-vous vraiment quitter l'application ?"):
            self.root.destroy()

# Application entry point
if __name__ == '__main__':
    app_root_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        app = AppManager(app_root_dir)
        # La boucle principale Tkinter doit être lancée une seule fois et en dernier.
        # Si AppManager crée tk.Tk() comme self.root, c'est cette instance qui doit appeler mainloop().
        app.root.mainloop() # Lance la boucle d'événements Tkinter une fois que tout est initialisé
    except Exception as e:
        print(f"Une erreur inattendue s'est produite : {e}")
        import traceback
        traceback.print_exc()
        # Affiche un message d'erreur dans une boîte de dialogue pour l'utilisateur
        # et dans la console pour le débogage.
        try:
            # Tente d'afficher une messagebox si Tkinter est déjà initialisé
            tk.Tk().withdraw() # Crée une instance Tk temporaire et la cache si root n'existe pas encore
            messagebox.showerror("Erreur de l'Application", f"Une erreur critique est survenue : {e}\nL'application va se fermer.")
        except:
            # Si Tkinter n'est pas initialisé du tout, juste print
            pass
        input("Appuyez sur Entrée pour quitter...") # Maintient la fenêtre

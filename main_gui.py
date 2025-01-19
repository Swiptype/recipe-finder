import os
import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog, Toplevel, Text, ttk
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

DB_PATH = "recettes.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recettes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            instructions TEXT NOT NULL,
            nb_personnes INTEGER NOT NULL DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

class RecetteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestionnaire de Recettes")

        # Création des widgets de l'interface utilisateur
        self.frame = ttk.Frame(root, padding=10)
        self.frame.pack()

        # Zone de recherche
        ttk.Label(self.frame, text="Rechercher par ingrédients :").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_recherche = ttk.Entry(self.frame, width=40)
        self.entry_recherche.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.frame, text="Chercher", command=self.rechercher_par_ingredients).grid(row=0, column=2, padx=5, pady=5)

        # Champ de recherche pour le nom de la recette
        ttk.Label(self.frame, text="Rechercher par nom de recette :").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_recherche_nom = ttk.Entry(self.frame, width=40)
        self.entry_recherche_nom.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(self.frame, text="Chercher par nom", command=self.rechercher_par_nom).grid(row=1, column=2, padx=5, pady=5)

        # Sélecteur de recettes
        ttk.Label(self.frame, text="Recettes disponibles :").grid(row=2, column=0, padx=5, pady=5)
        self.combo_recettes = ttk.Combobox(self.frame, width=40, state="readonly")
        self.combo_recettes.grid(row=2, column=1, padx=5, pady=5)
        self.combo_recettes.bind("<<ComboboxSelected>>", self.afficher_recette)

        # Boutons d'action
        ttk.Button(self.frame, text="Ajouter une recette", command=self.ajouter_recette).grid(row=3, column=0, padx=5, pady=5)
        ttk.Button(self.frame, text="Modifier une recette", command=self.modifier_recette).grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(self.frame, text="Exporter en PDF", command=self.exporter_pdf).grid(row=4, column=0, padx=5, pady=5)
        ttk.Button(self.frame, text="Quitter", command=root.quit).grid(row=4, column=1, padx=5, pady=5)

        # Reinitialiser la comboBox des recettes
        ttk.Button(self.frame, text="Réinitialiser la recherche", command=self.reinitialiser_recherche).grid(row=3, column=2, padx=5, pady=5)

        # Affichage de la recette
        ttk.Label(self.frame, text="Détails de la recette :").grid(row=6, column=0, columnspan=3, pady=(10, 5))
        self.text_recette = Text(self.frame, width=80, height=15, wrap="word")
        self.text_recette.grid(row=7, column=0, columnspan=3, padx=5, pady=5)

        # Charger les recettes après la création des widgets
        self.charger_recettes()

    def rechercher_par_nom(self):
        # Récupérer le nom de la recette
        nom_recherche = self.entry_recherche_nom.get().strip()

        if not nom_recherche:
            messagebox.showwarning("Attention", "Veuillez saisir un nom de recette.")
            return

        # Connexion à la base de données et recherche
        conn = sqlite3.connect("recettes.db")
        cursor = conn.cursor()

        try:
            # Rechercher la recette par son nom (sensibilité à la casse ignorée)
            cursor.execute("SELECT nom FROM recettes WHERE nom LIKE ?", ('%' + nom_recherche + '%',))
            resultats = cursor.fetchall()

            if resultats:
                # Met à jour la combobox avec les recettes trouvées
                noms_recettes = [row[0] for row in resultats]
                self.combo_recettes['values'] = noms_recettes
                self.combo_recettes.set("")  # Effacer la sélection actuelle
                messagebox.showinfo("Succès", f"{len(noms_recettes)} recette(s) trouvée(s) avec ce nom.")
            else:
                messagebox.showinfo("Aucune recette", "Aucune recette trouvée avec ce nom.")

        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur s'est produite : {str(e)}")

        finally:
            conn.close()

    def reinitialiser_recherche(self):
        # Connexion à la base de données et récupération de toutes les recettes
        conn = sqlite3.connect("recettes.db")
        cursor = conn.cursor()

        try:
            # Récupérer toutes les recettes
            cursor.execute("SELECT nom FROM recettes")
            resultats = cursor.fetchall()

            # Met à jour la combobox avec toutes les recettes
            noms_recettes = [row[0] for row in resultats]
            self.combo_recettes['values'] = noms_recettes
            self.combo_recettes.set("")  # Effacer la sélection actuelle

            messagebox.showinfo("Réinitialisation", "La recherche a été réinitialisée.")

        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur s'est produite : {str(e)}")

        finally:
            conn.close()

    def charger_recettes(self, filtre=None):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if filtre:
            cursor.execute("SELECT nom FROM recettes WHERE ingredients LIKE ?", (f"%{filtre}%",))
        else:
            cursor.execute("SELECT nom FROM recettes")
        noms = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.combo_recettes['values'] = noms
        self.combo_recettes.set("")  # Réinitialise la sélection
        self.text_recette.delete("1.0", "end")  # Vide la zone d'affichage des détails

    def rechercher_par_ingredients(self):
        # Récupérer les ingrédients de la recherche, séparés par des virgules
        ingredients_recherche = self.entry_recherche.get().strip()

        if not ingredients_recherche:
            messagebox.showwarning("Attention", "Veuillez saisir un ou plusieurs ingrédients pour la recherche.")
            return

        # Séparer les ingrédients par des virgules et enlever les espaces
        ingredients_list = [ingredient.strip() for ingredient in ingredients_recherche.split(",")]

        # Connexion à la base de données et recherche
        conn = sqlite3.connect("recettes.db")
        cursor = conn.cursor()

        try:
            # Construire une requête SQL avec LIKE pour chaque ingrédient
            query = "SELECT nom FROM recettes WHERE "
            conditions = []
            for ingredient in ingredients_list:
                conditions.append(f"ingredients LIKE ?")
            
            # Joindre les conditions avec "AND" pour rechercher des recettes contenant tous les ingrédients
            query += " AND ".join(conditions)
            
            # Préparer les paramètres de la requête (en utilisant % pour la recherche partielle)
            params = [f"%{ingredient}%" for ingredient in ingredients_list]
            
            cursor.execute(query, tuple(params))
            resultats = cursor.fetchall()

            if resultats:
                # Met à jour la combobox avec les recettes trouvées
                noms_recettes = [row[0] for row in resultats]
                self.combo_recettes['values'] = noms_recettes
                self.combo_recettes.set("")  # Efface la sélection actuelle
                messagebox.showinfo("Succès", f"{len(noms_recettes)} recette(s) trouvée(s) contenant les ingrédients.")
            else:
                messagebox.showinfo("Aucune recette", "Aucune recette trouvée avec ces ingrédients.")

        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur s'est produite : {str(e)}")

        finally:
            conn.close()

    def afficher_recette(self, event=None):
        recette_selectionnee = self.combo_recettes.get()
        if not recette_selectionnee:
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT ingredients, instructions, nb_personnes FROM recettes WHERE nom = ?", (recette_selectionnee,))
        recette = cursor.fetchone()
        conn.close()

        if recette:
            ingredients, instructions, nb_personnes = recette
            self.spin_personnes.delete(0, "end")
            self.spin_personnes.insert(0, nb_personnes)
            texte = f"**Ingrédients :**\n{nb_personnes}\n\n**Instructions :**\n{instructions}"
            self.text_recette.delete("1.0", "end")
            self.text_recette.insert("1.0", texte)

    def ajouter_recette(self):
        self._fenetre_saisie(mode="ajouter")

    def modifier_recette(self):
        recette_selectionnee = self.combo_recettes.get()
        if not recette_selectionnee:
            messagebox.showwarning("Avertissement", "Sélectionnez une recette à modifier.")
            return
        self._fenetre_saisie(mode="modifier", nom_initial=recette_selectionnee)

    def _fenetre_saisie(self, mode="ajouter", nom_initial=None):
        window = Toplevel(self.root)
        window.title("Ajouter/Modifier une Recette")

        # Champs de saisie
        ttk.Label(window, text="Nom de la recette :").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        entry_nom = ttk.Entry(window, width=50)
        entry_nom.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(window, text="Ingrédients (format : ingrédient : poids, un par ligne) :").grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        text_ingredients = Text(window, width=50, height=10)
        text_ingredients.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(window, text="Instructions :").grid(row=2, column=0, padx=5, pady=5, sticky="nw")
        text_instructions = Text(window, width=50, height=10)
        text_instructions.grid(row=2, column=1, padx=5, pady=5)

        if mode == "modifier":
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT ingredients, instructions FROM recettes WHERE nom = ?", (nom_initial,))
            recette = cursor.fetchone()
            conn.close()

            if recette:
                ingredients, instructions = recette
                entry_nom.insert(0, nom_initial)
                text_ingredients.insert("1.0", ingredients)
                text_instructions.insert("1.0", instructions)

        def sauvegarder():
            nom = entry_nom.get().strip()
            ingredients = text_ingredients.get("1.0", "end-1c").strip()
            instructions = text_instructions.get("1.0", "end-1c").strip()

            if not nom or not ingredients or not instructions:
                messagebox.showwarning("Avertissement", "Tous les champs doivent être remplis.")
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            if mode == "modifier":
                cursor.execute("UPDATE recettes SET nom = ?, ingredients = ?, instructions = ? WHERE nom = ?",
                               (nom, ingredients, instructions, nom_initial))
            else:
                cursor.execute("INSERT INTO recettes (nom, ingredients, instructions) VALUES (?, ?, ?)",
                               (nom, ingredients, instructions))
            conn.commit()
            conn.close()

            messagebox.showinfo("Succès", f"Recette '{nom}' sauvegardée.")
            self.charger_recettes()
            window.destroy()

        ttk.Button(window, text="Sauvegarder", command=sauvegarder).grid(row=3, column=0, columnspan=2, pady=10)

    def afficher_recette(self, event=None):
        recette_selectionnee = self.combo_recettes.get()
        if not recette_selectionnee:
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT ingredients, instructions FROM recettes WHERE nom = ?", (recette_selectionnee,))
        recette = cursor.fetchone()
        conn.close()

        if recette:
            ingredients, instructions = recette
            texte = f"**Ingrédients (avec poids) :**\n{ingredients}\n\n**Instructions :**\n{instructions}"
            self.text_recette.delete("1.0", "end")
            self.text_recette.insert("1.0", texte)

    def exporter_pdf(self):
        recette_selectionnee = self.combo_recettes.get()
        if not recette_selectionnee:
            messagebox.showwarning("Avertissement", "Sélectionnez une recette à exporter.")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT ingredients, instructions FROM recettes WHERE nom = ?", (recette_selectionnee,))
        recette = cursor.fetchone()
        conn.close()

        if not recette:
            messagebox.showerror("Erreur", "Les détails de la recette n'ont pas pu être trouvés.")
            return

        ingredients, instructions = recette

        # Demander le chemin de sauvegarde pour le fichier PDF
        fichier_pdf = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not fichier_pdf:
            return

        # Générer le contenu PDF
        try:
            c = canvas.Canvas(fichier_pdf, pagesize=A4)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, 800, f"Recette : {recette_selectionnee}")

            c.setFont("Helvetica", 12)
            c.drawString(100, 770, "Ingrédients :")
            y = 750
            for ligne in ingredients.split("\n"):
                c.drawString(120, y, f"- {ligne}")
                y -= 20
                if y < 50:  # Gérer les sauts de page si nécessaire
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = 800

            c.drawString(100, y - 20, "Instructions :")
            y -= 40
            for ligne in instructions.split("\n"):
                c.drawString(120, y, ligne)
                y -= 20
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = 800

            c.save()
            messagebox.showinfo("Succès", f"Recette exportée en PDF sous '{fichier_pdf}'.")

        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur s'est produite lors de l'exportation en PDF : {str(e)}")

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = RecetteApp(root)
    root.mainloop()

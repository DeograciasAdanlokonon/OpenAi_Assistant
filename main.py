import sys
import openai
import sqlite3
import customtkinter as ctk
from tkinter import messagebox, simpledialog
import pyttsx3
import speech_recognition as sr
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from pyvirtualdisplay import Display

sys.path.append('/home/Casius/myenv/lib/python3.9/site-packages')


print("Début du script")  # Instruction de débogage

# Configurez votre clé API OpenAI
openai.api_key = 'API_KEY'

# Configuration de la journalisation
logging.basicConfig(filename='assistant.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# Connexion à la base de données SQLite
conn = sqlite3.connect('competences.db')
c = conn.cursor()

# Création de la table des compétences si elle n'existe pas
c.execute('''CREATE TABLE IF NOT EXISTS competences (prompt TEXT, reponse TEXT)''')
conn.commit()


def obtenir_reponse(prompt):
    try:
        # Vérifiez si la compétence existe déjà dans la base de données
        c.execute("SELECT reponse FROM competences WHERE prompt=?", (prompt,))
        result = c.fetchone()
        if result:
            return result[0]

        # Si la compétence n'existe pas, utilisez l'API OpenAI
        response = openai.Completion.create(
            engine="text-davinci-004",
            prompt=prompt,
            max_tokens=150
        )
        return response.choices[0].text.strip()
    except sqlite3.Error as e:
        logging.error(f"Erreur SQLite : {e}")
        return f"Erreur de base de données : {str(e)}"
    except openai.OpenAIError as e:
        logging.error(f"Erreur OpenAI : {e}")
        return f"Erreur de l'API OpenAI : {str(e)}"
    except Exception as e:
        logging.error(f"Erreur inconnue : {e}")
        return f"Erreur : {str(e)}"


def deployer_instance():
    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(tache_lourde, i) for i in range(4)]
            for future in futures:
                result = future.result()
                logging.info(f"Résultat de la tâche {result}")
        logging.info("Instances de calcul déployées avec succès.")
    except Exception as e:
        logging.error(f"Erreur lors du déploiement de l'instance : {e}")


def tache_lourde(instance_id):
    # Simuler une tâche lourde
    time.sleep(5)
    return f"Tâche {instance_id} terminée"


def augmenter_ressources():
    while True:
        deployer_instance()
        time.sleep(10)  # Intervalle entre chaque augmentation de ressources


class AssistantIA:
    def __init__(self, root):
        self.root = root
        self.root.title("Assistant IA")
        self.root.geometry("600x400")

        self.chat_area = ctk.CTkTextbox(root, wrap="word", width=580, height=300)
        self.chat_area.pack(padx=10, pady=10)

        self.entry = ctk.CTkEntry(root, width=400)
        self.entry.pack(padx=10, pady=10, side="left")
        self.entry.bind("<Return>", self.envoyer_message)

        self.bouton_envoyer = ctk.CTkButton(root, text="Envoyer", command=self.envoyer_message)
        self.bouton_envoyer.pack(padx=10, pady=10, side="left")

        self.bouton_apprendre = ctk.CTkButton(root, text="Apprendre", command=self.apprendre_competence)
        self.bouton_apprendre.pack(padx=10, pady=10, side="left")

        self.bouton_parler = ctk.CTkButton(root, text="Parler", command=self.reconnaissance_vocale)
        self.bouton_parler.pack(padx=10, pady=10, side="left")

        self.bouton_deployer = ctk.CTkButton(root, text="Déployer Instance", command=deployer_instance)
        self.bouton_deployer.pack(padx=10, pady=10, side="left")

        self.engine = pyttsx3.init()

    def envoyer_message(self, event=None):
        message = self.entry.get()
        self.chat_area.insert("end", "Vous: " + message + "\n")
        self.entry.delete(0, "end")

        reponse = obtenir_reponse(message)
        self.chat_area.insert("end", "Assistant: " + reponse + "\n")
        self.synthese_vocale(reponse)

    def apprendre_competence(self):
        prompt = self.entry.get()
        reponse_attendue = simpledialog.askstring("Apprendre", "Quelle est la réponse attendue ?")
        if prompt and reponse_attendue:
            try:
                c.execute("INSERT INTO competences (prompt, reponse) VALUES (?, ?)", (prompt, reponse_attendue))
                conn.commit()
                messagebox.showinfo("Apprentissage", "Nouvelle compétence ajoutée avec succès !")
                logging.info(f"Nouvelle compétence ajoutée : {prompt} -> {reponse_attendue}")
            except sqlite3.Error as e:
                logging.error(f"Erreur SQLite lors de l'ajout de compétence : {e}")
                messagebox.showerror("Erreur", f"Erreur de base de données : {str(e)}")
        else:
            messagebox.showwarning("Erreur", "Veuillez entrer un prompt et une réponse attendue.")

    def synthese_vocale(self, texte):
        self.engine.say(texte)
        self.engine.runAndWait()

    def reconnaissance_vocale(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Parlez maintenant...")
            audio = recognizer.listen(source)
            try:
                texte = recognizer.recognize_google(audio, language="fr-FR")
                self.entry.insert(0, texte)
                self.envoyer_message()
            except sr.UnknownValueError:
                messagebox.showwarning("Erreur", "Je n'ai pas compris ce que vous avez dit.")
            except sr.RequestError as e:
                messagebox.showwarning("Erreur", f"Erreur de service de reconnaissance vocale; {e}")
                logging.error(f"Erreur de service de reconnaissance vocale : {e}")


class Application:
    def __init__(self):
        self.root = ctk.CTk()
        self.assistant = AssistantIA(self.root)

    def run(self):
        self.root.mainloop()


def redemarrer_script():
    """Redémarre le script en cas de crash."""
    python = sys.executable
    os.execl(python, python, *sys.argv)


def deployer_et_tester():
    """Déploie et teste le script automatiquement."""
    print("Début de deployer_et_tester")  # Instruction de débogage
    try:
        app = Application()
        app.run()
    except Exception as e:
        logging.error(f"Erreur : {e}")
        time.sleep(5)
        redemarrer_script()


def start_tkinter_interface():
    # Démarrer le serveur X virtuel
    display = Display(visible=False, size=(1024, 768))
    display.start()

    try:
        print("Démarrage de l'application Tkinter")  # Instruction de débogage
        app = Application()
        app.run()
    except Exception as e:
        logging.error(f"Erreur lors du démarrage de l'interface Tkinter : {e}")

    # Arrêter le serveur X virtuel
    display.stop()


if __name__ == "__main__":
    start_tkinter_interface()

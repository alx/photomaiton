from flask import Flask, render_template
import platform
import sys
sys.path.append("..")
import db

app = Flask(__name__)

@app.route("/infos")
def hello():
    uname = platform.uname()

    # TODO : Récup depuis config
    id_booth = 3

    # Connexion à la base de données
    conn = db.connect_database()
    cursor = conn.cursor()

    # Exécuter une requête SQL pour sélectionner la ligne avec idBooth spécifique
    cursor.execute("SELECT * FROM BOOTH WHERE idBooth = ?;", (id_booth,))
    
    # Récupérer la ligne correspondante
    booth_data = cursor.fetchone()

    # Fermeture du curseur et de la connexion à la base de données
    cursor.close()
    conn.close()

    thisdict = {
        "id": booth_data[0],
        "name": booth_data[1],
        "tarif": booth_data[2]
    }
    return render_template('infos.html', **thisdict)
    
if __name__ == "__main__":
  app.run(host='0.0.0.0', port=5001, debug=True)
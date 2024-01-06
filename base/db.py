import sqlite3
import os
from pathlib import Path

def create_tables(conn):
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='version';")
    table_exists = cursor.fetchone()

    if table_exists:
        cursor.execute("SELECT version FROM version;")
        db_version = cursor.fetchone()[0]
        if db_version == 1:
            return
        elif db_version < 1:
            pass
    else:
        cursor.execute("CREATE TABLE version (version INTEGER);")
        cursor.execute("INSERT INTO version VALUES (1);")
        cursor.execute("CREATE TABLE IF NOT EXISTS BOOTH (idBooth INTEGER PRIMARY KEY, name TEXT NOT NULL, tarif REAL NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS SHOT (idShot INTEGER PRIMARY KEY, date TEXT DEFAULT (DATE('now')), ia integer, paiement REAL NOT NULL, folder not null, idBooth INTEGER NOT NULL, FOREIGN KEY (idBooth) REFERENCES BOOTH(idBooth))")
        cursor.execute("INSERT INTO BOOTH VALUES (1, 'OClock', 4);");
        cursor.execute("INSERT INTO BOOTH VALUES (2, 'Bikini', 4);");
        cursor.execute("INSERT INTO BOOTH VALUES (3, 'LaVoixDeSonMaître', 0);");

    conn.commit()

def connect_database():
    CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(Path(CURRENT_PATH, "booth.db"))
    create_tables(conn)
    return conn

def insert_shot(conn, ia, paiement, folder, idBooth):
    cursor = conn.cursor()

    # Insérer une nouvelle ligne dans la table SHOT en utilisant la date actuelle
    cursor.execute("INSERT INTO SHOT (ia, paiement, folder, idBooth) VALUES (?, ?, ?, ?);", (ia, paiement, folder, idBooth))

    conn.commit()


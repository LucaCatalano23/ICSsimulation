import tkinter as tk
import webbrowser
import threading
import time
import mysql.connector
from pyModbusTCP.client import ModbusClient
from flask import Flask, request, render_template, jsonify, url_for, redirect
from Configs import TAG, Controllers
from webauthn import (generate_registration_options, 
                          options_to_json, 
                          verify_registration_response, 
                          generate_authentication_options, 
                          verify_authentication_response)
from webauthn.helpers.structs import (AuthenticatorAttachment,
                                          AuthenticatorSelectionCriteria,
                                          ResidentKeyRequirement,
                                          UserVerificationRequirement)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url

app = Flask(__name__, static_url_path='/static' , static_folder='static')
    
privilege = ""

conn = mysql.connector.connect(
    host="192.168.0.30",  
    user="root",   
    password="root",
    port="3306",
    database="passwordless",
    auth_plugin='mysql_native_password'
)

@app.route('/', methods=['GET'])
def index():
    return render_template('login_admin.html')

@app.route('/createUser', methods=['GET'])
def createUser():
    return render_template('create_user.html')

@app.route('/createUser/register', methods=['POST'])
def register():
    global privilege
    try:
        data = request.json
        username = data.get('username')   
        privilege = data.get('menu')
        # Generare le opzioni di registrazione per il client. 
        # Authenticator_selection è un attributo opzionale
        # per definire meglio l'authenticator
        options = generate_registration_options(rp_id="localhost", 
                                                    rp_name="example",
                                                    user_name=username, 
                                                    authenticator_selection=AuthenticatorSelectionCriteria(
                                                        resident_key=ResidentKeyRequirement.REQUIRED,
                                                        user_verification=UserVerificationRequirement.PREFERRED))
        # Convertire le opzioni in JSON in quanto ci sono oggetti bytes che non possono essere serializzati
        json_options = options_to_json(options)
        
        # Restituire le opzioni al client
        response = jsonify(json_options)
        return response

    except Exception as e:
        privilege = ""
        print('Errore durante la registrazione fase 1:', e)
        return jsonify({'error': 'Errore durante la registrazione.'}), 500

@app.route('/createUser/complete-registration', methods=['POST'])
def complete_registration():
    global privilege
    try:
        data = request.json
        # Verificare le credenziali ricevute dal client
        result = verify_registration_response(credential=data.get('credential'), 
                                            expected_origin="https://localhost:5000", 
                                            expected_rp_id="localhost",
                                            expected_challenge=base64url_to_bytes(data.get("challenge")))
        
        # Aggiungere le credenziali al database
        cursor = conn.cursor()
        query = "INSERT INTO credentials (credential_id,credential_public_key,sign_count,aaguid,fmt,credential_type,user_verified,attestation_object,credential_device_type,credential_backed_up,privilege) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        values = (bytes_to_base64url(result.credential_id), result.credential_public_key, result.sign_count, result.aaguid, result.fmt, result.credential_type.value, result.user_verified, result.attestation_object, result.credential_device_type.value, result.credential_backed_up, privilege)
        cursor.execute(query, values)
        # Commit delle modifiche
        conn.commit()
        cursor.close()
        privilege = ""
        return jsonify({'success': True}), 200

    except Exception as e:
        privilege = ""
        print('Errore durante la registrazione fase 2:', e)
        return jsonify({'error': 'Errore durante la registrazione.'}), 500

@app.route('/auth', methods=['POST'])
def authenticate():
    try:
        # Generare le opzioni di autenticazione per il client
        options = generate_authentication_options(rp_id='localhost',
                                                  user_verification=UserVerificationRequirement.PREFERRED)

        # Convertire le opzioni in JSON in quanto ci sono oggetti bytes che non possono essere serializzati
        json_options = options_to_json(options)

        # Restituire le opzioni al client
        response = jsonify(json_options)
        return response

    except Exception as e:
        print('Errore durante l\'autenticazione:', e)
        return jsonify({'error': 'Errore durante l\'autenticazione.'}), 500

@app.route('/verify', methods=['POST'])
def verify():
    global authenticated
    try:
        data = request.json

        credential = data.get('credential')
        credential_id = credential.get("id")
        cursor = conn.cursor()
        query = "SELECT credential_public_key, sign_count FROM credentials WHERE credential_id = %s AND privilege = %s"
        values = (credential_id,"admin")
        cursor.execute(query, values)
        result = cursor.fetchall()
        cursor.close()
        credential_public_key, sign_count = result[0]
        # Verificare le credenziali ricevute dal client
        result = verify_authentication_response(credential=credential,
                                                expected_origin="https://localhost:5000", 
                                                expected_rp_id="localhost",
                                                expected_challenge=base64url_to_bytes(data.get("challenge")),
                                                credential_current_sign_count=sign_count,
                                                credential_public_key=credential_public_key,
                                                require_user_verification=True)
        authenticated = True
        return jsonify({'success': True}), 200

    except Exception as e:
        print('Errore durante la verifica delle credenziali:', e)
        return jsonify({'error': 'Errore durante la verifica delle credenziali.'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=('server.crt', 'server.key'))

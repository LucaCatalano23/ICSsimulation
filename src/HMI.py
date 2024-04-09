import sys
from flask import Flask, request, render_template, jsonify, url_for, redirect
from pyModbusTCP.client import ModbusClient
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
import mysql.connector

app = Flask(__name__, static_url_path='/static' , static_folder='static')

if len(sys.argv) < 2:
        sys.exit(1)
n_plc = int(sys.argv[1])
if n_plc == 1:
    adress = "https://localhost:5001"
else:
    adress = "https://localhost:5002"
        
client = ModbusClient(Controllers.PLC_CONFIG[n_plc]["ip"], Controllers.PLC_CONFIG[n_plc]["port"])

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
    return render_template('index.html', n_plc=n_plc)

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')    
        
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
        print('Errore durante la registrazione fase 1:', e)
        return jsonify({'error': 'Errore durante la registrazione.'}), 500

@app.route('/complete-registration', methods=['POST'])
def complete_registration():
    try:
        data = request.json
       
        # Verificare le credenziali ricevute dal client
        result = verify_registration_response(credential=data.get('credential'), 
                                            expected_origin=adress, 
                                            expected_rp_id="localhost",
                                            expected_challenge=base64url_to_bytes(data.get("challenge")))
        
        # Aggiungere le credenziali al database
        cursor = conn.cursor()
        query = "INSERT INTO credentials (credential_id,credential_public_key,sign_count,aaguid,fmt,credential_type,user_verified,attestation_object,credential_device_type,credential_backed_up) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        values = (bytes_to_base64url(result.credential_id), result.credential_public_key, result.sign_count, result.aaguid, result.fmt, result.credential_type.value, result.user_verified, result.attestation_object, result.credential_device_type.value, result.credential_backed_up)
        cursor.execute(query, values)
        # Commit delle modifiche
        conn.commit()
        cursor.close()
        
        return jsonify({'success': True}), 200

    except Exception as e:
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
    try:
        data = request.json

        credential = data.get('credential')
        credential_id = credential.get("id")
        cursor = conn.cursor()
        query = "SELECT credential_public_key, sign_count FROM credentials WHERE credential_id = %s"
        values = (credential_id,)
        cursor.execute(query, values)
        result = cursor.fetchall()
        cursor.close()
        credential_public_key, sign_count = result[0]
        # Verificare le credenziali ricevute dal client
        result = verify_authentication_response(credential=credential,
                                                expected_origin=adress, 
                                                expected_rp_id="localhost",
                                                expected_challenge=base64url_to_bytes(data.get("challenge")),
                                                credential_current_sign_count=sign_count,
                                                credential_public_key=credential_public_key,
                                                require_user_verification=True)
        
        return jsonify({'success': True}), 200

    except Exception as e:
        print('Errore durante la verifica delle credenziali:', e)
        return jsonify({'error': 'Errore durante la verifica delle credenziali.'}), 500

# Funzione per la visualizzazione del pannello di controllo e monitoraggio dell'HMI
@app.route('/panel')
def panel():
    return render_template('panel.html', n_plc=n_plc)

# Funzione per controllare avvio/arresto del flusso/deflusso d'acqua
@app.route('/control', methods=['POST'])
def control():
    data = request.json
    print(data)
    name = data.get('name')
    value = data.get('value')
    
    if name == "flow":
        client.write_single_coil(TAG.TAG_LIST[TAG.TANK_FLOW_ACTIVE]["id"], value)
    if name == "drain":
        client.write_single_coil(TAG.TAG_LIST[TAG.TANK_DRAIN_ACTIVE]["id"], value)
    
    return 'OK', 200

# Funzione che mi permette di monitorare il livello dell'acqua, il flusso e il deflusso
@app.route('/monitor', methods=['GET'])
def monitor():
    level = client.read_holding_registers(TAG.TAG_LIST[TAG.TANK_LEVEL]["id"])[0]
    flow_rate = client.read_holding_registers(TAG.TAG_LIST[TAG.TANK_FLOW_RATE]["id"])[0]
    drain_rate = client.read_holding_registers(TAG.TAG_LIST[TAG.TANK_DRAIN_RATE]["id"])[0]
    values = {'level': level, 'flow_rate': flow_rate, 'drain_rate': drain_rate}
    return jsonify(values)

# Funzione per aggiornare la velocità di flusso 
@app.route('/flowUpdate', methods=['POST'])
def flowUpdate():
    data = request.json
    value = data.get('value')
    client.write_single_register(TAG.TAG_LIST[TAG.TANK_FLOW_RATE]["id"], int(value))
    return 'OK', 200

# Funzione per aggiornare la velocità di deflusso
@app.route('/drainUpdate', methods=['POST'])
def drainUpdate():
    data = request.json
    value = data.get('value')
    client.write_single_register(TAG.TAG_LIST[TAG.TANK_DRAIN_RATE]["id"], int(value))
    return 'OK', 200

if __name__ == "__main__":
    try:
        client.open()
        if n_plc == 1:
            app.run(host='0.0.0.0', port=5001, debug=True, ssl_context=('server.crt', 'server.key'))
        else:
            app.run(host='0.0.0.0', port=5002, debug=True, ssl_context=('server.crt', 'server.key'))
    except Exception as e:
        print(f"Errore durante la comunicazione con il server: {e}")
    finally:
        client.close()
        
        
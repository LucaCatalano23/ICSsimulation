import gpiozero
import tkinter as tk
import webbrowser
import sys
import mysql.connector
import threading
import time
from pyModbusTCP.client import ModbusClient
from flask import Flask, request, render_template, jsonify
from webauthn import (options_to_json, 
                      generate_authentication_options, 
                      verify_authentication_response)
from webauthn.helpers.structs import UserVerificationRequirement
from webauthn.helpers import base64url_to_bytes

app = Flask(__name__, static_url_path='/static' , static_folder='static')

adress = ""
authenticated = False
server_on = False

conn = mysql.connector.connect(
    host="192.168.123.1",  
    user="root",   
    password="root",
    port="3306",
    database="passwordless",
    auth_plugin='mysql_native_password'
)

@app.route('/', methods=['GET'])
def index():
    return render_template('login.html', n_plc="Robotic arm")

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
        authenticated = True
        return jsonify({'success': True}), 200

    except Exception as e:
        print('Errore durante la verifica delle credenziali:', e)
        return jsonify({'error': 'Errore durante la verifica delle credenziali.'}), 500

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HMI - Control Panel")
        
        # Creazione dei frame per le interfacce
        self.login = Login(self)
        self.panel = Panel(self)
        # Mostra il primo frame all'avvio dell'applicazione
        self.show_frame(self.login)

    def show_frame(self, frame):
        # Mostra il frame desiderato
        frame.pack(fill="both", expand=True)

        # Nasconde gli altri frame
        for child in self.winfo_children():
            if child != frame:
                child.pack_forget()

class Login(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        label = tk.Label(self, text="HMI Robotic arm ")
        label.pack()
        
        # Pulsante per passare alla seconda interfaccia
        button = tk.Button(self, text="Login", command=self.open_webpage)
        button.pack()
        
        # Dimensioni del frame di login
        self.configure(width=500, height=300) 
    
    def open_webpage(self):
            # URL della pagina web da aprire
            global adress
            global server_on

            if(server_on == False):
                port = 5000
                adress = f"https://localhost:{port}"
                threading.Thread(target=self.start_server, daemon=True, args=(port,)).start()
                server_on = True
                time.sleep(1)        
                
            webbrowser.open(adress)
            
            self.parent.after(1000, self.check_authenticated)
            
    def check_authenticated(self):
        global authenticated
        if not authenticated:
            self.parent.after(1000, self.check_authenticated)
        else:
            self.master.show_frame(self.master.panel)
        
    def start_server(self,port):
        try:
            app.run(host='0.0.0.0', port=port, ssl_context=('server.crt', 'server.key'))
        except Exception as e:
            print(f"Errore durante la comunicazione con il server: {e}")

class Panel(tk.Frame):
	def __init__(self, parent):
		super().__init__(parent)
		self.client = ModbusClient("192.168.123.2", 1025)
             
		self.claw_close = gpiozero.Button(17)
		self.claw_open = gpiozero.Button(4)
		self.base_left = gpiozero.Button(27)
		self.base_right = gpiozero.Button(22)
		self.lenght_short = gpiozero.Button(5)
		self.lenght_long = gpiozero.Button(6)
		self.height_short = gpiozero.Button(13)
		self.height_high = gpiozero.Button(19)
				
		threading.Thread(target=self.controls, daemon=True).start()
		    
		label = tk.Label(self, text="Use the commands to control the robotic arm ")
		label.pack()
		
		#Logout
		logout_button = tk.Button(self, text="Logout", command=self.quit)
		logout_button.pack()
		
		# Dimensioni del frame di login
		self.configure(width=500, height=300) 
            
	def controls(self):
		global authenticated
		while True:
			if authenticated:
				if(self.claw_close.is_pressed):
					self.send_command(0)
					time.sleep(0.02)
				if(self.claw_open.is_pressed):
					self.send_command(1)
					time.sleep(0.02)
				if(self.base_left.is_pressed):
					self.send_command(3)
					time.sleep(0.02)				
				if(self.base_right.is_pressed):
					self.send_command(2)
					time.sleep(0.02)
				if(self.lenght_short.is_pressed):
					self.send_command(7)
					time.sleep(0.02)
				if(self.lenght_long.is_pressed):
					self.send_command(6)
					time.sleep(0.02)
				if(self.height_short.is_pressed):
					self.send_command(5)
					time.sleep(0.02)
				if(self.height_high.is_pressed):
					self.send_command(4)
					time.sleep(0.02)
						
	def send_command(self, coil):
		self.client.write_single_coil(coil, True)
        
	def quit(self):
		self.client.close()
		global authenticated
		authenticated = False
		self.master.show_frame(self.master.login)
        
if __name__ == "__main__":
	ui = App()
	ui.mainloop()

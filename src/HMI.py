import tkinter as tk
import webbrowser
import threading
import time
import sys
import mysql.connector
from pyModbusTCP.client import ModbusClient
from flask import Flask, request, render_template, jsonify
from Configs import TAG, Controllers
from webauthn import (options_to_json, 
                      generate_authentication_options, 
                      verify_authentication_response)
from webauthn.helpers.structs import UserVerificationRequirement
from webauthn.helpers import base64url_to_bytes

app = Flask(__name__, static_url_path='/static' , static_folder='static')
    
address = ""
n_plc = -1
hmi = -1
authenticated = False
server_on = False

if len(sys.argv) < 2:
        sys.exit(1)
hmi = int(sys.argv[1])

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
    global n_plc
    return render_template('login.html', n_plc=n_plc)

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
                                                expected_origin=address, 
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
                
        global hmi
        label = tk.Label(self, text="HMI " + str(hmi))
        label.pack()
        
        # Lista delle opzioni del menu a tendina
        options = ["PLC 1", "PLC 2", "Robotic arm"]
    
        # Variabile per memorizzare l'opzione selezionata
        self.selected_var = tk.StringVar()
        self.selected_var.set(options[0])  # Imposta l'opzione predefinita

        # Creazione del menu a tendina
        self.option_menu = tk.OptionMenu(self, self.selected_var, *options)
        self.option_menu.pack(padx=10, pady=10)

        # Pulsante per passare alla seconda interfaccia
        button = tk.Button(self, text="Login", command=self.open_webpage)
        button.pack()
        
        # Dimensioni del frame di login
        self.configure(width=500, height=300) 
    
    def open_webpage(self):
            # URL della pagina web da aprire
            choice = self.selected_var.get()
            global n_plc
            global hmi
            global address
            global server_on
            if choice == "PLC 1":
                n_plc = 1
            elif choice == "PLC 2":
                n_plc = 2
            elif choice == "Robotic arm":
                n_plc = 0

            if(server_on == False):
                port = 5000 + hmi
                address = f"https://localhost:{port}"
                threading.Thread(target=self.start_server, daemon=True, args=(port,)).start()
                server_on = True
                time.sleep(1)        
                
            webbrowser.open(address)
            
            global authenticated
            while authenticated == False:
                time.sleep(1)
            if n_plc == 0:
                panel = RoboticPanel(self.master)
                self.master.show_frame(panel)
            else:
                panel = Panel(self.master)
                self.master.show_frame(panel)
        
    def start_server(self,port):
        try:
            app.run(host='0.0.0.0', port=port, ssl_context=('server.crt', 'server.key'))
        except Exception as e:
            print(f"Errore durante la comunicazione con il server: {e}")
            
class Panel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        global n_plc
        global hmi
        self.client = ModbusClient(Controllers.PLC_CONFIG[n_plc]["ip"], Controllers.PLC_CONFIG[n_plc]["port"])
        
        # Definizione delle variabili per i valori di flusso e drenaggio
        flow_rate_value = tk.StringVar()
        drain_rate_value = tk.StringVar()

        # Creazione del frame principale
        container = tk.Frame(self)
        container.pack(padx=10, pady=10)

        # Titolo
        title_label = tk.Label(container, text="HMI " + str(hmi) + "del PLC " + str(n_plc) + " - Control Panel")
        title_label.config(font=("Arial", 16))
        title_label.grid(row=0, column=0, columnspan=2)

        # Sezione Flow Rate
        flow_label = tk.Label(container, text="Flow Rate")
        flow_label.grid(row=1, column=0, sticky="w", pady=5)

        self.flow_value_label = tk.Label(container, text="")
        self.flow_value_label.grid(row=1, column=1, sticky="w", pady=5)
        
        self.flow_box = tk.Entry(container, textvariable=flow_rate_value)
        self.flow_box.grid(row=1, column=2, pady=5)

        flow_button = tk.Button(container, text="Update", command=self.update_flow_rate)
        flow_button.grid(row=1, column=3, pady=5)

        # Sezione Drain Rate
        drain_label = tk.Label(container, text="Drain Rate")
        drain_label.grid(row=2, column=0, sticky="w", pady=5)

        self.drain_value_label = tk.Label(container, text="")
        self.drain_value_label.grid(row=2, column=1, sticky="w", pady=5)
        
        self.drain_box = tk.Entry(container, textvariable=drain_rate_value)
        self.drain_box.grid(row=2, column=2, pady=5)

        drain_button = tk.Button(container, text="Update", command=self.update_drain_rate)
        drain_button.grid(row=2, column=3, pady=5)

        # Sezione Water Level
        water_level_label = tk.Label(container, text="Water Level")
        water_level_label.grid(row=3, column=0, sticky="w", pady=5)

        self.water_level_value = tk.Label(container, text="(max 1000)")
        self.water_level_value.grid(row=3, column=1, pady=5)

        # Sezione Flow Control (checkbox)
        self.flow = tk.BooleanVar()
        flow_control_label = tk.Label(container, text="Flow Control")
        flow_control_label.grid(row=4, column=0, sticky="w", pady=5)

        flow_control_checkbox = tk.Checkbutton(container, variable=self.flow, command=self.flow_change)
        flow_control_checkbox.grid(row=4, column=1, pady=5)

        # Sezione Drain Control (checkbox)
        self.drain = tk.BooleanVar()
        drain_control_label = tk.Label(container, text="Drain Control")
        drain_control_label.grid(row=5, column=0, sticky="w", pady=5)

        drain_control_checkbox = tk.Checkbutton(container, variable=self.drain, command=self.drain_change)
        drain_control_checkbox.grid(row=5, column=1, pady=5)

        #Logout
        logout_button = tk.Button(container, text="Logout", command=self.quit)
        logout_button.grid(row=6, column=0, columnspan=3, pady=5)

        self.stop_flag = threading.Event()
        threading.Thread(target=self.monitor, daemon=True).start()

    #Qui aggiorna ogni secondo i dati provenienti dal PLC
    def monitor(self):
        while not self.stop_flag.is_set():
            level = self.client.read_holding_registers(TAG.TAG_LIST[TAG.TANK_LEVEL]["id"])[0]
            self.water_level_value.config(text=str(level)+" (max 1000)")
            flow_rate = self.client.read_holding_registers(TAG.TAG_LIST[TAG.TANK_FLOW_RATE]["id"])[0]
            self.flow_value_label.config(text=flow_rate)
            drain_rate = self.client.read_holding_registers(TAG.TAG_LIST[TAG.TANK_DRAIN_RATE]["id"])[0]
            self.drain_value_label.config(text=drain_rate)
            time.sleep(1)
   
    # Qui puoi inserire la logica per aggiornare il tasso di flusso     
    def update_flow_rate(self):
        flow_rate_value = self.flow_box.get()
        self.client.write_single_register(TAG.TAG_LIST[TAG.TANK_FLOW_RATE]["id"], int(flow_rate_value))

    # Qui puoi inserire la logica per aggiornare il tasso di drenaggio
    def update_drain_rate(self):
        drain_rate_value = self.drain_box.get()
        self.client.write_single_register(TAG.TAG_LIST[TAG.TANK_DRAIN_RATE]["id"], int(drain_rate_value))

    # Funzione per controllare avvio/arresto del flusso d'acqua
    def flow_change(self):
        self.client.write_single_coil(TAG.TAG_LIST[TAG.TANK_FLOW_ACTIVE]["id"], self.flow.get())

    # Funzione per controllare avvio/arresto del drenaggio d'acqua
    def drain_change(self):
        self.client.write_single_coil(TAG.TAG_LIST[TAG.TANK_DRAIN_ACTIVE]["id"], self.drain.get())

    # Funzione per tornare alla schermata di login
    def quit(self):
        self.stop_flag.set()
        self.client.close()
        global authenticated
        authenticated = False
        self.master.show_frame(self.master.login)

class RoboticPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.client = ModbusClient(host="192.168.123.2",port=1025)

        # Griglia per i comandi WASD
        frame_wasd = tk.Frame(self)
        frame_wasd.pack(side=tk.LEFT, padx=10)
        self.w = tk.Button(frame_wasd, text="W", command=lambda: self.send_command(0))
        self.w.grid(row=0, column=1, pady=5)
        self.a = tk.Button(frame_wasd, text="A", command=lambda: self.send_command(3))
        self.a.grid(row=1, column=0, padx=5)
        self.s = tk.Button(frame_wasd, text="S", command=lambda: self.send_command(1))
        self.s.grid(row=2, column=1, pady=5)
        self.d = tk.Button(frame_wasd, text="D", command=lambda: self.send_command(2))
        self.d.grid(row=1, column=2, padx=5)

        # Griglia per i comandi freccia
        frame = tk.Frame(self)
        frame.pack(side=tk.RIGHT, padx=10)
        self.up = tk.Button(frame, text="⇧", command=lambda: self.send_command(4))
        self.up.grid(row=0, column=1, pady=5)
        self.left = tk.Button(frame, text="⇦", command=lambda: self.send_command(7))
        self.left.grid(row=1, column=0, padx=5)
        self.down = tk.Button(frame, text="⇩", command=lambda: self.send_command(5))
        self.down.grid(row=2, column=1, pady=5)
        self.right = tk.Button(frame, text="⇨", command=lambda: self.send_command(6))
        self.right.grid(row=1, column=2, padx=5)
                
        #Logout
        logout_button = tk.Button(frame, text="Logout", command=self.quit)
        logout_button.grid(row=3, column=2, columnspan=3, pady=5)
            
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
    

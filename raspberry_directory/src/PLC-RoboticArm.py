from gpiozero import Servo
from time import sleep
from gpiozero.pins.pigpio import PiGPIOFactory
import math
from pyModbusTCP.server import ModbusServer

# Definisco la classe PLC
class PLC:
        def __init__(self):
                self.server = ModbusServer("192.168.123.2", 1025, no_block=True)
                factory = PiGPIOFactory(host="192.168.123.2", port=8888)
                self.claw = Servo(12, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory=factory)
                self.base = Servo(16, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory=factory)
                self.height = Servo(21, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory=factory)
                self.lenght= Servo(20, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory=factory)
                claw_pos = 270
                base_pos = 180
                height_pos = 230
                lenght_pos = 180
                self.set_registers(claw_pos, base_pos, height_pos, lenght_pos)
                self.boot_arm()

        def set_registers(self, claw_pos, base_pos, height_pos, lenght_pos):
                self.server.data_bank.set_holding_registers(0, [claw_pos])
                self.server.data_bank.set_holding_registers(1, [base_pos])
                self.server.data_bank.set_holding_registers(2, [height_pos])
                self.server.data_bank.set_holding_registers(3, [lenght_pos])
                
        def boot_arm(self):
                self.claw.value = math.sin(math.radians(self.server.data_bank.get_holding_registers(0)[0]))
                self.base.value = math.sin(math.radians(self.server.data_bank.get_holding_registers(1)[0]))
                self.height.value = math.sin(math.radians(self.server.data_bank.get_holding_registers(2)[0]))
                self.lenght.value = math.sin(math.radians(self.server.data_bank.get_holding_registers(3)[0]))
                
        def control(self):
                claw_close = self.server.data_bank.get_coils(0)[0]
                claw_open = self.server.data_bank.get_coils(1)[0]
                self.move_claw(claw_close, claw_open)
                base_right = self.server.data_bank.get_coils(2)[0]
                base_left = self.server.data_bank.get_coils(3)[0]
                self.move_base(base_right, base_left)
                height_up = self.server.data_bank.get_coils(4)[0]
                height_down = self.server.data_bank.get_coils(5)[0]
                self.move_height(height_up, height_down)
                lenght_long = self.server.data_bank.get_coils(6)[0]
                lenght_short = self.server.data_bank.get_coils(7)[0]
                self.move_lenght(lenght_long, lenght_short)
                
        def move_claw(self, close, Open):
                pos = self.server.data_bank.get_holding_registers(0)[0]
                if(close and pos < 270):
                        pos = pos + 1
                        self.server.data_bank.set_coils(0, [False])
                        self.server.data_bank.set_holding_registers(0, [pos])
                if(Open and pos > 160):
                        pos = pos- 1 
                        self.server.data_bank.set_coils(1, [False])
                        self.server.data_bank.set_holding_registers(0, [pos])
                self.claw.value = math.sin(math.radians(pos))
            
        def move_base(self, right, left):
                pos = self.server.data_bank.get_holding_registers(1)[0]
                if(right and pos < 270):
                        pos = pos + 1
                        self.server.data_bank.set_coils(2, [False])
                        self.server.data_bank.set_holding_registers(1, [pos])
                if(left and pos > 90):
                        pos = pos- 1 
                        self.server.data_bank.set_coils(3, [False])
                        self.server.data_bank.set_holding_registers(1, [pos])
                self.base.value = math.sin(math.radians(pos))
                
        def move_height(self, up, down):
                pos = self.server.data_bank.get_holding_registers(2)[0]
                if(up and pos < 270):
                        pos = pos + 1
                        self.server.data_bank.set_coils(4, [False])
                        self.server.data_bank.set_holding_registers(2, [pos])
                if(down and pos > 200):
                        pos = pos- 1 
                        self.server.data_bank.set_coils(5, [False])
                        self.server.data_bank.set_holding_registers(2, [pos])
                self.height.value = math.sin(math.radians(pos))
                
        def move_lenght(self, Long, short):
                pos = self.server.data_bank.get_holding_registers(3)[0]
                if(Long and pos < 270):
                        pos = pos + 1
                        self.server.data_bank.set_coils(6, [False])
                        self.server.data_bank.set_holding_registers(3, [pos])
                if(short and pos > 90):
                        pos = pos- 1 
                        self.server.data_bank.set_coils(7, [False])
                        self.server.data_bank.set_holding_registers(3, [pos])
                self.lenght.value = math.sin(math.radians(pos))
        
        def main(self):      
                try:
                        self.server.start()
                        while True:
                                self.control()
                except Exception as e:
                        print(e)
                        self.server.stop()
            
if __name__ == "__main__":
        # Creo un'istanza del PLC e avvio la funzione main
        plc = PLC()
        plc.main()


class TAG:
    TANK_LEVEL = 'tank_level'
    TANK_MAX_LEVEL = 'tank_max_level'
    TANK_FLOW_RATE = 'tank_flow_rate' 
    TANK_DRAIN_RATE = 'tank_drain_rate'
    TANK_FLOW_ACTIVE = 'tank_flow_active'
    TANK_DRAIN_ACTIVE = 'tank_drain_active'

    TAG_LIST = {
        # tag_name (tag_id, PLC number, input/output, fault (just for inputs)
        TANK_LEVEL : {'id': 0, 'plc': 1, 'type': 'register', 'fault': 0.0, 'default': 1000},
        TANK_FLOW_RATE : {'id': 1, 'plc': 1, 'type': 'register', 'fault': 0.0, 'default': 5},
        TANK_DRAIN_RATE : {'id': 2, 'plc': 1, 'type': 'register', 'fault': 0.0, 'default': 10},
        TANK_MAX_LEVEL : {'id': 5, 'plc': 1, 'type': 'input',  'fault': 0.0, 'default': 1000},
        TANK_FLOW_ACTIVE : {'id': 1, 'plc': 1, 'type': 'coil',  'fault': 0.0, 'default': False},
        TANK_DRAIN_ACTIVE : {'id': 2, 'plc': 1, 'type': 'coil',  'fault': 0.0, 'default': False}
    }

class Controllers:
    PLC_CONFIG = {
            1: {
                'name': 'plc1',
                'ip': '192.168.0.11',
                'port': 502,
                'protocol': 'ModbusWriteRequest-TCP'
            },
            2: {
                'name': 'plc2',
                'ip': '192.168.0.12',
                'port': 502,
                'protocol': 'ModbusWriteRequest-TCP'
            }
    }
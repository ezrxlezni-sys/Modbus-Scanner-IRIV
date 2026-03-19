import board
import time
from umodbus.serial import Serial as ModbusRTUMaster

# List of baudrates
baudrates = [9600, 4800]

# Slave ID range
slave_ids = range(1, 248)

def scan_modbus():

    host = None  # Keep reference to previous host

    for baud in baudrates:

        print("\nTesting Baudrate:", baud)

        # Deinitialize previous UART before switching baudrate
        if host is not None:
            try:
                host._uart.deinit()
                print("Previous UART deinitialized")
            except:
                pass

        # Create new Modbus master with new baudrate
        host = ModbusRTUMaster(
            tx_pin=board.TX,
            rx_pin=board.RX,
            baudrate=baud
        )

        for slave in slave_ids:

            try:
                print("  Trying Slave ID:", slave)

                data = host.read_holding_registers(
                    slave_addr=slave,
                    starting_addr=0,
                    register_qty=1,
                    signed=False
                )

                print("FOUND device!")
                print("Baudrate:", baud)
                print("Slave ID:", slave)
                print("Data:", data)

                time.sleep(0.1)

            except Exception:
                print("    No response")
                continue


scan_modbus()

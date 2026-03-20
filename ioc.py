import board
import time
from umodbus.serial import Serial as ModbusRTUMaster

baudrates = [9600, 4800]
slave_ids = range(1, 248)

def scan_modbus():
    host = None

    for baud in baudrates:
        print("\nTesting Baudrate:", baud)

        if host is not None:
            try:
                host._uart.deinit()
                print("Previous UART deinitialized")
            except:
                pass

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


if __name__ == "__main__":
    scan_modbus()

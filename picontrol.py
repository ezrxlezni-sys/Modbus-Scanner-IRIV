import sys
import os

BAUDRATES = [9600, 4800]
SLAVE_IDS = range(1, 248)


def scan_modbus():
    found = []

    for baud in BAUDRATES:
        print("\nTesting baudrate:", baud)

        for slave_id in SLAVE_IDS:
            try:
                # Assume IRIV handles Modbus internally
                # Replace this with your IRIV read function
                response = read_modbus(slave_id, baud)

                if response:
                    print("FOUND -> Baudrate:", baud, "Slave ID:", slave_id)
                    found.append((baud, slave_id))
                else:
                    print("No response -> Slave ID:", slave_id)

            except Exception as e:
                print("Error -> Slave ID:", slave_id, e)

    print("\n=== RESULT ===")
    if found:
        for f in found:
            print("Baudrate:", f[0], "Slave ID:", f[1])
    else:
        print("No device found")


# Dummy function (YOU replace this with IRIV function)
def read_modbus(slave_id, baud):
    """
    Replace this with your IRIV Modbus read function
    Example:
    host.read_holding_registers(...)
    """
    return None  # placeholder


if __name__ == "__main__":
    scan_modbus()

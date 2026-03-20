import sys
import os

CURRENT_DIR = os.path.dirname(__file__)
LIB_PATH = os.path.join(CURRENT_DIR, "lib")

if LIB_PATH not in sys.path:
    sys.path.insert(0, LIB_PATH)

PORT = "/dev/ttyACM0"
BAUDRATES = [9600, 4800]
SLAVE_IDS = range(1, 248)
TIMEOUT = 0.3


def crc16_modbus(data: bytes) -> bytes:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack("<H", crc)


def build_read_request(slave_id: int, reg_addr: int = 0, reg_qty: int = 1) -> bytes:
    pdu = struct.pack(">BHH", 3, reg_addr, reg_qty)
    adu_no_crc = struct.pack(">B", slave_id) + pdu
    return adu_no_crc + crc16_modbus(adu_no_crc)


def scan_modbus():
    found = []

    for baud in BAUDRATES:
        print(f"\n[INFO] Testing baudrate {baud}")

        try:
            ser = serial.Serial(PORT, baudrate=baud, bytesize=8, parity="N", stopbits=1, timeout=TIMEOUT)
        except Exception as e:
            print(f"[ERROR] Cannot open port: {e}")
            continue

        for slave_id in SLAVE_IDS:
            try:
                request = build_read_request(slave_id, 0, 1)

                ser.reset_input_buffer()
                ser.write(request)
                ser.flush()

                time.sleep(0.05)
                response = ser.read(64)

                if len(response) >= 5:
                    print(f"[FOUND] Slave ID {slave_id} at baudrate {baud} -> {response.hex(' ')}")
                    found.append((baud, slave_id, response.hex(' ')))
                else:
                    print(f"[NO] Slave ID {slave_id}")

            except Exception as e:
                print(f"[ERR] Slave ID {slave_id}: {e}")

        ser.close()

    print("\n=== Scan Result ===")
    if found:
        for item in found:
            print(f"Baudrate={item[0]}, Slave ID={item[1]}, Response={item[2]}")
    else:
        print("No device found.")


if __name__ == "__main__":
    scan_modbus()

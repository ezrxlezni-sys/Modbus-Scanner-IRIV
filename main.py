import serial
import struct
import time

PORT = "/dev/ttyACM0"
BAUDRATES = [9600]
SLAVE_IDS = range(1, 248)
TIMEOUT = 0.5

def crc16_modbus(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack("<H", crc)

def validate_response(response, slave_id):
    """Check that the response actually belongs to this slave ID."""
    if len(response) < 5:
        return False
    if response[0] != slave_id:          # ← NEW: match slave ID
        return False
    # Validate CRC
    payload = response[:-2]
    expected_crc = crc16_modbus(payload)
    actual_crc = response[-2:]
    return actual_crc == expected_crc     # ← NEW: CRC check

def build_read_request(slave_id, reg_addr=0, reg_qty=1):
    pdu = struct.pack(">BHH", 3, reg_addr, reg_qty)
    adu_no_crc = struct.pack(">B", slave_id) + pdu
    return adu_no_crc + crc16_modbus(adu_no_crc)

def scan_modbus():
    found = []
    for baud in BAUDRATES:
        # Calculate inter-frame delay: 3.5 char times at this baud
        char_time = 10 / baud  # 10 bits per char (8N1 + start/stop)
        inter_frame_delay = max(char_time * 3.5, 0.002)  # min 2ms per spec

        print(f"\n[INFO] Testing baudrate {baud}, inter-frame delay: {inter_frame_delay*1000:.1f}ms")
        try:
            ser = serial.Serial(
                PORT,
                baudrate=baud,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=TIMEOUT
            )
        except Exception as e:
            print(f"[ERROR] Cannot open port: {e}")
            continue

        for slave_id in SLAVE_IDS:
            try:
                request = build_read_request(slave_id, 0, 1)

                ser.reset_input_buffer()
                ser.write(request)
                ser.flush()

                time.sleep(inter_frame_delay)   # ← proper Modbus gap

                response = ser.read(7)          # ← expect exactly 7 bytes for FC03/1reg

                if validate_response(response, slave_id):
                    print(f"[FOUND] Slave ID {slave_id} at {baud} baud -> {response.hex(' ')}")
                    found.append((baud, slave_id, response.hex(' ')))
                else:
                    print(f"[NO]    Slave ID {slave_id}")

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

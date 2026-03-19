import sys

def detect_platform():

    # --- Microcontroller detection ---
    try:
        if sys.implementation.name in ("micropython", "circuitpython"):
            return "Microcontroller"
    except:
        pass

    # --- Raspberry Pi detection ---
    try:
        with open("/proc/cpuinfo") as f:
            if "Raspberry Pi" in f.read():
                return "Raspberry Pi"
    except:
        pass

    return "Unknown"


def main():

    platform_type = detect_platform()

    print("Detected Platform:", platform_type)

    if platform_type == "Raspberry Pi":

        print("Running PiControl Modbus Scanner...")
        import picontrol
        picontrol.scan_modbus()

    elif platform_type == "Microcontroller":

        print("Microcontroller detected (scanner not implemented yet)")

    else:
        print("Unsupported platform")


if __name__ == "__main__":
    main()

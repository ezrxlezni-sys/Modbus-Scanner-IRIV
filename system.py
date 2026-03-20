def detect_platform():
    # --- Check Microcontroller (MicroPython) ---
    print("Checking board using MicroPython method...")
    try:
        import board
        return "Microcontroller"
    except:
        pass

    # --- Check Raspberry Pi (Linux) ---
    print("Checking board using Linux cpuinfo...")
    try:
        with open("/proc/cpuinfo", "r") as f:
            if "Raspberry Pi" in f.read():
                return "Raspberry Pi"
    except:
        pass

    return "Unknown"


def main():
    platform = detect_platform()
    print("Detected Platform:", platform)

    if platform == "Microcontroller":
        import ioc
        ioc.scan_modbus()

    elif platform == "Raspberry Pi":
        import picontrol
        picontrol.scan_modbus()

    else:
        print("Unsupported platform")


if __name__ == "__main__":
    main()

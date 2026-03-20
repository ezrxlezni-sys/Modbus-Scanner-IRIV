def detect_platform():
    # --- Check CircuitPython board ---
    print("Checking board using CircuitPython method...")
    try:
        import board
        return "IOC"
    except Exception:
        pass

    # --- Check Raspberry Pi (Linux) ---
    print("Checking board using Linux cpuinfo...")
    try:
        with open("/proc/cpuinfo", "r") as f:
            if "Raspberry Pi" in f.read():
                return "PiControl"
    except Exception:
        pass

    return "Unknown"


def main():
    platform = detect_platform()
    print("Detected Platform:", platform)

    if platform == "IOC":
        from ioc import scan_modbus
        scan_modbus()

    elif platform == "PiControl":
        from picontrol import scan_modbus
        scan_modbus()

    else:
        print("Unsupported platform")


if __name__ == "__main__":
    main()

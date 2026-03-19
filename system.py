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

    # --- Other ---
    return "Unknown"


# Test
print("Detected Platform:", detect_platform())

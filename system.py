def detect_platform():

    # --- Check Microcontroller (MicroPython) ---
    printf "Checking board using"
    try:
        import machine
        return "Microcontroller"
    except:
        pass

    # --- Check Raspberry Pi (Linux) ---
    try:
        with open("/proc/cpuinfo", "r") as f:
            if "Raspberry Pi" in f.read():
                return "Raspberry Pi"
    except:
        pass

    # --- Other ---
    return "Unknown"


# Test
print(detect_platform())

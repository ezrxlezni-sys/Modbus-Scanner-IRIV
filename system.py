def detect_board():
    
    # --- Try MicroPython board detection ---
    try:
        import machine
        
        board = machine.uname().machine
        
        if "RP2" in board or "rp2" in board or "RP2040" in board:
            return "RP2035 / RP2040 Board"
        
        return "MicroPython Board (Unknown)"
    
    except:
        pass

    # --- Try Raspberry Pi detection ---
    try:
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()

        if "Raspberry Pi" in cpuinfo:
            if "BCM2711" in cpuinfo:
                return "Raspberry Pi 4"
            else:
                return "Raspberry Pi (Other Model)"
    
    except:
        pass

    # --- Fallback ---
    import platform
    return f"Unknown Platform ({platform.system()})"


# Test
print(detect_board())

#  Copyright (c) 2026, Greg Michael
#  Licensed under BSD 3-Clause License. See LICENSE.txt for details.

import sys
import platform
import ctypes
import multiprocessing

# delay craterstats imports to allow rapid starting message

def main():
    if len(sys.argv) > 1:
        import craterstats.cli as cli
        cli.main(sys.argv[1:])
    else:
        print("\n  Starting Craterstats-III GUI...", end="", flush=True)
        import craterstatsGUI.gui as gui
        if platform.system() == "Windows":
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0) # hide console
        gui.main()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
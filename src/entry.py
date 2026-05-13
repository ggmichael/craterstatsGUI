#  Copyright (c) 2026, Greg Michael
#  Licensed under BSD 3-Clause License. See LICENSE.txt for details.

import sys
import platform
import ctypes
import multiprocessing
import craterstatsGUI.gui as gui
import craterstats.cli as cli

def main():
    if len(sys.argv) > 1:
        cli.main(sys.argv[1:])
    else:
        if platform.system() == "Windows":
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0) # hide console
        gui.main()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
#!/usr/bin/env python

import craterstatsGUI.gui as gui
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    gui.main()

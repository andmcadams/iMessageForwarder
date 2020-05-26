import threading
import sys
import signal
import time
import updater
import gui

if __name__ == '__main__':
    def terminateUpdateThread(signalNumber=0, frame=None):
        t1.stopThread()
        t2.stopThread()
        sys.exit(0)
    signal.signal(signal.SIGINT, terminateUpdateThread)
    t1 = updater.UpdaterThread()
    t1.start()
    t2 = gui.GuiThread()
    t2.daemon = True
    t2.start()
    t2.join()
    terminateUpdateThread()

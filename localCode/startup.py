import threading
import signal
import time
import updater
import gui

if __name__ == '__main__':
    def terminateThreads(signalNumber, frame):
        t1.stopThread()
    signal.signal(signal.SIGINT, terminateThreads)
    t1 = updater.UpdaterThread()
    t1.start()
    t2 = threading.Thread(target=lambda debug=0: gui.runGui(debug))
    t2.daemon = True
    t2.start()

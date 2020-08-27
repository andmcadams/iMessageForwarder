import threading
import sys
import signal
import time
import updater
import gui
import getopt

def handleOptions(argv):
    try:
        opts, args = getopt.getopt(argv, "d", ["debug"])
    except getopt.GetoptError as e:
        print(e)
        sys.exit(1)
    
    for opt, arg in opts:
        if opt == '-d':
            print('Debug coloring turned on.')
            return True
    return False

if __name__ == '__main__':
    debug = False
    if len(sys.argv) > 1:
        debug = handleOptions(sys.argv[1:])
    def terminateUpdateThread(signalNumber=0, frame=None):
        t1.stopThread()
        t2.stopThread()
        sys.exit(0)
    signal.signal(signal.SIGINT, terminateUpdateThread)
    t1 = updater.UpdaterThread()
    t1.start()
    t2 = gui.GuiThread(debug=debug)
    t2.daemon = True
    t2.start()
    t2.join()
    terminateUpdateThread()

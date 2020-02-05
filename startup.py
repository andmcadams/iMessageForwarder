import threading
import time
import updater
import gui

if __name__ == '__main__':
	t1 = threading.Thread(target=updater.runUpdater)
	t1.start()
	t2 = threading.Thread(target=gui.runGui)
	t2.start()

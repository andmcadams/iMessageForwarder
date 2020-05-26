import threading
import json
import subprocess
import time
import sqlite3
import os

dirname = os.path.dirname(__file__)
secretsFile = os.path.join(dirname, 'secrets.json')
secrets = json.load(open(secretsFile))

user = secrets['user']
ip = secrets['ip']
scriptPath = secrets['scriptPath']
retrieveScriptPath = secrets['retrieveScriptPath']

def updateLastAccess(newTime):
	global lastAccess
	lastAccess = newTime
	print('Last access time updated to {}'.format(lastAccess))

def readLastAccess():
	try:
		with open(os.path.join(dirname, 'data.json')) as infile:
			data = json.load(infile)
			updateLastAccess(data['lastAccess'])
	except FileNotFoundError as e:
		# This is hit when the data.json file is blank.
		updateLastAccess(0)	

def writeLastAccess():
	with open(os.path.join(dirname, 'data.json'), 'w+') as outfile:
		try:
			data = json.load(outfile)
			data['lastAccess'] = lastAccess
		except json.decoder.JSONDecodeError as e:
			# This is hit when the data.json file is blank.
			outfile.write(json.dumps({ 'lastAccess': lastAccess }))
	print('Wrote last access time of {}'.format(lastAccess))
	
def retrieveUpdates():
	oldTime = lastAccess
	# Sub 10 seconds (likely too much) to account for possibility of missing messages that come in at the same time
	tempLastAccess = int(time.time()) - 10
	try:
		cmd = ["ssh {}@{} \"python {} {}\"".format(user, ip, retrieveScriptPath, lastAccess)]
		output = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, check=True)
		output = json.loads(output.stdout)
		for attachment in output['attachment']:
			# each attachment needs to be scp'ed over
			# this will be a bottleneck when starting up
			# Obviously using basename leads to squashing attachments with the same basename. This should be changed later.
			# I just didn't want to navigate a nest of folders while working on this.
			if attachment['filename']:
				if not os.path.isfile('./attachments/{}'.format(os.path.basename(attachment['filename']).replace(' ', '_'))):
					cmd = ["scp {}@{}:\"{}\" ./attachments/{}".format(user, ip, attachment['filename'].replace(' ', '\\ ').replace('(','\\(').replace(')','\\)'), os.path.basename(attachment['filename']).replace(' ', '_').replace('(','\\(').replace(')','\\)'))]
					subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL)
				attachment['filename'] = './attachments/{}'.format(os.path.basename(attachment['filename']).replace(' ', '_'))

		conn = sqlite3.connect('sms.db')

		for table in output:
			for row in output[table]:
				if row.keys():
					columns = ', '.join(row.keys())
					placeholders = ', '.join('?' * len(row))
					sql = 'INSERT OR REPLACE INTO {} ({}) VALUES ({})'.format(table, columns, placeholders)
					conn.execute(sql, tuple(row.values()))
		conn.commit()
		conn.close()
		updateLastAccess(tempLastAccess)
	except subprocess.CalledProcessError as e:
		print(e.stderr)
		print('Failed to connect via ssh...')

class UpdaterThread(threading.Thread):

	def __init__(self, name='UpdaterThread'):
		self._stopevent = threading.Event()
		threading.Thread.__init__(self, name=name)

	def run(self):
		readLastAccess()
		while not self._stopevent.isSet():
			retrieveUpdates()
			time.sleep(1)
		self.terminate()

	def terminate(self):
		writeLastAccess()

	def stopThread(self):
		self._stopevent.set()

if __name__ == '__main__':
	runUpdater()

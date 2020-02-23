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

lastAccess = 0

def retrieveUpdates():
	global lastAccess
	oldTime = lastAccess
	# Sub 10 seconds (likely too much) to account for possibility of missing messages that come in at the same time
	tempLastAccess = int(time.time()) - 10
	try:
		cmd = ["ssh {}@{} \"python {} {}\"".format(user, ip, retrieveScriptPath, lastAccess)]
		lastAccess = tempLastAccess
		output = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
		output = json.loads(output.stdout)

		for attachment in output['attachment']:
			# each attachment needs to be scp'ed over
			# this will be a bottleneck when starting up
			# Later, once lastAccess is tracked across sessions, this should be less of an issue
			# Obviously using basename leads to squashing attachments with the same basename. This should be changed later.
			# I just didn't want to navigate a nest of folders while working on this.
			if attachment['filename']:
				cmd = ["scp {}@{}:\"{}\" ./attachments/{}".format(user, ip, attachment['filename'].replace(' ', '\\ '), os.path.basename(attachment['filename']).replace(' ', '_'))]
				subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
	except subprocess.CalledProcessError as e:
		print(e.stderr)
		lastAccess = oldTime
		print('Failed to connect via ssh...')

def runUpdater():
	while True:
		retrieveUpdates()
		time.sleep(1)

if __name__ == '__main__':
	runUpdater()
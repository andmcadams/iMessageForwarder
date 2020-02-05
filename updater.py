import json
import subprocess
import time
import sqlite3


# Adding 10 so that there's a bit of a "buffer", messages will be received if they
# are under ten seconds old
UNIX_TIME_OFFSET = 978307200 + 10

secrets = json.load(open('secrets.json'))
ip = secrets['ip']
scriptPath = secrets['scriptPath']
retrieveScriptPath = secrets['retrieveScriptPath']

lastAccess = 0

def setAccessTime(t):
	global lastAccess
	lastAccess = t - UNIX_TIME_OFFSET

def retrieveUpdates():
	oldTime = lastAccess
	tempLastAccess = int(time.time())
	try:
		cmd = ["ssh root@{} \"python {} {}\"".format(ip, retrieveScriptPath, lastAccess)]
		setAccessTime(tempLastAccess)
		output = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
		output = json.loads(output.stdout)
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
		setAccessTime(lastAccess + UNIX_TIME_OFFSET)
		print('Failed to connect via ssh...')

def runUpdater():
	while True:
		retrieveUpdates()
		time.sleep(1)
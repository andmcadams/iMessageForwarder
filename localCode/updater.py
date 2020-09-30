import threading
import json
import time
import sqlite3
import os
import requests

dirname = os.path.dirname(__file__)
secretsFile = os.path.join(dirname, 'secrets.json')
secrets = json.load(open(secretsFile))

user = secrets['user']
ip = secrets['ip']
scriptPath = secrets['scriptPath']
retrieveScriptPath = secrets['retrieveScriptPath']
serverCrt = secrets['serverCrt']
clientCrt = secrets['clientCrt']
clientKey = secrets['clientKey']

def updateLastAccess(newTime):
    global lastAccess
    lastAccess = newTime


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
            outfile.write(json.dumps({'lastAccess': lastAccess}))
    print('Wrote last access time of {}'.format(lastAccess))


def translatePath(filename):
    (head, rightPath) = os.path.split(filename)
    rightFolder = os.path.basename(head).replace(' ', '_')
    rightPath = rightPath.replace(' ', '_')
    if rightFolder:
        rightPath = '{}/{}'.format(rightFolder, rightPath)
    return (rightFolder, rightPath)


def retrieveUpdates():
    oldTime = lastAccess
    # Sub 10 seconds (likely too much) to account for possibility of
    # missing messages that come in at the same time.
    tempLastAccess = int(time.time()) - 10
    try:
        resp = requests.get(
            'https://{}:3000/update'.format(ip),
            json={
                'last_update_time': lastAccess},
            verify=serverCrt, cert=(clientCrt, clientKey))
        output = resp.json()
        attachmentPre = './attachments/{}'
        for attachment in output['attachment']:
            if not attachment['filename']:
                continue
            (rightFolder, rightPath) = translatePath(attachment['filename'])
            if rightFolder:
                if not os.path.isdir(attachmentPre.format(rightFolder)):
                    os.mkdir(attachmentPre.format(rightFolder))
            if not os.path.isfile(attachmentPre.format(rightPath)):
                attachResp = requests.get('https://{}:3000/sent/attachment/{}'
                                          .format(ip, attachment['ROWID']),
                                          verify=serverCrt,
                                          cert=(clientCrt, clientKey))
                if attachResp .status_code == 200:
                    file = open(attachmentPre.format(rightPath), 'wb+')
                    file.write(attachResp.content)
                    file.close()
            attachment['filename'] = attachmentPre.format(rightPath)

        conn = sqlite3.connect('sms.db')

        for table in output:
            for row in output[table]:
                if row.keys():
                    columns = ', '.join(row.keys())
                    placeholders = ', '.join('?' * len(row))
                    sql = ('INSERT OR REPLACE INTO {} ({}) VALUES ({})'
                           .format(table, columns, placeholders))
                    conn.execute(sql, tuple(row.values()))
        conn.commit()
        conn.close()
        updateLastAccess(tempLastAccess)
    except requests.exceptions.ConnectionError as e:
        print('Failed to hit update endpoint...')
        pass


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

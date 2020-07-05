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


def escapeSpecialShell(pathname):
    return pathname.replace(' ', '\\ ').replace('(', '\\(').replace(')', '\\)')


def retrieveUpdates():
    oldTime = lastAccess
    # Sub 10 seconds (likely too much) to account for possibility of
    # missing messages that come in at the same time.
    tempLastAccess = int(time.time()) - 10
    try:
        cmd = ["ssh {}@{} \"python {} {}\"".format(user, ip,
                                                   retrieveScriptPath,
                                                   lastAccess)]
        output = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, check=True)
        output = json.loads(output.stdout)
        attachmentPre = './attachments/{}'
        for attachment in output['attachment']:
            if not attachment['filename']:
                continue
            (rightFolder, rightPath) = translatePath(attachment['filename'])
            if rightFolder:
                if not os.path.isdir(attachmentPre.format(rightFolder)):
                    os.mkdir(attachmentPre.format(rightFolder))
            if not os.path.isfile(attachmentPre.format(rightPath)):
                cmd = ["scp {}@{}:\"{}\" ./attachments/{}".format(user, ip,
                       escapeSpecialShell(attachment['filename']),
                       escapeSpecialShell(rightPath))]
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL)
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
    except subprocess.CalledProcessError as e:
        if e.returncode == -2:
            print('Updater ssh call interrupted by SIGINT...')
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

import Quartz
import pyautogui
import sqlite3
import time
import subprocess
import json
import os
import ast

dirname = os.path.dirname(__file__)
configFile = os.path.join(dirname, 'config.json')
config = json.load(open(configFile))
QUEUE_DB_PATH = config['queueLocation']
CHAT_DB_PATH = config['chatLocation']

typeDict = {
	2000: ['darkmode/dHeart.png', 'darkmode/aHeart.png'],
	2001: ['darkmode/dThumbUp.png', 'darkmode/aThumbUp.png'],
	2002: ['darkmode/dThumbDown.png', 'darkmode/aThumbDown.png'],
	2003: ['darkmode/dHaha.png', 'darkmode/aHaha.png'],
	2004: ['darkmode/dExclamation.png', 'darkmode/aExclamation.png'],
	2005: ['darkmode/dQuestion.png', 'darkmode/aQuestion.png']
}

isFromMeDict = {
	0: 582,
	1: (2560-40)
}

isGroupDict = {
	False: 0,
	True: 60
}

class NewMessageException(Exception):
	def __init__(self, message, messageId):

		# Call the base class constructor with the parameters it needs
		super(NewMessageException, self).__init__(message)

		# Now for your custom code...
		self.messageId = messageId

# It seems that Catalina doesn't like when clicks last for a very short amount of time
# These are really just pyautogui functions that I have added a "duration" to
def _sendMouseEvent(ev, x, y, button):
		mouseEvent = Quartz.CGEventCreateMouseEvent(None, ev, (x, y), button)
		Quartz.CGEventPost(Quartz.kCGHIDEventTap, mouseEvent)

def click(x, y, duration=0.5):
	x = int(x/2)
	y = int(y/2)
	_sendMouseEvent(Quartz.kCGEventLeftMouseDown, x, y, Quartz.kCGMouseButtonLeft)
	time.sleep(0.5)
	_sendMouseEvent(Quartz.kCGEventLeftMouseUp, x, y, Quartz.kCGMouseButtonLeft)

LEFT_CLICK = 0
RIGHT_CLICK = 1
def moveToAndClick(x, y, click=LEFT_CLICK, startDelay=0, endDelay=0):
	pyautogui.moveTo(x//2, y//2)
	time.sleep(startDelay)
	pyautogui.click() if click == LEFT_CLICK else pyautogui.rightClick()
	time.sleep(endDelay)

def getToChat(chatId):
	# Given the chatId, get either a list of recips or the group name
	conn = sqlite3.connect(CHAT_DB_PATH)
	cursor = conn.execute("select display_name from chat where ROWID = ?", (chatId, ))
	row = cursor.fetchone()
	groupName = ''
	if row:
		groupName = row[0]
	if groupName == '':
		cursor.execute("select id from handle inner join chat_handle_join on handle.ROWID = chat_handle_join.handle_id and chat_handle_join.chat_id = ?", (chatId, ))
		groupMembers = []
		for row in cursor.fetchall():
			groupMembers.append(row[0])
		groupName = ', '.join(groupMembers)
	newRecipients(groupName)

def makeNewChat(recipientString):
	groupName = ', '.join(ast.literal_eval(recipientString))
	newRecipients(groupName)

def newRecipients(groupName):
		# Create a new message
	loc = pyautogui.locateCenterOnScreen('darkmode/composeButton.png', confidence=0.98)
	if not loc:
		print('I couldn\'t find the compose button!')
		exit(1)

	click(loc[0], loc[1])

	# Make sure there are no recips
	loc = pyautogui.locateCenterOnScreen('darkmode/noRecips.png', confidence=0.90)
	if not loc:
		print('I couldn\'t find the No recipient label!')

		loc = pyautogui.locateCenterOnScreen('darkmode/toLabel.png', confidence=0.90)
		if not loc:
			print('I couldn\'t find the To label!')
			exit(1)

		click(loc[0]+20, loc[1])
		pyautogui.hotkey('command', 'a')
		pyautogui.press('backspace')
	else:
		click(loc[0], loc[1])

	# Add recips
	print('Writing groupName: {}'.format(groupName))
	pyautogui.write(groupName, interval=0.05)
	pyautogui.press('space')
	time.sleep(0.5)
	pyautogui.press('backspace')
	time.sleep(0.5)
	pyautogui.press('enter')
	time.sleep(0.1)
	pyautogui.press('enter')

def getXVal(isFromMe, isFromGroup):
	xVal = isFromMeDict[isFromMe]
	if isFromMe == 0:
		xVal += isGroupDict[isFromGroup]

	return xVal

def getLocationsToCheck(isFromMe, isFromGroup):
	xVal = getXVal(isFromMe, isFromGroup)

	im = pyautogui.screenshot('longStrip.png', region=(xVal, 100, 1, 1600-185))
	onRun = False
	pixels = []
	for i in range(im.height):
		r, g, b, _ = im.getpixel((0, i))
		if r != 31 or g != 41 or b != 39:
			if not onRun:
				pixels.append(i+185)
			onRun = True
		elif onRun:
			pixels[-1] = int((i+pixels[-1])/2)
			onRun = False
	pixels.reverse()
	return pixels

# This function only exists because python can't handle
# x, y = pyautogui.locateCenterOnScreen(filename, confidence=confidence)
# when the image can't be found onscreen.
def wrapLocateCenterOnScreen(filename, confidence=1.0):
	loc = pyautogui.locateCenterOnScreen(filename, confidence=confidence)
	if not loc:
		return None, None
	return loc[0], loc[1]


def checkText(p, xVal):
	moveToAndClick(xVal, p, click=RIGHT_CLICK, endDelay=1.5)
	x, y = wrapLocateCenterOnScreen('darkmode/copy.png', confidence=0.97)
	if x == None:
		return False

	moveToAndClick(x, y, click=LEFT_CLICK, startDelay=0.125, endDelay=1)

	output = subprocess.run("pbpaste", capture_output=True)
	if output.stdout.decode('UTF-8') != textToMatch:
		return False
	return True

def hitReact(p, xVal):
	moveToAndClick(xVal, p, click=RIGHT_CLICK, endDelay=1.5)

	x, y = wrapLocateCenterOnScreen('darkmode/tapback.png', confidence=0.97)
	if x == None:
		return False

	moveToAndClick(x, y, click=LEFT_CLICK, startDelay=0.125, endDelay=2)

	# It seems more likely that reacting is more common than "de-reacting", so check unactivated first.
	x, y = wrapLocateCenterOnScreen(typeDict[assocType][0], confidence=0.97)
	if x == None:
		x, y = wrapLocateCenterOnScreen(typeDict[assocType][1], confidence=0.97)
		if x == None:
			return False

	moveToAndClick(x, y, click=LEFT_CLICK, startDelay=0.125, endDelay=1)
	return True


# While running

# Poll queue for new messages

# If there is a new message
	# Check what kind of message it is
time.sleep(10)
conn = sqlite3.connect(QUEUE_DB_PATH)
while True:
	cursor = conn.execute('select * from outgoing')
	rows = cursor.fetchall()
	for row in rows:
		rowId, text, chatId, assocGUID, assocType, messageCode, recipientString = row
		if recipientString == '':
			getToChat(chatId)
		else:
			makeNewChat(recipientString)
		time.sleep(1.5)

		# Simple Text
		if messageCode == 0:
			print('Printing chatId: {}'.format(chatId))
			pyautogui.write(text, interval=0.0001)
			time.sleep(0.2)
			pyautogui.press('enter')
			cursor = conn.execute('delete from outgoing where ROWID = ?', (rowId, ))
			conn.commit()
			# Create a new message
			# Make sure there are no recips
			# Add recips
			# Hit enter (goes to message box)
			# Type message
			# Send message
		# Reaction
		def getIsGroup(chatId, conn):
			chatCursor = conn.execute('select style from chat where ROWID = ?', (chatId, ))
			style = chatCursor.fetchone()[0]
			return style == 43

		def lastMessageId(chatId, conn):
			chatCursor = conn.execute('select message_id, max(message_date) from chat_message_join where chat_id = ?', (chatId, ))
			newId, _ = chatCursor.fetchone()
			return newId

		def newMessage(lastId, chatId, conn):
			newId = lastMessageId(chatId, conn)
			if newId != lastId:
				raise NewMessageException('New Message Detected!', newId)

		if messageCode == 1:
			chatConn = sqlite3.connect(CHAT_DB_PATH)
			isFromGroup = getIsGroup(chatId, chatConn)

			chatCursor = chatConn.execute('select text, is_from_me from message where ROWID = ?', (assocGUID, ))
			r = chatCursor.fetchone()
			textToMatch = r[0]
			isFromMe = r[1]

			lastId = lastMessageId(chatId, chatConn)
			print(lastId)
			print('Looking for: {}'.format(textToMatch))
			lastPixels = []
			found = False
			while not found:
				pixels = getLocationsToCheck(isFromMe, isFromGroup)
				# This is obviously less than ideal
				if lastPixels == pixels:
					break
				try:
					for p in pixels:
						newMessage(lastId, chatId, chatConn)
						# Check to make sure there aren't any new messages in the chat.
						# If there are, we need to relocate the pixels
						if checkText(p, getXVal(isFromMe, isFromGroup)) == False:
							continue

						newMessage(lastId, chatId, chatConn)

						# Might want to make this a decorator
						attempts = 0
						while hitReact(p, getXVal(isFromMe, isFromGroup)) == False and attempts < 3:
							attempts += 1
							newMessage(lastId, chatId, chatConn)

						if attempts >= 3:
							break

						found = True
						cursor = conn.execute('delete from outgoing where ROWID = ?', (rowId, ))
						conn.commit()
						break
					if attempts >= 3:
						print('Uh oh!')
						tapoffXVal = getXVal(isFromMe, isFromGroup)
						tapoffXVal = tapoffXVal + 20 if isFromMe == 1 else tapoffXVal - 20
						moveToAndClick(tapoffXVal, p, click=LEFT_CLICK, startDelay=1, endDelay=1.5)
						lastPixels = pixels
						pyautogui.scroll(1)
						time.sleep(4)
						continue
					if found:
						break
					lastPixels = pixels
					pyautogui.scroll(17)
					time.sleep(4)
				# If a new message is received in this conversation, just go on to the next iteration.
				except NewMessageException as e:
					lastId = e.messageId
			# Search for message
			# Screenshot column of right side
			# Identify message locations

		# Group Add/Remove
	time.sleep(1)

-- STATE VALUES
-- These should be constant. Do not reassign values to these variables.
NOT_IN_MESSAGES = 1
CONVERSATION_LIST_STATE = 2
CONVERSATION_STATE = 3
COMPOSE_STATE = 4
-- End of consts

sqlite3 = require('lsqlite3')

function sleep(time)
	usleep(time*1000000)
end

function tap(x, y)
	touchDown(0, x, y)
	usleep(16000)
	touchUp(0, x, y)
end

local composeButtonLocation = {560, 58, 50, 50}
local backButtonLocation = {20, 60, 33, 48}
local cancelButtonLocation = {500, 65, 110, 35}
function findComposeButton()
	return findImage("images/compose.png", 1, 0.99, {558, 55, 55, 55})
end

function findBackButton()
	return findImage("images/back.png", 1, 0.99, {17, 57, 40, 55})
end

function findCancelButton()
	return findImage("images/cancel.png", 1, 0.99, {495, 60, 120, 45})
end

function determineState()
	local appId = frontMostAppId();
	if appId ~= "com.apple.MobileSMS" then
		-- alert("Not in messages")
		return 1
	end
	if #findComposeButton() ~= 0 then
		-- alert("In ConversationList")
		return 2
	elseif #findBackButton() ~= 0 then
		-- alert("In Conversation")
		return 3
	elseif #findCancelButton() ~= 0 then
		-- alert("In Compose")
		return 4
	end
	return 1
end

openMessages = function()
	appRun("com.apple.MobileSMS")
	sleep(2)
end

noop = function()

end

unimplemented = function()
	alert("This should never appear :)")
end

tapButton = function(location)
	if #location == 0 then
		alert("FUCK")
	else
		tap(location[1][1], location[1][2])
	end
end

tapComposeButton = function()
	tapButton(findComposeButton())
end

tapBackButton = function()
	tapButton(findBackButton())
end

tapCancelButton = function()
	tapButton(findCancelButton())
end

function getToState(n)
	local stateMap = {
		{noop, openMessages, openMessages, openMessages},
		{unimplemented, noop, unimplemented, tapComposeButton},
		{unimplemented, tapBackButton, noop, tapBackButton},
		{unimplemented, tapCancelButton, tapCancelButton, noop}}
	repeat
		local state = determineState()
		stateMap[state][n]()
		sleep(1)
	until determineState() == n
end

function openConversation(recipients, groupName)
	-- Tap on recipient list
	tap(141, 180)
	sleep(0.5)
	if groupName ~= "" then
		inputText(groupName)
		sleep(2)
		tap(129, 275)
		sleep(1.5)
	else
		for k, v in pairs(recipients) do
			inputText(v .. ",\n")
			tap(560, 1089)
			sleep(0.5)
		end
	end
end

function sendMessage(recipients, message, groupName)
	openConversation(recipients, groupName)
	-- Tap on message box
	sleep(1)
	tap(456, 662)
	sleep(1)
	inputText(message)
	-- Tap on send button
	sleep(2)
	tap(571, 662)
	sleep(2)
end

local db, err, errmsg = sqlite3.open("/var/mobile/Library/AutoTouch/Scripts/iMessageForwarder/msgQueue.db", sqlite3.OPEN_READWRITE)

while true do
	local flag = false
	for row in db:rows("select * from outgoing") do
		flag = true
	end
	if flag == true then
		local smsdb = sqlite3.open("/var/mobile/Library/SMS/sms.db")
		for row in db:rows("select * from outgoing") do

			id = row[1]
			text = row[2]
			chatId = row[3]
			recips = {}
			groupName = nil
			for displayNameRow in smsdb:rows("select display_name from chat where ROWID = " .. chatId) do
				groupName = displayNameRow[1]
			end

			for recipRow in smsdb:rows("select id from handle inner join chat_handle_join on handle.ROWID = chat_handle_join.handle_id and chat_handle_join.chat_id = " .. chatId) do
				table.insert(recips, recipRow[1])
			end

			getToState(CONVERSATION_LIST_STATE)

			getToState(COMPOSE_STATE)

			sendMessage(recips, text, groupName)

			getToState(CONVERSATION_LIST_STATE)

			err = db:exec("delete from outgoing where ROWID = " .. id)
			if err ~= 0 then
				alert(err)
				return
			end
		end
		smsdb:close()
	end
	sleep(1)
end

db:close()





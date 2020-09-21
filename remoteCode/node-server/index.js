const express = require('express')
const sqlite = require('sqlite3')
const bodyParser = require('body-parser')

const app = express()
const port = 3000

const dbPath = './testDb.db'

app.use(bodyParser.json())

// value - A string
// returns the integer represented by the string or a NaN if no such integer exists.
function parseId(value) {
	if (/^\d+$/.test(value))
		return parseInt(value)
	else
		return NaN
}

function handleBadId(res) {
	return res.status(400).send({
		error: '"chat_id" value must be an integer.'
	})
}

app.post('/message', (req, res) => {
  if (req.body.chat_id == null || req.body.text == null) {
	// Missing either of these means the request is malformed.
	return res.status(400).send({
		error: 'Missing "chat_id" or "text" keys in request body.'
	})
  }
  else {
	let chat_id = parseId(req.body.chat_id)
	let text = req.body.text
	if (isNaN(chat_id))
		return handleBadId(res)
	let db = new sqlite.Database(dbPath)
	db.run('INSERT INTO message (chat_id, text) VALUES (?, ?)', chat_id, text, function(err) {
		if (err == null) {
			res.set({'Location': '/message/' + this.lastID})
			return res.status(201).send({
				ROWID: this.lastID
			})
		}
		else {
			return res.status(400).send({
				error: err
			})
		}
	})
	db.close()
  }
})

app.post('/chat', (req, res) => {
  if (req.body.recipient_string == null || req.body.text == null) {
	// Missing either of these means the request is malformed.
	return res.status(400).send({
		error: 'Missing "recipient_string" or "text" keys in request body.'
	})
  }
  else {
	let recipient_string = req.body.recipient_string
	let text = req.body.text
	let db = new sqlite.Database(dbPath)
	db.run('INSERT INTO chat (recipient_string, text) VALUES (?, ?)', recipient_string, text, function(err) {
		if (err == null) {
			res.set({'Location': '/chat/' + this.lastID})
			return res.status(201).send({
				ROWID: this.lastID
			})
		}
		else {
			return res.status(400).send({
				error: err
			})
		}
	})
	db.close()
  }
})

app.post('/reaction', (req, res) => {
  if (req.body.chat_id == null || req.body.associated_guid == null || req.body.associated_type == null) {
	// Missing any of these means the request is malformed.
	return res.status(400).send({
		error: 'Missing "chat_id", "associated_guid", or "associated_type" keys in request body.'
	})
  }
  else {
	let chat_id = parseId(req.body.chat_id)
	let associated_guid = req.body.associated_guid
	let associated_type = req.body.associated_type
	if (isNaN(chat_id))
		return handleBadId(res)
	let db = new sqlite.Database(dbPath)
	db.run('INSERT INTO reaction (chat_id, associated_guid, associated_type) VALUES (?, ?, ?)', chat_id, associated_guid, associated_type, function(err) {
		if (err == null) {
			res.set({'Location': '/reaction/' + this.lastID})
			return res.status(201).send({
				ROWID: this.lastID
			})
		}
		else {
			res.statusCode = 400
			return res.send({
				error: err
			})
		}
	})
	db.close()
  }
})

app.post('/rename', (req, res) => {
  if (req.body.chat_id == null || req.body.group_title == null) {
	// Missing either of these means the request is malformed.
	return res.status(400).send({
		error: 'Missing "chat_id" or "group_title" keys in request body.'
	})
  }
  else {
	let chat_id = parseId(req.body.chat_id)
	let group_title = req.body.group_title
	if (isNaN(chat_id))
		return handleBadId(res)
	let db = new sqlite.Database(dbPath)
	db.run('INSERT INTO rename (chat_id, group_title) VALUES (?, ?)', chat_id, group_title, function(err) {
		if (err == null) {
			res.set({'Location': '/rename/' + this.lastID})
			return res.status(201).send({
				ROWID: this.lastID
			})
		}
		else {
			res.statusCode = 400
			return res.send({
				error: err
			})
		}
	})
	db.close()
  }
})

app.get('/:table/:id', (req, res) => {
  var table = req.params.table
  var id = parseId(req.params.id)
  if (isNaN(id))
	return res.status(400).send({
		error: '"ROWID" value must be an integer.'
	})

  if (table === 'message' || table === 'chat' || table === 'reaction' || table === 'rename') {
	  let db = new sqlite.Database(dbPath)
	  // Note that table name cannot use parameterization.
	  db.get('SELECT * FROM ' + table + ' WHERE ROWID = ?', id, function(err, row) {
		if (err == null) {
			hasSent = row == null
			return res.send({
				sent: hasSent,
				row: row
			})
		}
		else
			return res.status(400).send({
				error: err
			})
	  })
	  db.close()
  }
  else
	res.status(400).send({
		error: 'Table must be one of {message, chat, reaction, rename}.'
	})
})

app.get('/ping', (req, res) => {
	return res.status(200).send({
		name: 'iMessageForwarder'
	})
})

app.post('/attachment', (req, res) => {
  res.send('Not implemented')
})

app.get('/all', (req, res) => {
  res.send('Not implemented')
})

app.listen(port, () => {
  console.log(`Example app listening at http://localhost:${port}`)
})

const express = require('express')
const sqlite = require('sqlite3')
const bodyParser = require('body-parser')

const app = express()
const port = 3000

const dbPath = './testDb.db'

app.use(bodyParser.json())

app.get('/', (req, res) => {
  res.send('Hello World!')
})

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
		status: 400,
		error: '"chat_id" value must be an integer.'
	})
}

app.post('/message', (req, res) => {
  if (req.body.chat_id == null || req.body.text == null) {
	// Missing either of these means the request is malformed.
	return res.status(400).send({
		status: 400,
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
		if (err == null)
			return res.send({
				status: 200,
				ROWID: this.lastID
			})
		else
			return res.send({
				status: 400,
				error: err
			})
	})
	db.close()
  }
})

app.post('/reaction', (req, res) => {
  if (req.body.chat_id == null || req.body.associated_guid == null || req.body.associated_type == null) {
	// Missing either of these means the request is malformed.
	return res.status(400).send({
		status: 400,
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
		if (err == null)
			return res.send({
				status: 200,
				ROWID: this.lastID
			})
		else
			return res.send({
				status: 400,
				error: err
			})
	})
	db.close()
  }
})

app.post('/rename', (req, res) => {
  res.send('Hello World!')
})

app.post('/attachment', (req, res) => {
  res.send('Hello World!')
})

app.get('/all', (req, res) => {
  res.send('Hello World!')
})

app.listen(port, () => {
  console.log(`Example app listening at http://localhost:${port}`)
})

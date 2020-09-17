const express = require('express')
const sqlite = require('sqlite3')
const bodyParser = require('body-parser')

const app = express()
const port = 3000

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

app.post('/message', (req, res) => {
  if (req.body.chat_id == null || req.body.text == null)
	// Missing either of these means the request is malformed.
	return res.status(400).send({
		status: 400,
		error: 'Missing "chat_id" or "text" keys in request body.'
	})
  else
	var chat_id = parseId(req.body.chat_id)
	var text = req.body.text
	if (isNaN(chat_id))
		return res.status(400).send({
			status: 400,
			error: '"chat_id" value must be an integer.'
		})
	var db = new sqlite.Database('./testDb.db')
	db.run('INSERT INTO message (chat_id, text) VALUES (?, ?)', chat_id, text)
	db.close()
    return res.send({
		status: 200,
	})
})

app.post('/reaction', (req, res) => {
  res.send('Hello World!')
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

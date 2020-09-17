const express = require('express')
const sqlite = require('sqlite3')
const bodyParser = require('body-parser')

const app = express()
const port = 3000

app.use(bodyParser.json())

app.get('/', (req, res) => {
  res.send('Hello World!')
})

app.post('/message', (req, res) => {
  var chat_id = req.body.chat_id
  var text = req.body.text
  if (chat_id == null || text == null)
	// Missing either of these means the request is malformed.
	res.send(req.body)
  else
	var db = new sqlite.Database('./testDb.db')
	db.run('INSERT INTO message (chat_id, text) VALUES (1, "This is sample text")')
	db.close()
    res.send(req.body.text)
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

const sqlite = require('sqlite3')
const express = require('express')
// Add message, chat, reaction, and rename ops to queue
// Should be https and require auth

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

function protectedEndpoints(dbPath, rootPath) {
	var router = express.Router();
	router.post('/message', (req, res) => {
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
				res.set({'Location': rootPath + 'message/' + this.lastID})
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

	router.post('/chat', (req, res) => {
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
				res.set({'Location': rootPath + 'chat/' + this.lastID})
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

	router.post('/reaction', (req, res) => {
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
				res.set({'Location': rootPath + 'reaction/' + this.lastID})
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

	router.post('/rename', (req, res) => {
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
				res.set({'Location': rootPath + 'rename/' + this.lastID})
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
	return router;
}

// Check table :table for ROWID :id and send back false if still in queue, true otherwise
// No need for https or auth, queue objects cannot be identified by sent or not
function unprotectedEndpoints(dbPath, sendRow) {
	var router = express.Router()
	router.get('/:table/:id', (req, res) => {
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
				// Only send row info if toggled on
				if (sendRow == false)
					row = null
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
	return router;
}

module.exports.protectedEndpoints = protectedEndpoints;
module.exports.unprotectedEndpoints = unprotectedEndpoints;
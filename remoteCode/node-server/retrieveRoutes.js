const sqlite = require('sqlite3')
const express = require('express')
const spawn = require("child_process").spawn;
const path = require('path');

function parseId(value) {
	if (/^\d+$/.test(value))
		return parseInt(value)
	else
		return NaN
}

function handleBadId(res) {
	return res.status(400).send({
		error: '"ROWID" value must be an integer.'
	})
}

function protectedEndpoints(messageDbPath) {
	router = express.Router();

	router.get('/update', (req, res) => {
		var last_update_time = req.body.last_update_time
		if (last_update_time == null)
			last_update_time = 0
	  const pythonProcess = spawn('python', ["./getMessages.py", last_update_time]);
	  pythonProcess.stdout.on('data', (data) => {
	      res.write(data);
	  });
	  pythonProcess.stdout.on('end', () => {
	  	res.end()
	  })
	})

	router.get('/file/:id', (req, res) => {
		var rowId = parseId(req.params.id)
		if (isNaN(rowId))
			return handleBadId(res)

		let db = new sqlite.Database(messageDbPath)
		db.get('SELECT filename FROM attachment WHERE ROWID = ?', rowId, function(err, row) {
			if (err == null) {
				if (row == null) {
					return res.status(400).send({
						error: 'No file could be found for ROWID ' + rowId
					})
				}
				else {
					filename = row.filename
					if (filename[0] === '~')
						filename = path.join(process.env.HOME, filename.slice(1));
					res.sendFile(filename, (err) => {
						if (err)
							return res.status(400).send({
								error: err
							})
					})
				}
			}
			else
				return res.status(400).send({
					error: err
				})
		  })
		  db.close()
	})

	router.get('/:table/:id', (req, res) => {
	  var table = req.params.table
	  var rowId = parseId(req.params.id)
	  if (isNaN(rowId))
			return handleBadId(res)

	  if (table === 'message' || table === 'chat' || table === 'attachment') {
			let db = new sqlite.Database(messageDbPath)
			db.get('SELECT * FROM ' + table + ' WHERE ROWID = ?', rowId, function(err, row) {
				if (err == null) {
					hasSent = row == null
					return res.send({
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
				error: 'Table must be one of {message, chat, attachment}.'
			})
	})

	return router;
}

module.exports.protectedEndpoints = protectedEndpoints;
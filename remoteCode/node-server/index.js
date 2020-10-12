const express = require('express')
const sqlite = require('sqlite3')
const bodyParser = require('body-parser')
const http = require('http');
const https = require('https');
const fs = require('fs');
const queueRoutes = require('./queueRoutes');
const retrieveRoutes = require('./retrieveRoutes');
require('dotenv').config();

const QUEUE_PATH = process.env.QUEUE_PATH
const CHAT_PATH = process.env.CHAT_PATH
const IMF_HTTP_PORT = process.env.IMF_HTTP_PORT || 3000
const IMF_HTTPS_PORT = process.env.IMF_HTTPS_PORT || 3001

if (QUEUE_PATH == null || CHAT_PATH == null) {
	console.log('Missing required environment variables! Check .env for proper usage.')
	console.log(`QUEUE_PATH=${QUEUE_PATH}`)
	console.log(`CHAT_PATH=${CHAT_PATH}`)
	process.exit(1)
}

// HTTP App definition
const httpApp = express()
httpApp.use(bodyParser.json())
httpApp.use('/queue', queueRoutes.unprotectedEndpoints(QUEUE_PATH, false))
httpApp.get('/ping', (req, res) => {
	return res.status(200).send({
		name: 'iMessageForwarder'
	})
})

// HTTPS App definition
const httpsApp = express()
httpsApp.use(bodyParser.json())
httpsApp.use('/queue', queueRoutes.protectedEndpoints(QUEUE_PATH, '/queue/'))
httpsApp.use('/queue', queueRoutes.unprotectedEndpoints(QUEUE_PATH, true))
httpsApp.use('/retrieve', retrieveRoutes.protectedEndpoints(CHAT_PATH))
httpsApp.get('/ping', (req, res) => {
	return res.status(200).send({
		name: 'iMessageForwarder'
	})
})

var key = fs.readFileSync('./server.key', 'utf8')
var cert = fs.readFileSync('./server.crt', 'utf8')
var credentials = {
	key: key,
	cert: cert,
	requestCert: true,
	rejectUnauthorized: true,
	ca: [cert]
}

var httpServer = http.createServer(httpApp);
httpServer.listen(IMF_HTTP_PORT, () => {
  console.log(`iMessageForwarder listening at http://localhost:${IMF_HTTP_PORT}`)
  console.log(`Path to queue:${QUEUE_PATH}`)
  console.log(`Path to message database:${CHAT_PATH}`)
})

var httpsServer = https.createServer(credentials, httpsApp);
httpsServer.listen(IMF_HTTPS_PORT, () => {
  console.log(`iMessageForwarder listening at https://localhost:${IMF_HTTPS_PORT}`)
  console.log(`Path to queue:${QUEUE_PATH}`)
  console.log(`Path to message database:${CHAT_PATH}`)
})

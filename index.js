var express = require('express');
var app = express();
app.use(express.bodyParser());
var fs = require('fs');
var child_process = require('child_process');

var util = require('util');
var log_file = fs.createWriteStream(__dirname + '/html/debug.log', {flags : 'w'});
var log_stdout = process.stdout;
var portNumber = 3000;

app.use(express.static('html')); // serve static files from html directory

console.log = function(d) { // for logging purposes, copy output to file
  log_file.write(util.format(d) + '\n');
  log_stdout.write(util.format(d) + '\n');
};

app.get('/render', function(req, res) {
  console.log('GET request on /render');
  return res.json({'message':'No GET on /render','error':true});
});

app.post('/render', function (req, res) { /* Receives the renderer information */
  console.log('POST request on /render');
  var json = req.accepts('json');
  var error = 0;
  if (!json) { error = 'Received non-json request'; }
  else if (!req.body.hasOwnProperty('render')) { error = "Missing property: render"; }
  else if (!req.body.hasOwnProperty('id')) { error = "Missing property: id"; }
  if (error != 0) {
    console.log('ERROR: '+error);
    return res.json({'message':error,'error':true});
  }
  
  console.log('server: '+req.connection.localAddress);
  console.log(req.body.id+': submitting image render');
  render = child_process.spawn('/usr/bin/python27',['raytrace.py',req.body.render]);
  render.stderr.on( 'data', function(data) {
    var s = data.toString();
    if (s.substring(0,4) === 'URL:') {
      url = s.substring(4,s.length)
      res.json({'id':req.body.id,'error':false,'url':url,'server':req.connection.localAddress});
      res.end();
    }
    else console.log('stderr: ' + s); 
  });
  render.on('close',function(data) { 
    console.log(req.body.id+': completed '+req.body.id); 
    if (!res.finished) { 
      // something went wrong..
      res.json({'id':req.body.id,'error':true,'server':req.connection.localAddress});
      res.end();
    }
  });
});

/* bind and listen for connections */
var server = app.listen(portNumber, function() {
  console.log('(Server running) ====== '+new Date().toGMTString()+' ======');
});
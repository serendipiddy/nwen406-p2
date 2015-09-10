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

testImage = {
  'id': 'test_clientSend',
  'ambient': 0.1,
  'gammaCorrection': 1/2.2,
  'dim_x': 500,
  'dim_y': 500,
  'lightSource': {'x':-10,'y':0,'z':0},
  'cameraPos': {'x':0,'y':0,'z':20},
  'objects': [
    { 'type':'sphere',
      'center': {'x':-2,'y':0,'z':-10},
      'radius': 2.0,
      'colour': {'x':0,'y':255,'z':0}
    },
    { 'type':'sphere',
      'center': {'x':2,'y':0,'z':-10},
      'radius': 2.5,
      'colour': {'x':255,'y':0,'z':0}
    },
    { 'type':'sphere',
      'center': {'x':0,'y':-4,'z':-10},
      'radius': 3.0,
      'colour': {'x':0,'y':0,'z':255}
    },
    { 'type':'plane',
      'point': {'x':0,'y':0,'z':-12},
      'normal': {'x':0,'y':0,'z':1},
      'colour': {'x':255,'y':255,'z':255}
    }
  ],
}

console.log = function(d) { //
  log_file.write(util.format(d) + '\n');
  log_stdout.write(util.format(d) + '\n');
};

app.get('/render', function (req, res) { /* Checks whether a rendered image with the given ID exists */
  console.log('GET request on /render');
  error = 0;
  var json = req.accepts('json');
  if (!json) { error = 'Received non-json request'; }
  else if (!req.body.hasOwnProperty('imageid')) { error = "Missing property: imageid"; }
  if (error != 0) {
    console.log('ERROR: '+error);
    console.log(req);
    return res.json({'message':error,'error':true});
  }
  
  // check file exists
  stats = fs.lstatSync('./html/render/'+imageid+'.png');
  if (stats.isFile()) { return res.json({'exists':true,'error':false}); }
  else { return res.json({'exists':false,'error':false}); }
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
  
  console.log(req.body.id+': submitting image render');
  // render = child_process.spawn('/usr/bin/python27',['raytrace.py',JSON.stringify(testImage)]);
  render = child_process.spawn('/usr/bin/python27',['raytrace.py',req.body.render]);
  render.stderr.on( 'data', function(data) {
    var s = data.toString();
    if (s.substring(0,4) === 'URL:') {
      url = s.substring(4,s.length)
      res.json({'id':req.body.id,'error':false,'url':url});
      res.end();
    }
    else console.log('stderr: ' + s); 
  });
  render.on('close',function(data) { 
    console.log(req.body.id+': completed '+req.body.id); 
    if (!res.finished) { // something went wrong..
      res.json({'id':req.body.id,'error':true});
      res.end();
    }
  });
});

/* bind and listen for connections */
var server = app.listen(portNumber, function() {
  console.log('(Server running) ====== '+new Date().toGMTString()+' ======');
});
#
# Adapted from from http://randyheiland.com/raytrace/
#

from math import sqrt, pow, pi
import Image   # 3rd party module, not part of the Python standard library (try: "easy_install pil")
import sys, json, math, logging
from datetime import datetime

import boto
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import cStringIO

# conn = S3Connection()

# # new object, need new key, unique to the bucket
# k = Key(bucket)
# k.key = 'foobar'
# k.set_contents_from_string('test')

# # steps
# c = boto.connect_s3()
# b = c.get_bucket('nwen406-iddy-projectrender')
# k = Key(b)
# k.key = 'foobar'
# k.get_contents_as_string()
# k.get_contents_from_filename('bar.jpg')

# # check if exists
# b.get_key('mykey')
# b.get_key('mykey', validate=False) # no check



logging.basicConfig(filename='render.log',level=logging.INFO)

# Perhaps this is not the best named class; it really serves as just a 3-tuple most of the time. A mathematical
# vector would have a magnitude and direction. These are implicit by specifying a (x,y,z) 3-tuple (assumes relative
# to the origin (0,0,0).
class Vector( object ):
  def __init__(self,x,y,z):
    self.x = x
    self.y = y
    self.z = z

  def dot(self, b):  # vector dot product
    return self.x*b.x + self.y*b.y + self.z*b.z

  def cross(self, b):  # vector cross product
    return (self.y*b.z-self.z*b.y, self.z*b.x-self.x*b.z, self.x*b.y-self.y*b.x)

  def magnitude(self): # vector magnitude
    return sqrt(self.x**2+self.y**2+self.z**2)

  def normal(self): # compute a normalized (unit length) vector
    mag = self.magnitude()
    return Vector(self.x/mag,self.y/mag,self.z/mag)

        # Provide "overridden methods via the "__operation__" notation; allows you to do, for example, a+b, a-b, a*b
  def __add__(self, b):  # add another vector (b) to a given vector (self)
    return Vector(self.x + b.x, self.y+b.y, self.z+b.z)

  def __sub__(self, b):  # subtract another vector (b) from a given vector (self)
    return Vector(self.x-b.x, self.y-b.y, self.z-b.z)

  def __mul__(self, b):  # scalar multiplication of a given vector
    assert type(b) == float or type(b) == int
    return Vector(self.x*b, self.y*b, self.z*b)

class Sphere( object ):
  def __init__(self, center, radius, color):
    self.c = center
    self.r = radius
    self.col = color

  def intersection(self, l):
    q = l.d.dot(l.o - self.c)**2 - (l.o - self.c).dot(l.o - self.c) + self.r**2
    if q < 0:
      return Intersection( Vector(0,0,0), -1, Vector(0,0,0), self)
    else:
      d = -l.d.dot(l.o - self.c)
      d1 = d - sqrt(q)
      d2 = d + sqrt(q)
      if 0 < d1 and ( d1 < d2 or d2 < 0):
        return Intersection(l.o+l.d*d1, d1, self.normal(l.o+l.d*d1), self)
      elif 0 < d2 and ( d2 < d1 or d1 < 0):
        return Intersection(l.o+l.d*d2, d2, self.normal(l.o+l.d*d2), self)
      else:
        return Intersection( Vector(0,0,0), -1, Vector(0,0,0), self)

  def normal(self, b):
    return (b - self.c).normal()

class Plane( object ):
  def __init__(self, point, normal, color):
    self.n = normal
    self.p = point
    self.col = color

  def intersection(self, l):
    d = l.d.dot(self.n)
    if d == 0:
      return Intersection( vector(0,0,0), -1, vector(0,0,0), self)
    else:
      d = (self.p - l.o).dot(self.n) / d
      return Intersection(l.o+l.d*d, d, self.n, self)

class Ray( object ):
  def __init__(self, origin, direction):
    self.o = origin
    self.d = direction

class Intersection( object ):
  def __init__(self, point, distance, normal, obj):
    self.p = point
    self.d = distance
    self.n = normal
    self.obj = obj

def testRay(ray, objects, ignore=None):
  intersect = Intersection( Vector(0,0,0), -1, Vector(0,0,0), None)

  for obj in objects:
    if obj is not ignore:
      currentIntersect = obj.intersection(ray)
      if currentIntersect.d > 0 and intersect.d < 0:
        intersect = currentIntersect
      elif 0 < currentIntersect.d < intersect.d:
        intersect = currentIntersect
  return intersect

def trace(ray, objects, light, maxRecur):
  if maxRecur < 0:
    return (0,0,0)
  intersect = testRay(ray, objects)
  if intersect.d == -1:
    col = vector(AMBIENT,AMBIENT,AMBIENT)
  elif intersect.n.dot(light - intersect.p) < 0:
    col = intersect.obj.col * AMBIENT
  else:
    lightRay = Ray(intersect.p, (light-intersect.p).normal())
    if testRay(lightRay, objects, intersect.obj).d == -1:
      lightIntensity = 1000.0/(4*pi*(light-intersect.p).magnitude()**2)
      col = intersect.obj.col * max(intersect.n.normal().dot((light - intersect.p).normal()*lightIntensity), AMBIENT)
    else:
      col = intersect.obj.col * AMBIENT
  return col

def gammaCorrection(color,factor):
  return (int(pow(color.x/255.0,factor)*255),
      int(pow(color.y/255.0,factor)*255),
      int(pow(color.z/255.0,factor)*255))

AMBIENT = 0.1
GAMMA_CORRECTION = 1/2.2

def main():
  print('Beginning test render')
  objs = []   # create an empty Python "list"
  # Put 4 objects into the list: 3 spheres and a plane (rf. class __init__ methods for parameters)
  objs.append(Sphere( Vector(-2,0,-10), 2.0, Vector(0,255,0)))   # center, radius, color(=RGB)
  objs.append(Sphere( Vector(2,0,-10),  3.5, Vector(255,0,0)))
  objs.append(Sphere( Vector(0,-4,-10), 3.0, Vector(0,0,255)))
  objs.append(Plane( Vector(0,0,-12), Vector(0,0,1), Vector(255,255,255)))  # normal, point, color

  lightSource = Vector(-10,0,0)  # experiment with a different (x,y,z) light position

  img = Image.new("RGB",(400,400))
  cameraPos = Vector(0,0,20)
  for x in range(400):  # loop over all x values for our image
    sys.stdout.write('Render progress: %d%%    \r' % math.floor(100* x/400))
    sys.stdout.flush();
    for y in range(400):  # loop over all y values
      ray = Ray( cameraPos, (Vector(x/50.0-5,y/50.0-5,0)-cameraPos).normal())
      col = trace(ray, objs, lightSource, 10)
      img.putpixel((x,399-y),gammaCorrection(col,GAMMA_CORRECTION))
  
  # img.save("html/render/trace00.png","PNG")  # save the image as a .png (or "BMP", but it produces a much larger file)
  url = save_to_s3(img, 'trace00')
  print (url)
  
def save_to_s3(image, name):
  out_img = cStringIO.StringIO()
  image.save(out_img, "PNG")
  
  conn = boto.connect_s3()
  b = conn.get_bucket('nwen406-iddy-projectrender')
  
  k = b.new_key('renders/%s.png' % name)
  k.set_contents_from_string(out_img.getvalue())
  url = k.generate_url(expires_in=300, force_http=True)
  return(url)
  
  

def nodejs(arg):
  AMBIENT = arg['ambient']
  GAMMA = arg['gammaCorrection']
  CAMERA = Vector(arg['cameraPos']['x'],arg['cameraPos']['y'],arg['cameraPos']['z'])
  SOURCE = Vector(arg['lightSource']['x'],arg['lightSource']['y'],arg['lightSource']['z'])
  
  # populate with objects
  objs = []
  for o in arg['objects']:
    if o['type'] == 'plane':
      objs.append(
        Plane(Vector(o['point']['x'], o['point']['y'], o['point']['z']),  
              Vector(o['normal']['x'],o['normal']['y'],o['normal']['z']), 
              Vector(o['colour']['x'],o['colour']['y'],o['colour']['z']))
      )
    elif o['type'] == 'sphere':
      objs.append(
        Sphere(Vector(o['center']['x'],o['center']['y'],o['center']['z']),  
              o['radius'], 
              Vector(o['colour']['x'],o['colour']['y'],o['colour']['z']))
      )
  
  
  # Create image
  img = Image.new("RGB",(arg['dim_x'],arg['dim_y']))
  logging.info('Render progress: BEGIN    -- %s -- %s -- %d objects ' % (arg['id'],datetime.today(),len(objs)))
  for x in range(arg['dim_x']):
    # http://stackoverflow.com/q/517127 \r then flush
    sys.stdout.write('Render progress: %d%%    \r' % math.floor(100* x/arg['dim_x']))
    sys.stdout.flush();
    for y in range(arg['dim_y']):
      ray = Ray( CAMERA, (Vector(x/50.0-5,y/50.0-5,0)-CAMERA).normal())
      col = trace(ray, objs, SOURCE, 10)
      img.putpixel((x, arg['dim_y']-1-y),gammaCorrection(col,GAMMA))
      
  logging.info('Render progress: COMPLETE -- %s -- %s' % (arg['id'],datetime.today()))
  print('Render progress: COMPLETE -- %s -- %s' % (arg['id'],datetime.today()))
  url = save_to_s3(img, arg['id'])
  sys.stderr.write('URL:'+url)
  sys.stderr.flush()
  logging.info('Render -- %s' % url)
  # img.save("html/render/%s.png" % (arg['id']),"PNG")

if __name__ == '__main__':
  if (len(sys.argv) == 1):
    logging.info('launching main')
    main()
  elif (len(sys.argv) >= 2):
    logging.info('launching nodejs version')
    j = json.loads(sys.argv[1])
    nodejs(j)
  else:
    logging.info("Requires JSON object as argument")
    print("Requires JSON object as argument")

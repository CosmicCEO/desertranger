import sys
from PIL import Image
im=Image.open('orig.jpg'); s=4913/1024
name,x0,y0,x1,y1=sys.argv[1],*map(float,sys.argv[2:6])
rot=int(sys.argv[6]) if len(sys.argv)>6 else 0
c=im.crop(tuple(int(v*s) for v in (x0,y0,x1,y1)))
if rot: c=c.rotate(rot,expand=True)
c.thumbnail((1400,1400)); c.save(f'crops/{name}.jpg',quality=88)

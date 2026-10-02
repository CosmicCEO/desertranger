import cv2, numpy as np
g2=np.load('/tmp/g2.npy'); ch=np.load('/tmp/chroma.npy')
tr=np.load('/tmp/track.npy').astype(np.uint8); H,W=tr.shape
weak=((g2<0.72)&(ch<16)).astype(np.uint8)
# crease removal in band
x0,x1=1740,1900
b=weak[:,x0:x1]
vert=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(1,35)))
wide=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(11,1)))
cr=cv2.dilate(vert&(1-wide),np.ones((5,5),np.uint8))
weak[:,x0:x1]=b&(1-cr)
weakt=cv2.morphologyEx(weak,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
seed=weakt|tr
n,l,st,_=cv2.connectedComponentsWithStats(seed,connectivity=8)
ids=np.unique(l[tr>0]); keep=np.zeros(n,bool); keep[ids]=True; keep[0]=False
t2=keep[l].astype(np.uint8)
# erase doodle remnants (x0,y0,x1,y1) at 3000px scale
ER=[(2040,1240,2160,1440),(2900,1500,2990,1660),(1600,1080,1680,1180),(1880,1060,1960,1180),
    (2690,40,2900,240),(2880,180,2990,330)]
for a,b_,c,d in ER: t2[b_:d,a:c]=0
np.save('/tmp/track2.npy',t2.astype(bool))
n=np.load('/tmp/norm.npy'); v=(n*0.6+150).clip(0,255).astype(np.uint8); v[t2>0]=(0,0,255)
for i,(y,x) in enumerate([(0,0),(0,1500),(1140,0),(1140,1500)]):
    c=v[y:y+1140,x:x+1500].copy()
    for gx in range(0,1500,100): cv2.line(c,(gx,0),(gx,1139),(255,200,0),1); cv2.putText(c,str(x+gx),(gx+2,20),0,0.6,(255,0,0),2)
    for gy in range(0,1140,100): cv2.line(c,(0,gy),(1499,gy),(255,200,0),1); cv2.putText(c,str(y+gy),(2,gy+20),0,0.6,(255,0,0),2)
    cv2.imwrite('/tmp/ov%d.jpg'%i,c)

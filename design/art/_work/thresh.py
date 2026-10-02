import cv2, numpy as np, sys
LO=float(sys.argv[1]); HI=float(sys.argv[2]); MINA=int(sys.argv[3])
ink=np.load('/tmp/ink.npy'); H,W=ink.shape
weak=(ink>LO).astype(np.uint8); strong=(ink>HI).astype(np.uint8)
n,lbl,st,_=cv2.connectedComponentsWithStats(weak,connectivity=8)
keep=np.zeros(n,bool); keep[np.unique(lbl[strong>0])]=True; keep[0]=False
# despeckle by area
keep&=st[:,4]>=MINA
m=keep[lbl]
# crease suppression: in band around crease, remove components that are tall, thin, near-vertical
cx=int(W*float(sys.argv[4])) if len(sys.argv)>4 else None
mu=m.astype(np.uint8)
if cx:
    band=slice(cx-60,cx+60)
    n2,l2,s2,_=cv2.connectedComponentsWithStats(mu,connectivity=8)
    for i in range(1,n2):
        x,y,w,h,a=s2[i]
        if x>=cx-60 and x+w<=cx+60 and h>2.5*w and a<h*12: mu[l2==i]=0
m=mu>0
out=np.where(m,0,255).astype(np.uint8)
out=cv2.medianBlur(out,3)
cv2.imwrite('board-lineart.png',out)
cv2.imwrite('/tmp/la_crop.png',out[1100:1900,1400:2200])
cv2.imwrite('/tmp/la_crop2.png',out[0:800,0:800])
cv2.imwrite('/tmp/la_s.png',cv2.resize(out,(1200,int(1200*H/W)),interpolation=cv2.INTER_AREA))

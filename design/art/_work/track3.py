import cv2, numpy as np
g2=np.load('/tmp/g2.npy'); ch=np.load('/tmp/chroma.npy')
tr=np.load('/tmp/track.npy').astype(np.uint8); H,W=tr.shape
weak=((g2<0.72)&(ch<16)).astype(np.uint8)
x0,x1=1740,1900
b=weak[:,x0:x1]
vert=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(1,35)))
wide=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(11,1)))
cr=cv2.dilate(vert&(1-wide),np.ones((5,5),np.uint8))
weak[:,x0:x1]=b&(1-cr)
weakt=cv2.morphologyEx(weak,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
add=weakt&(1-cv2.dilate(tr,np.ones((3,3),np.uint8)))
n,l,st,_=cv2.connectedComponentsWithStats(add,connectivity=8)
trd=cv2.dilate(tr,np.ones((7,7),np.uint8))
acc=np.zeros_like(tr)
for i in range(1,n):
    x,y,w,h,a=st[i]
    if a<150: continue
    comp=(l[y:y+h,x:x+w]==i).astype(np.uint8)
    # must touch track
    if not (comp&trd[y:y+h,x:x+w]).any(): continue
    pts=cv2.findNonZero(comp); (cx,cy),(rw,rh),ang=cv2.minAreaRect(pts)
    L,Wd=max(rw,rh),max(1,min(rw,rh))
    fill=a/(L*Wd)
    if L/Wd>5 and Wd<22: acc[y:y+h,x:x+w]|=comp
t2=tr|acc
np.save('/tmp/track3.npy',t2.astype(bool)); np.save('/tmp/acc.npy',acc.astype(bool))
n_=np.load('/tmp/norm.npy'); v=(n_*0.6+150).clip(0,255).astype(np.uint8); v[tr>0]=(0,0,255); v[acc>0]=(255,0,0)
cv2.imwrite('/tmp/ovall.jpg',cv2.resize(v,(1500,int(1500*H/W)),interpolation=cv2.INTER_AREA))

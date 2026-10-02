import cv2, numpy as np
black=np.load('/tmp/black.npy').astype(np.uint8); H,W=black.shape
color=np.load('/tmp/color.npy').astype(np.uint8)
# crease removal: long vertical thin runs in band
x0,x1=1740,1900
band=black[:,x0:x1].copy()
vert=cv2.morphologyEx(band,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(1,45)))
# keep only thin ones: things that are also not wide horizontally
wide=cv2.morphologyEx(band,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(9,1)))
crease=vert&(1-wide)
crease=cv2.dilate(crease,np.ones((3,3),np.uint8))&band
black2=black.copy(); black2[:,x0:x1]=band&(1-crease)
np.save('/tmp/black2.npy',black2.astype(bool))
op=cv2.morphologyEx(black2,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
n,l,st,_=cv2.connectedComponentsWithStats(op,connectivity=8)
order=np.argsort(-st[1:,4])+1
print([(i,st[i,4],st[i,:4].tolist()) for i in order[:12]])
keep=np.zeros(n,bool)
for i in order:
    x,y,w,h,a=st[i]
    if a>3000 and max(w,h)>250: keep[i]=True
tr=keep[l].astype(np.uint8)
tr=cv2.dilate(tr,np.ones((5,5),np.uint8))&black2
np.save('/tmp/track.npy',tr.astype(bool))
o=np.where(tr>0,0,255).astype(np.uint8); cv2.imwrite('/tmp/track.png',o)
cv2.imwrite('/tmp/track_s.png',cv2.resize(o,(1400,int(1400*H/W)),interpolation=cv2.INTER_AREA))

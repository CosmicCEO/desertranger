import cv2, numpy as np
from icons_spec import ICONS
n_=np.load('/tmp/norm.npy'); tiles=[]
for s,((a,b,c,d),m,_) in ICONS.items():
    pad=30; A,B=max(0,a-pad),max(0,b-pad); C,D=c+pad,d+pad
    cr=n_[B:D,A:C].copy(); cv2.rectangle(cr,(a-A,b-B),(c-A,d-B),(0,0,255),2)
    h,w=cr.shape[:2]; sc=200/max(h,w); cr=cv2.resize(cr,(int(w*sc),int(h*sc)))
    t=np.full((225,210,3),255,np.uint8); t[:cr.shape[0],:cr.shape[1]]=cr
    cv2.putText(t,s[:24],(2,220),0,0.4,(0,0,0),1); tiles.append(t)
while len(tiles)%7: tiles.append(np.full((225,210,3),255,np.uint8))
cv2.imwrite('/tmp/boxes.jpg',np.vstack([np.hstack(tiles[i:i+7]) for i in range(0,len(tiles),7)]))

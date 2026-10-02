import cv2, numpy as np
n=np.load('/tmp/norm.npy'); H,W=n.shape[:2]
g=cv2.cvtColor(n,cv2.COLOR_BGR2GRAY).astype(np.float32)
lab=cv2.cvtColor(n,cv2.COLOR_BGR2LAB).astype(np.float32)
ch=np.hypot(lab[...,1]-128,lab[...,2]-128)
# local ink level: robust local dark level
mn=cv2.erode(g,np.ones((9,9)))      # get line cores
lo=cv2.erode(mn,np.ones((121,121)))
lo=cv2.GaussianBlur(cv2.dilate(lo,np.ones((61,61))),(0,0),40)
lo=np.minimum(lo,150)
g2=np.clip((g-lo)/(250-lo),0,1)
np.save('/tmp/g2.npy',g2)
ink=(g2<0.42)
black=ink&(ch<20)
color=(ch>20)&(g<235)
color=cv2.morphologyEx(color.astype(np.uint8),cv2.MORPH_OPEN,np.ones((3,3),np.uint8))>0
# colored strokes darken too -> remove from black; but keep black that's adjacent? no
black&=~cv2.dilate(color.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
for nm,m in [('black',black),('color',color)]:
    np.save('/tmp/%s.npy'%nm,m)
    o=np.where(m,0,255).astype(np.uint8); cv2.imwrite('/tmp/%s.png'%nm,o)
    cv2.imwrite('/tmp/%s_s.png'%nm,cv2.resize(o,(1400,int(1400*H/W)),interpolation=cv2.INTER_AREA))

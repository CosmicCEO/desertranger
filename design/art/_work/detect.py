import cv2, numpy as np
A='/home/box/agent-data/agents/e5e321df-9ea7-438c-adec-4927c4c97baa/attachments/'
img=cv2.imread(A+'1c823f93f274fbe4c876a1dfc778b66c989aff7a6267c5797752481fe680c97b.jpg')
s=0.25; sm=cv2.resize(img,None,fx=s,fy=s)
lab=cv2.cvtColor(sm,cv2.COLOR_BGR2LAB)
m=((lab[...,0]>140)&(lab[...,2]>130)).astype(np.uint8)*255
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((31,31),np.uint8))
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((9,9),np.uint8))
n,lbl,st,_=cv2.connectedComponentsWithStats(m)
k=1+np.argmax(st[1:,4]); m=(lbl==k).astype(np.uint8)
# fill holes
cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); m[:]=0; cv2.drawContours(m,cs,-1,1,-1)
H,W=m.shape
rows=np.arange(H); cols=np.arange(W)
has_r=m.any(1); has_c=m.any(0)
left=[(np.argmax(m[y]),y) for y in rows if has_r[y]]
right=[(W-1-np.argmax(m[y,::-1]),y) for y in rows if has_r[y]]
top=[(x,np.argmax(m[:,x])) for x in cols if has_c[x]]
bot=[(x,H-1-np.argmax(m[::-1,x])) for x in cols if has_c[x]]
def fit(pts):
    pts=np.array(pts,np.float32); n=len(pts); pts=pts[int(n*.2):int(n*.8)]
    vx,vy,x0,y0=cv2.fitLine(pts,cv2.DIST_HUBER,0,0.01,0.01).ravel(); return np.array([vx,vy]),np.array([x0,y0])
def inter(a,b):
    (d1,p1),(d2,p2)=a,b; M=np.array([d1,-d2]).T; t=np.linalg.solve(M,p2-p1); return p1+t[0]*d1
L,R,T,B=fit(left),fit(right),fit(top),fit(bot)
q=np.array([inter(T,L),inter(T,R),inter(B,R),inter(B,L)])
print((q/s).round().tolist())
v=sm.copy(); cv2.polylines(v,[q.astype(np.int32)],True,(0,0,255),2)
cv2.imwrite('/tmp/mask.jpg',m*255); cv2.imwrite('/tmp/quad.jpg',v); np.save('/tmp/quad.npy',q/s)

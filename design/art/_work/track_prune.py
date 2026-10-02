import cv2, numpy as np
from skimage.morphology import skeletonize
t=np.load('/tmp/trackF.npy').astype(np.uint8); H,W=t.shape
for a,b,c,d in [(440,20,600,170),(600,150,745,300),(1990,1280,2175,1458)]: t[b:d,a:c]=0
sk0=skeletonize(t>0).astype(np.uint8)
K=np.ones((3,3),np.float32)
def ends(s): return (s==1)&((cv2.filter2D(s,-1,K,borderType=cv2.BORDER_CONSTANT)-s)<=1)
N=45
sk=sk0.copy()
for _ in range(N): sk[ends(sk)]=0
X=(ends(sk)).astype(np.uint8)
for _ in range(N+2): X=cv2.dilate(X,np.ones((3,3),np.uint8))&sk0
sk=sk|X
# remove tiny isolated skeleton bits
n,l,st,_=cv2.connectedComponentsWithStats(sk,connectivity=8)
keep=st[:,4]>60; keep[0]=False; sk=keep[l].astype(np.uint8)
eps=np.argwhere(ends(sk))[:,::-1]
def snap(pt,r=40):
    d=np.hypot(*(eps-np.array(pt)).T); i=np.argmin(d); return tuple(int(v) for v in eps[i]) if d[i]<r else pt
arc=[(463,68),(536,102),(610,165),(675,241),(708,285)]
arc[0]=snap(arc[0]); arc[-1]=snap(arc[-1]); print('arc',arc)
# smooth spline through points
P=np.array(arc,np.float32); tt=np.linspace(0,1,len(P)); ts=np.linspace(0,1,200)
cx=np.polyfit(tt,P[:,0],3); cy=np.polyfit(tt,P[:,1],3)
curve=np.stack([np.polyval(cx,ts),np.polyval(cy,ts)],1); curve[0]=P[0]; curve[-1]=P[-1]
cv2.polylines(sk,[curve.astype(np.int32)],False,1,1)
np.save('/tmp/trackSK.npy',sk)
line=cv2.dilate(sk,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))
line=cv2.GaussianBlur(line.astype(np.float32),(0,0),1.0)>0.5
np.save('/tmp/trackLine.npy',line)
o=np.where(line,0,255).astype(np.uint8); cv2.imwrite('layers/track.png',o)
n_=np.load('/tmp/norm.npy'); v=(n_*0.6+150).clip(0,255).astype(np.uint8); v[line]=(0,0,255)
for (y,x) in np.argwhere(ends(sk)): cv2.circle(v,(int(x),int(y)),9,(0,160,0),3)
cv2.imwrite('/tmp/ovall.jpg',cv2.resize(v,(1500,int(1500*H/W)),interpolation=cv2.INTER_AREA))
print('endpoints',int(ends(sk).sum()))
# auto-bridge close endpoint pairs
from itertools import combinations
eps=np.argwhere(ends(sk))[:,::-1]; used=set()
n,l,st,_=cv2.connectedComponentsWithStats(sk,connectivity=8)
pairs=sorted([(np.hypot(*(eps[i]-eps[j])),i,j) for i,j in combinations(range(len(eps)),2)])
for d,i,j in pairs:
    if d>70: break
    if i in used or j in used: continue
    cv2.line(sk,tuple(map(int,eps[i])),tuple(map(int,eps[j])),1,1); used|={i,j}; print('bridged',eps[i],eps[j],round(d))
np.save('/tmp/trackSK.npy',sk)
line=cv2.dilate(sk,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))
line=cv2.GaussianBlur(line.astype(np.float32),(0,0),1.0)>0.5
np.save('/tmp/trackLine.npy',line)
cv2.imwrite('layers/track.png',np.where(line,0,255).astype(np.uint8))
cv2.imwrite('/tmp/track_s.png',cv2.resize(np.where(line,0,255).astype(np.uint8),(1400,int(1400*H/W)),interpolation=cv2.INTER_AREA))

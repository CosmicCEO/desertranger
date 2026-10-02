import cv2, numpy as np
from skimage.morphology import skeletonize
g2=np.load('/tmp/g2.npy'); ch=np.load('/tmp/chroma.npy')
t=np.load('/tmp/track3.npy').astype(np.uint8); H,W=t.shape
weak=((g2<0.78)&(ch<18)).astype(np.uint8)
weak=cv2.morphologyEx(weak,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)))
ACC=[(450,40,720,290),(420,770,730,815),(1740,220,1775,360),(1770,1520,1860,1575),(1900,1440,2060,1500)]
for a,b,c,d in ACC: t[b:d,a:c]|=weak[b:d,a:c]
ER=[(1660,1080,1740,1172),(1805,1090,1860,1160),(2895,1540,2966,1670),(2085,1300,2175,1462)]
for a,b,c,d in ER: t[b:d,a:c]=0
def endpoints(m):
    sk=skeletonize(m>0).astype(np.uint8)
    nb=cv2.filter2D(sk,-1,np.ones((3,3)),borderType=cv2.BORDER_CONSTANT)
    return np.argwhere((sk==1)&(nb==2))[:,::-1]
ep=endpoints(t)
BR=[((1771,51),(1844,49)),((1785,350),(1850,345)),((1780,525),(1840,523)),((1770,820),(1830,785)),
    ((945,1840),(1092,1866)),((2384,314),(2566,300)),((2465,1963),(2540,1963)),((1826,1192),(1955,1268))]
for p,q in BR:
    pp=[]
    for r in (p,q):
        d=np.hypot(*(ep-np.array(r)).T); i=np.argmin(d)
        pp.append(tuple(ep[i]) if d[i]<45 else r)
        print(r,'->',pp[-1],round(float(d[i]),1))
    cv2.line(t,tuple(map(int,pp[0])),tuple(map(int,pp[1])),1,8,cv2.LINE_AA)
# remove small isolated bits
n,l,st,_=cv2.connectedComponentsWithStats(t,connectivity=8)
keep=st[:,4]>400; keep[0]=False; t=keep[l].astype(np.uint8)
# smooth edges
tb=cv2.GaussianBlur(t.astype(np.float32),(0,0),1.2)>0.5
np.save('/tmp/trackF.npy',tb)
print('remaining endpoints', len(endpoints(tb.astype(np.uint8))))
o=np.where(tb,0,255).astype(np.uint8)
import os; os.makedirs('layers',exist_ok=True)
cv2.imwrite('layers/track.png',o)
n_=np.load('/tmp/norm.npy'); v=(n_*0.6+150).clip(0,255).astype(np.uint8); v[tb]=(0,0,255)
for (x,y) in endpoints(tb.astype(np.uint8)): cv2.circle(v,(int(x),int(y)),9,(0,160,0),3)
cv2.imwrite('/tmp/ovall.jpg',cv2.resize(v,(1500,int(1500*H/W)),interpolation=cv2.INTER_AREA))

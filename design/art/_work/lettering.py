import cv2, numpy as np, json
g2=np.load('/tmp/g2.npy'); ch=np.load('/tmp/chroma.npy'); H,W=g2.shape
trk=cv2.dilate(np.load('/tmp/trackLine.npy').astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(13,13)))
man=json.load(open('icons/manifest.json'))['icons']
icon_m=np.zeros((H,W),np.uint8); icon_lines=np.zeros((H,W),np.uint8); icon_rgba=np.zeros((H,W,4),np.uint8)
for s,v in man.items():
    x,y,w,h=v['bbox_3000']
    la=cv2.imread(v['files']['lineart_png'],cv2.IMREAD_UNCHANGED); co=cv2.imread(v['files']['color_png'],cv2.IMREAD_UNCHANGED)
    a=co[...,3]>40
    icon_m[y:y+h,x:x+w]|=a.astype(np.uint8)
    icon_lines[y:y+h,x:x+w]=np.maximum(icon_lines[y:y+h,x:x+w],la[...,3])
    sub=icon_rgba[y:y+h,x:x+w]; al=co[...,3:4]/255.0
    sub[...,:3]=(co[...,:3]*al+sub[...,:3]*(1-al)).astype(np.uint8); sub[...,3]=np.maximum(sub[...,3],co[...,3])
np.save('/tmp/icon_m.npy',icon_m)
L=((g2<0.62)&(ch<12)).astype(np.uint8)
L&=1-trk; L&=1-cv2.dilate(icon_m,np.ones((9,9),np.uint8))
# crease removal
x0,x1=1740,1900; b=L[:,x0:x1]
vert=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(1,70)))
L[:,x0:x1]=b&(1-cv2.dilate(vert,np.ones((3,5),np.uint8)))
# remove board-edge junk: 12px margin
L[:14,:]=0;L[-14:,:]=0;L[:,:14]=0;L[:,-14:]=0
n,l,st,_=cv2.connectedComponentsWithStats(L,connectivity=8)
keep=(st[:,4]>=18)&(st[:,4]<6000); keep[0]=False; L=keep[l].astype(np.uint8)
La=(cv2.GaussianBlur(L.astype(np.float32),(0,0),0.6)*255).clip(0,255).astype(np.uint8)
cv2.imwrite('layers/lettering.png',255-La)
rg=np.zeros((H,W,4),np.uint8); rg[...,3]=La; cv2.imwrite('layers/lettering-transparent.png',rg)
# composites
track=np.load('/tmp/trackLine.npy')
tra=(cv2.GaussianBlur(track.astype(np.float32),(0,0),0.6)*255).astype(np.uint8)
ink=np.maximum.reduce([tra,La,icon_lines])
cv2.imwrite('board-lineart.png',255-ink)
cv2.imwrite('/tmp/bl.pbm',np.where(ink>127,0,255).astype(np.uint8))
# colour composite: cream-white bg, icon colours, then track+lettering black on top
bg=np.full((H,W,3),255,np.float32)
al=icon_rgba[...,3:4]/255.0; bg=bg*(1-al)+icon_rgba[...,:3]*al
k=(np.maximum(tra,La)/255.0)[...,None]; bg=bg*(1-k)+20*k
cv2.imwrite('board-lineart-color.png',bg.astype(np.uint8))

import cv2, numpy as np, json
man=json.load(open('icons/manifest.json'))['icons']
tiles=[]; T=230
def fit(im,box=200):
    h,w=im.shape[:2]; s=box/max(h,w); return cv2.resize(im,(max(1,int(w*s)),max(1,int(h*s))),interpolation=cv2.INTER_AREA)
def comp(rgba,bg):
    a=rgba[...,3:4]/255.0; return (rgba[...,:3]*a+bg*(1-a)).astype(np.uint8)
for slug,v in man.items():
    la=cv2.imread(v['files']['lineart_png'],cv2.IMREAD_UNCHANGED); co=cv2.imread(v['files']['color_png'],cv2.IMREAD_UNCHANGED)
    t=np.full((T+40,2*T+10,3),255,np.uint8)
    # checker bg to show transparency
    chk=((np.indices((T,T)).sum(0)//10)%2*20+230).astype(np.uint8)[...,None].repeat(3,2)
    for j,im in enumerate([la,co]):
        bg=chk.copy(); f=fit(im,T-10); h,w=f.shape[:2]; y,x=(T-h)//2,(T-w)//2
        bg[y:y+h,x:x+w]=comp(f,bg[y:y+h,x:x+w].astype(np.float32)); t[0:T,j*(T+10):j*(T+10)+T]=bg
    sq=v['square']; cv2.putText(t,f"{slug} [sq {sq}]",(4,T+25),0,0.5,(0,0,0),1)
    tiles.append(t)
C=4
while len(tiles)%C: tiles.append(np.full_like(tiles[0],255))
sheet=np.vstack([np.hstack([np.pad(x,((5,5),(5,5),(0,0)),constant_values=255) for x in tiles[i:i+C]]) for i in range(0,len(tiles),C)])
cv2.imwrite('icons-preview.png',sheet); print(sheet.shape)

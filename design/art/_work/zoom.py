import cv2, numpy as np, sys, json
t=np.load(sys.argv[1]); out=sys.argv[2]; centers=json.loads(sys.argv[3])
n_=np.load('/tmp/norm.npy'); H,W=t.shape
v=(n_*0.6+150).clip(0,255).astype(np.uint8); v[t]=(0,0,255)
tiles=[]
for cx,cy in centers:
    x0=max(0,min(W-400,cx-200)); y0=max(0,min(H-400,cy-200))
    c=v[y0:y0+400,x0:x0+400].copy()
    for gx in range((x0//50+1)*50,x0+400,50):
        cv2.line(c,(gx-x0,0),(gx-x0,399),(255,200,0),1)
        if gx%100==0: cv2.putText(c,str(gx),(gx-x0+2,12),0,0.4,(200,0,0),1)
    for gy in range((y0//50+1)*50,y0+400,50):
        cv2.line(c,(0,gy-y0),(399,gy-y0),(255,200,0),1)
        if gy%100==0: cv2.putText(c,str(gy),(2,gy-y0-2),0,0.4,(200,0,0),1)
    cv2.rectangle(c,(0,0),(399,399),(0,0,0),2); tiles.append(c)
while len(tiles)%3: tiles.append(np.full((400,400,3),255,np.uint8))
rows=[np.hstack(tiles[i:i+3]) for i in range(0,len(tiles),3)]
cv2.imwrite(out,np.vstack(rows))

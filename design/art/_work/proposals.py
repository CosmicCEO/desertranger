import cv2, numpy as np, json
color=np.load('/tmp/color.npy').astype(np.uint8); H,W=color.shape
ch=np.load('/tmp/chroma.npy'); n_=np.load('/tmp/norm.npy')
# softer color mask for light doodles (yellow etc)
col=((ch>14)).astype(np.uint8)
col=cv2.morphologyEx(col,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
cl=cv2.dilate(col,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(41,41)))
n,l,st,_=cv2.connectedComponentsWithStats(cl)
props=[]
for i in range(1,n):
    x,y,w,h,a=st[i]
    core=(col[y:y+h,x:x+w]&(l[y:y+h,x:x+w]==i)).sum()
    if core<400: continue
    props.append([int(x+20),int(y+20),int(w-40),int(h-40),int(core)])
print(len(props))
v=(n_*0.7+70).clip(0,255).astype(np.uint8)
for k,(x,y,w,h,c) in enumerate(props):
    cv2.rectangle(v,(x,y),(x+w,y+h),(0,0,255),3); cv2.putText(v,str(k),(x,y-5),0,1.4,(255,0,0),4)
cv2.imwrite('/tmp/props.jpg',cv2.resize(v,(1500,int(1500*H/W)),interpolation=cv2.INTER_AREA))
json.dump(props,open('/tmp/props.json','w'))
for k,p in enumerate(props): print(k,p)

import cv2, numpy as np, sys
img=cv2.imread('board-flat.jpg')
TW=3000; s=TW/img.shape[1]
img=cv2.resize(img,None,fx=s,fy=s,interpolation=cv2.INTER_AREA)
H,W=img.shape[:2]
f=img.astype(np.float32)
# background estimate per channel: close (remove dark ink) then big blur
k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(31,31))
bg=cv2.morphologyEx(img,cv2.MORPH_CLOSE,k)
bg=cv2.GaussianBlur(bg,(0,0),25).astype(np.float32)
norm=np.clip(f/(bg+1)*255,0,255).astype(np.uint8)
cv2.imwrite('/tmp/norm.jpg',norm)
np.save('/tmp/norm.npy',norm)
gray=cv2.cvtColor(norm,cv2.COLOR_BGR2GRAY)
hsv=cv2.cvtColor(norm,cv2.COLOR_BGR2HSV)
# ink strength: darkness from min channel (colored ink is dark in at least one channel)
mn=norm.min(2).astype(np.float32)
dark=255-gray.astype(np.float32)
ink=np.maximum(dark, (255-mn)*0.85)
ink=cv2.GaussianBlur(ink,(0,0),0.8)
np.save('/tmp/ink.npy',ink)

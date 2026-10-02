import cv2, numpy as np
A='/home/box/agent-data/agents/e5e321df-9ea7-438c-adec-4927c4c97baa/attachments/'
img=cv2.imread(A+'1c823f93f274fbe4c876a1dfc778b66c989aff7a6267c5797752481fe680c97b.jpg')
q=np.load('/tmp/quad.npy').astype(np.float32)
c=q.mean(0); q=c+(q-c)*0.995  # tiny inset to avoid background slivers
w=int((np.linalg.norm(q[1]-q[0])+np.linalg.norm(q[2]-q[3]))/2)
h=int((np.linalg.norm(q[3]-q[0])+np.linalg.norm(q[2]-q[1]))/2)
print(w,h,w/h)
M=cv2.getPerspectiveTransform(q,np.float32([[0,0],[w,0],[w,h],[0,h]]))
out=cv2.warpPerspective(img,M,(w,h),flags=cv2.INTER_CUBIC)
cv2.imwrite('board-flat.jpg',out,[cv2.IMWRITE_JPEG_QUALITY,93])
cv2.imwrite('/tmp/flat_s.jpg',cv2.resize(out,None,fx=0.3,fy=0.3,interpolation=cv2.INTER_AREA))

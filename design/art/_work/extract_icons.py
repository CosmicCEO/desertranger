import cv2, numpy as np, json, os, subprocess, re
from sklearn.cluster import KMeans
from icons_spec import ICONS
os.makedirs('icons',exist_ok=True)
n_=np.load('/tmp/norm.npy'); g2=np.load('/tmp/g2.npy'); ch=np.load('/tmp/chroma.npy'); H,W=g2.shape
trk=cv2.dilate(np.load('/tmp/trackLine.npy').astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(11,11)))
colorsoft=((ch>14)&(g2<0.93)).astype(np.uint8)
colorsoft=cv2.morphologyEx(colorsoft,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
dark=(g2<0.55).astype(np.uint8)
SQ={"cattails-ocotillo":41,"fonts-point-rays":43,"red-arrow":40,"fish":39,"barrel":45,"numeral-17-palms":38,"cholla-cactus":46,"bow":37,
"sunset-mountain":47,"numeral-9":48,"numeral-17-small":49,"ground-fire":50,"finish":51,"start":0,"title-desert-ranger":None,
"palm-trees":2,"star":3,"sandstone":4,"shortcut-arrow":6,"reeds":7,"signpost":9,"grapes":10,"dos-cabezas":11,"ocotillo-stems":12,
"screwdriver":13,"wrench":13,"fault-wash":15,"water-drop":16,"willows":17,"wagon-wheel":18,"arroyo-salado":19,"hawk-canyon":20,
"ladder":21,"arrow-back-10":23,"sheep":24,"tamarisk":25,"olla":26,"dice":29,"yaqui-pass":32,"court-gavel":34,"una-palma":33,"numeral-4":35}
# square centers -> 3000px flat space
q=np.load('/tmp/quad.npy').astype(np.float32); c=q.mean(0); q=c+(q-c)*0.995
FW,FH=4372,3321; M=cv2.getPerspectiveTransform(q,np.float32([[0,0],[FW,0],[FW,FH],[0,FH]]))
board=json.load(open('../board/desert-ranger.json'))
pts=np.array([[s['x'],s['y']] for s in board['squares']],np.float32).reshape(-1,1,2)
flat=cv2.perspectiveTransform(pts,M).reshape(-1,2); S=W/FW; sq3000=flat*S
def potrace(mask,out,color='#000000'):
    pbm='/tmp/_p.pbm'; cv2.imwrite(pbm,np.where(mask,0,255).astype(np.uint8))
    subprocess.run(['potrace',pbm,'-s','-t','4','-a','1.2','-O','0.4','-C',color,'-o',out],check=True)
manifest={}
for slug,spec in ICONS.items():
    (a,b,c_,d),mode,label=spec[:3]; P=spec[3] if len(spec)>3 else {}
    cth=P.get('cth',14); dthr=P.get('dthr',0.55)
    cs=((ch[b:d,a:c_]>cth)&(g2[b:d,a:c_]<0.93)).astype(np.uint8)
    cs=cv2.morphologyEx(cs,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    dk=(g2[b:d,a:c_]<dthr).astype(np.uint8)
    if mode=='color':
        m=cs | (dk & cv2.dilate(cs,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9))))
    else:
        m=cs | dk
    m&=1-trk[b:d,a:c_]
    if 'rects' in P:
        rm=np.zeros_like(m)
        for (ra,rb,rc,rd) in P['rects']: rm[rb-b:rd-b,ra-a:rc-a]=1
        m&=rm
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    nn,l,st,_=cv2.connectedComponentsWithStats(m,connectivity=8)
    keep=st[:,4]>=40; keep[0]=False; m=keep[l].astype(np.uint8)
    # fill tiny holes
    inv=1-m; nn,l,st,_=cv2.connectedComponentsWithStats(inv,connectivity=4)
    small=(st[:,4]<25); small[0]=False; m[small[l]]=1
    ys,xs=np.nonzero(m)
    if len(xs)==0: print('EMPTY',slug); continue
    p=8; x0,x1,y0,y1=max(0,xs.min()-p),min(m.shape[1],xs.max()+p+1),max(0,ys.min()-p),min(m.shape[0],ys.max()+p+1)
    m=m[y0:y1,x0:x1]; rgb=n_[b+y0:b+y1,a+x0:a+x1].astype(np.float32)
    gx0,gy0=a+x0,b+y0
    alpha=(cv2.GaussianBlur(m.astype(np.float32),(0,0),0.7)*255).clip(0,255).astype(np.uint8)
    gg=g2[b+y0:b+y1,a+x0:a+x1]; cc=ch[b+y0:b+y1,a+x0:a+x1]
    rim=m&(1-cv2.erode(m,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7))))
    inner=((gg<0.40)&(cc<22)).astype(np.uint8)&m
    inner=cv2.morphologyEx(inner,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    line=(rim|inner).astype(np.uint8)
    nn2,l2,st2,_=cv2.connectedComponentsWithStats(line,connectivity=8); kk=st2[:,4]>=15; kk[0]=False; line=kk[l2].astype(np.uint8)
    lalpha=(cv2.GaussianBlur(line.astype(np.float32),(0,0),0.6)*255).clip(0,255).astype(np.uint8)
    la=np.zeros(m.shape+(4,),np.uint8); la[...,3]=lalpha
    cv2.imwrite(f'icons/{slug}.png',la)
    potrace(line>0,f'icons/{slug}.svg')
    # color version: kmeans on Lab
    pix=cv2.cvtColor(rgb.astype(np.uint8),cv2.COLOR_BGR2LAB).reshape(-1,3)[m.reshape(-1)>0].astype(np.float32)
    K=int(min(6,max(2,len(pix)//800)))
    km=KMeans(K,n_init=4,random_state=0).fit(pix[::max(1,len(pix)//20000)])
    lab_all=cv2.cvtColor(rgb.astype(np.uint8),cv2.COLOR_BGR2LAB).reshape(-1,3).astype(np.float32)
    lbl=km.predict(lab_all).reshape(m.shape).astype(np.uint8)
    lbl=cv2.medianBlur(lbl,5)
    cents=km.cluster_centers_.copy()
    # boost chroma, push darks to near-black
    cents[:,1:]=128+(cents[:,1:]-128)*1.35
    cents[cents[:,0]<90,0]*=0.6
    cbgr=cv2.cvtColor(cents.clip(0,255).astype(np.uint8).reshape(1,-1,3),cv2.COLOR_LAB2BGR).reshape(-1,3)
    col=np.zeros(m.shape+(4,),np.uint8); col[...,:3]=cbgr[lbl]; col[...,3]=alpha
    la_f=lalpha[...,None]/255.0; col[...,:3]=(col[...,:3]*(1-la_f)+20*la_f).astype(np.uint8)
    col[...,3]=np.maximum(alpha,lalpha)
    cv2.imwrite(f'icons/{slug}-color.png',col)
    # color svg: one potrace layer per cluster, lightest first
    order=np.argsort(-cents[:,0]); groups=[]
    for k in order:
        mk=(lbl==k)&(m>0)
        if mk.sum()<30: continue
        hexc='#%02x%02x%02x'%tuple(int(v) for v in cbgr[k][::-1])
        potrace(mk,'/tmp/_k.svg',hexc)
        s=open('/tmp/_k.svg').read(); groups.append(s[s.index('<g'):s.rindex('</g>')+4])
    potrace(line>0,'/tmp/_k.svg','#141414'); s2=open('/tmp/_k.svg').read(); groups.append(s2[s2.index('<g'):s2.rindex('</g>')+4])
    base=open(f'icons/{slug}.svg').read()
    head=base[:base.index('<g')]
    open(f'icons/{slug}-color.svg','w').write(head+'\n'.join(groups)+'\n</svg>\n')
    cx,cy=gx0+(x1-x0)/2,gy0+(y1-y0)/2
    d=np.hypot(sq3000[:,0]-cx,sq3000[:,1]-cy); near=int(np.argmin(d))
    bb3000=[int(gx0),int(gy0),int(x1-x0),int(y1-y0)]
    manifest[slug]={"label":label,"square":SQ.get(slug),
        "squareName":board['squares'][SQ[slug]]['name'] if SQ.get(slug) is not None else None,
        "nearestSquareByCenter":near,
        "bbox_flat":[round(v/S) for v in bb3000],"bbox_3000":bb3000,
        "files":{"lineart_png":f"icons/{slug}.png","lineart_svg":f"icons/{slug}.svg","color_png":f"icons/{slug}-color.png","color_svg":f"icons/{slug}-color.svg"},
        "mode":mode,"params":{k:v for k,v in P.items()}}
json.dump({"coordinateSpace":{"bbox_flat":"[x,y,w,h] in art/board-flat.jpg pixels (%dx%d)"%(FW,FH),"bbox_3000":"[x,y,w,h] in 3000px-wide working space (3000x%d) = board-flat scaled by %.4f"%(H,S)},
           "icons":manifest},open('icons/manifest.json','w'),indent=1)
for k,v in manifest.items():
    if v['square']!=v['nearestSquareByCenter']: print('mismatch',k,v['square'],v['nearestSquareByCenter'])
np.save('/tmp/sq3000.npy',sq3000)

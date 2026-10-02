import numpy as np, librosa, soundfile as sf, json, glob, os, re, sys, warnings
from scipy.signal import fftconvolve, butter, sosfilt, lfilter
warnings.filterwarnings("ignore")
SR=48000; T="/workspace/boardgame/audio/samples/crowd/takes_v2"; O="/workspace/boardgame/audio/samples/crowd"
scr=json.load(open(f"{O}/takes_v2_screen.json"))
KEEP={"cheer":set("yeah yeahh woo whoo wooo woooo whoa woohoo woo-hoo whoo-hoo hoo huzzah hazza huzza hussah baby yay hooray yahoo yes woah woohoohoo ooh wahoo".split()),
      "aww":set("oh ohh ohhh ooh oooh aw aww awww awe no nooo noo ah oh-no ooh oooh".split())}
def ok(b,cat):
  r=scr.get(b)
  if not r: return False
  toks=re.findall(r"[a-z\-]+",r["text"].lower())
  return bool(toks) and all(t in KEEP[cat] for t in toks) and 0.3<r["dur"]<(2.0 if cat=="cheer" else 2.4)
def pool(cat):
  P={}
  for f in sorted(glob.glob(f"{T}/*{cat}_*.wav")):
    b=os.path.basename(f)
    if not ok(b,cat): continue
    src="cb" if b.startswith("cb") else "k"; v=b.split("_")[1]+"_"+b.split("_")[2]
    P.setdefault((src,v),[]).append(f)
  return P
def peaking(x,f0,gdb,Q):
  A=10**(gdb/40); w=2*np.pi*f0/SR; al=np.sin(w)/(2*Q)
  b=[1+al*A,-2*np.cos(w),1-al*A]; a=[1+al/A,-2*np.cos(w),1-al/A]
  return lfilter(np.array(b)/a[0],np.array(a)/a[0],x,axis=0)
def comp(x,thr_db,ratio,att=0.002,rel=0.06):
  env=np.abs(x).max(1); e=np.zeros_like(env); a1=np.exp(-1/(att*SR)); r1=np.exp(-1/(rel*SR)); s=0.0
  for i,v in enumerate(env):
    s=a1*s+(1-a1)*v if v>s else r1*s+(1-r1)*v; e[i]=s
  ed=20*np.log10(e+1e-9); gr=np.minimum(0,(thr_db-ed)*(1-1/ratio))
  return x*(10**(gr/20))[:,None]
def load(f,rng,st,rate):
  y,_=librosa.load(f,sr=SR); y,_=librosa.effects.trim(y,top_db=32)
  if abs(st)>0.05: y=librosa.effects.pitch_shift(y,sr=SR,n_steps=st)
  y=librosa.effects.time_stretch(y,rate=rate); y/=np.abs(y).max()+1e-9
  n=int(0.004*SR); y[:n]*=np.linspace(0,1,n); m=int(0.06*SR); y[-m:]*=np.linspace(1,0,m)
  return y
def ir(rng,rt,dur=1.0):
  n=int(dur*SR); t=np.arange(n)/SR; h=rng.standard_normal((n,2))*np.exp(-6.9*t/rt)[:,None]
  h=sosfilt(butter(2,[250,7000],btype="band",fs=SR,output="sos"),h,axis=0); h[:int(0.006*SR)]=0
  for d,g in [(0.009,0.5),(0.014,0.4),(0.021,0.35),(0.029,0.3)]:
    i=int(d*SR); h[i,0]+=g; h[i+int(rng.uniform(1,4)*SR/1000),1]+=g
  return h/np.sqrt((h**2).sum(0)).max()
def pan2(y,p): return np.stack([y*np.cos((p+1)*np.pi/4),y*np.sin((p+1)*np.pi/4)],1)
def claps(rng,dur,n=22,start=0.03,stop=3.0):
  out=np.zeros((int(dur*SR),2)); sos=butter(2,[800,5000],btype="band",fs=SR,output="sos")
  for p in range(n):
    rate=rng.uniform(4.5,6.5); t=start+rng.uniform(0,0.12); pan=rng.uniform(-0.9,0.9); g0=10**(rng.uniform(-8,0)/20)
    while t<stop:
      L=int(rng.uniform(0.02,0.035)*SR); e=np.exp(-np.arange(L)/(rng.uniform(0.003,0.006)*SR)); e[:60]*=np.linspace(0,1,60)
      b=sosfilt(sos,rng.standard_normal(L))*e; fade=1.0 if t<stop-0.8 else max(0,(stop-t)/0.8)
      i=int(t*SR); out[i:i+L]+=pan2(b*g0*fade*rng.uniform(0.7,1),pan); t+=1/rate*rng.uniform(0.85,1.15)
  return out
def whistle(rng,kind):
  # synthesized whistle: sine with glide 2-3.5 kHz, vibrato, breath noise, slight 2nd harmonic
  if kind=="wolf":   # rise then fall
    segs=[(0.28,2100,3400),(0.06,3400,3400),(0.45,3400,2000)]
  else:              # long rising "fweeee" with sustained top
    segs=[(0.22,2200,3300),(0.7,3300,3150)]
  f=np.concatenate([np.linspace(a,b,int(d*SR)) for d,a,b in segs]); n=len(f); t=np.arange(n)/SR
  f=f*(1+0.012*np.sin(2*np.pi*rng.uniform(5.5,7)*t)*np.clip(t/0.15,0,1))
  ph=2*np.pi*np.cumsum(f)/SR; y=np.sin(ph)+0.06*np.sin(2*ph)
  env=np.clip(t/0.03,0,1)*np.clip((t[-1]-t)/0.08,0,1)*(1+0.1*np.sin(2*np.pi*3*t))
  nz=sosfilt(butter(2,[1800,4500],btype="band",fs=SR,output="sos"),rng.standard_normal(n))
  return (y*0.9+nz*0.12)*env
def varirate(x,contour):
  # time-varying resample: contour(t)->playback rate; gives a rising-then-falling pitch feel
  t=np.arange(len(x))/SR; r=contour(t); pos=np.cumsum(r); pos=pos[pos<len(x)-1]
  return np.stack([np.interp(pos,np.arange(len(x)),x[:,k]) for k in range(2)],1)
def mix(cat,seed,dur,waves,cb_frac,st_rng,rate_rng,rt,clap_db=None,n_wh=0,contour=None,macro=None,pres_db=3.5):
  rng=np.random.default_rng(seed); P=pool(cat); keys=list(P); cbk=[k for k in keys if k[0]=="cb"]; kk=[k for k in keys if k[0]=="k"]
  print(cat,"cb voices",len(cbk),"cb takes",sum(len(P[k]) for k in cbk),"| kokoro voices",len(kk),"takes",sum(len(P[k]) for k in kk))
  N=int((dur+1.5)*SR); bus=np.zeros((N,2)); log=[]
  for (n,lo,hi) in waves:
    for j in range(n):

      src=cbk if (rng.random()<cb_frac and cbk) else kk
      key=src[rng.integers(len(src))]; f=P[key][rng.integers(len(P[key]))]
      st=rng.uniform(*st_rng); rate=rng.uniform(*rate_rng); y=load(f,rng,st,rate)
      off=rng.uniform(lo,hi); dist=rng.uniform(0,1)**1.5
      g=10**((-1-6*dist+rng.uniform(-1,1))/20)*(0.8 if lo>0.5 else 1.0)
      y=sosfilt(butter(1,13000-4500*dist,fs=SR,output="sos"),y)
      i=int(off*SR); L=min(len(y),N-i); bus[i:i+L]+=pan2(y[:L]*g,rng.uniform(-0.9,0.9))
      log.append(dict(f=os.path.basename(f),off=round(off,3),st=round(st,2),rate=round(rate,2)))
  if contour is not None: bus=varirate(bus,contour); bus=np.pad(bus,((0,max(0,N-len(bus))),(0,0)))[:N]
  bus=sosfilt(butter(2,110,btype="high",fs=SR,output="sos"),bus,axis=0)
  bus=peaking(bus,3000,pres_db,0.9); bus=peaking(bus,350,-1.5,1.0)        # upper-mid presence, de-mud
  vr=np.sqrt((bus[:int(1.5*SR)]**2).mean())
  if clap_db is not None:
    c=claps(rng,N/SR); c*=10**(clap_db/20)*vr/(np.sqrt((c[:int(1.5*SR)]**2).mean())+1e-9); bus+=c
  for w in range(n_wh):
    y=whistle(rng,"wolf" if w%2==0 else "long"); off=rng.uniform(0.2,1.4); i=int(off*SR)
    y=y*vr*10**(rng.uniform(-10,-6)/20)/np.sqrt((y**2).mean()); bus[i:i+len(y)]+=pan2(y,rng.uniform(-0.7,0.7))
    log.append(dict(whistle=w,off=round(off,2)))
  h=ir(rng,rt); wet=np.stack([fftconvolve(bus[:,k],h[:,k])[:N] for k in range(2)],1)
  dry=0.85*bus+0.2*wet
  dry/=np.abs(dry).max()
  sq=comp(dry,-28,10,0.001,0.08); sq/=np.abs(sq).max()            # parallel (NY) compression
  y=dry+0.55*sq; y=comp(y/np.abs(y).max(),-10,2.5,0.003,0.12)
  if macro is not None:
    tt=np.arange(len(y))/SR; y=y*(10**(np.interp(tt,macro[0],macro[1])/20))[:,None]
  y=y[:int(dur*SR)]; fo=int(0.55*SR); y[-fo:]*=np.linspace(1,0,fo)[:,None]**1.5; y[:96]*=np.linspace(0,1,96)[:,None]
  y/=np.abs(y).max()/0.7
  fn=f"{O}/raw_{cat}_v2.wav"; sf.write(fn,y,SR,subtype="PCM_24"); json.dump(log,open(f"{O}/mixlog_{cat}_v2.json","w"),indent=0)
  print(fn,len(log),"layers")
S=int(os.environ.get("SEED",1))
if "cheer" in sys.argv:
  mix("cheer",100+S,3.3,[(20,0.0,0.15),(4,0.15,0.35),(10,0.75,1.3),(6,1.5,2.1)],0.72,(-1.5,1.5),(0.95,1.1),0.6,clap_db=-8,n_wh=3,
      macro=([0,0.45,0.7,0.85,1.05,1.6,2.3,3.3],[0,0,-3.5,-3.5,0.5,0.5,-2.5,-5]))
if "aww" in sys.argv:
  def ctr(t): return np.interp(t,[0,0.35,0.9,1.6,3.5,5],[1.0,1.035,1.05,1.0,0.9,0.9])
  mix("aww",200+S,3.4,[(18,0.0,0.15),(4,0.15,0.4),(9,0.6,1.2),(5,1.3,1.8)],0.75,(-1.0,1.5),(0.72,0.92),0.75,contour=ctr,pres_db=5,
      macro=([0,0.2,0.5,0.9,1.4,2.0,2.8,3.4],[-4,-1,-1.5,0,0,-1.5,-4.5,-7]))

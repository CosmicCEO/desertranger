import numpy as np, librosa, soundfile as sf, json, glob, os, re, sys, warnings
from scipy.signal import fftconvolve, butter, sosfilt
warnings.filterwarnings("ignore")
SR=48000; T="/workspace/boardgame/audio/samples/crowd/takes"; O="/workspace/boardgame/audio/samples/crowd"
scr=json.load(open(f"{O}/takes_screen.json"))
KEEP={"cheer":set("yeah woot wood woota huzzah hizah woo whoo woohoo woo-hoo yahoo whoa yay hooray".split()),
      "aww":set("oh aw aww awe ooh ohh no man ah".split())}
def takes(cat):
  out=[]
  for f in sorted(glob.glob(f"{T}/{cat}_*.wav")):
    b=os.path.basename(f); r=scr.get(b)
    toks=re.findall(r"[a-z\-]+",r["text"].lower()) if r else []
    if toks and all(t in KEEP[cat] for t in toks) and 0.25<r["dur"]<1.6: out.append(f)
  CB={"cheer":["ranger_w0","ranger_w1","ranger_w2","rough_w0","rough_w1"],"aww":["ranger_w0","ranger_w1","ranger_w2","rough_w1","rough_w2"]}  # Whisper-checked
  out+=[f"{T}/cb{cat}_{k}.wav" for k in CB[cat]]
  return out
def voice_of(f): return os.path.basename(f).split("_",1)[1].rsplit("_w",1)[0] if not os.path.basename(f).startswith("cb") else "cb_"+os.path.basename(f).split("_")[1]
def load(f,rng,rate=(0.92,1.08)):
  y,_=librosa.load(f,sr=SR); y,_=librosa.effects.trim(y,top_db=35)
  y=librosa.effects.pitch_shift(y,sr=SR,n_steps=rng.uniform(-2,2))
  y=librosa.effects.time_stretch(y,rate=rng.uniform(*rate))
  y/=np.abs(y).max()+1e-9
  f=np.minimum(len(y),int(0.01*SR)); y[:f]*=np.linspace(0,1,f); y[-int(0.04*SR):]*=np.linspace(1,0,int(0.04*SR))
  return y
def ir(rng,rt=0.55,dur=0.9):
  n=int(dur*SR); t=np.arange(n)/SR; env=np.exp(-6.9*t/rt)
  h=rng.standard_normal((n,2))*env[:,None]
  sos=butter(2,[200,6000],btype="band",fs=SR,output="sos"); h=sosfilt(sos,h,axis=0)
  h[:int(0.008*SR)]=0
  for d,g in [(0.011,0.5),(0.017,0.4),(0.023,0.35),(0.031,0.3),(0.041,0.22)]:
    i=int(d*SR); h[i,0]+=g*rng.uniform(.7,1); h[i+int(rng.uniform(1,4)*SR/1000),1]+=g*rng.uniform(.7,1)
  return h/np.sqrt((h**2).sum(0)).max()
def claps(rng,dur,n_people=16,start=0.15,stop=2.45):
  out=np.zeros((int(dur*SR),2)); sos=butter(2,[900,4500],btype="band",fs=SR,output="sos")
  for p in range(n_people):
    rate=rng.uniform(3.5,5.5); t=start+rng.uniform(0,0.3); pan=rng.uniform(-0.8,0.8)
    g0=10**(rng.uniform(-10,0)/20); bright=rng.uniform(0.6,1.4)
    while t<stop:
      L=int(rng.uniform(0.02,0.04)*SR); e=np.exp(-np.arange(L)/(rng.uniform(0.003,0.007)*SR))
      e[:int(0.0015*SR)]*=np.linspace(0,1,int(0.0015*SR))
      b=sosfilt(sos,rng.standard_normal(L))*e
      b=b*bright+np.diff(np.r_[0,b])*(1-bright)*2
      fade=1.0 if t<stop-0.6 else max(0,(stop-t)/0.6)
      i=int(t*SR); g=g0*fade*rng.uniform(0.7,1.0)
      out[i:i+L,0]+=b*g*np.cos((pan+1)*np.pi/4); out[i:i+L,1]+=b*g*np.sin((pan+1)*np.pi/4)
      t+=1/rate*rng.uniform(0.85,1.15)
  return out
def mix(cat,seed,n_main=18,n_late=6,dur=2.8,clap_db=None,second_wave=(0.55,1.1),rate=(0.92,1.08),rt=0.55):
  rng=np.random.default_rng(seed); pool=takes(cat)
  byv={}
  for f in pool: byv.setdefault(voice_of(f),[]).append(f)
  vs=list(byv); rng.shuffle(vs)
  print(cat,"pool",len(pool),"voices",len(vs))
  out=np.zeros((int(dur*SR)+SR,2)); used=[]
  plan=[(v,rng.uniform(0,0.4)) for v in vs[:n_main]]
  plan+=[(v,rng.uniform(*second_wave)) for v in rng.choice(vs,n_late,replace=False)]
  for v,off in plan:
    f=rng.choice(byv[v]); y=load(f,rng,rate); used.append((os.path.basename(f),round(off,3)))
    dist=rng.uniform(0,1); g=10**((-2-10*dist+rng.uniform(-1.5,1.5))/20)
    if off>0.5: g*=0.75
    sos=butter(1,9000-5500*dist,fs=SR,output="sos"); y=sosfilt(sos,y)
    pan=rng.uniform(-0.85,0.85); i=int(off*SR)
    out[i:i+len(y),0]+=y*g*np.cos((pan+1)*np.pi/4); out[i:i+len(y),1]+=y*g*np.sin((pan+1)*np.pi/4)
  if clap_db is not None:
    c=claps(rng,dur+1); c*=10**(clap_db/20)/(np.sqrt((c**2).mean())+1e-9)*np.sqrt((out**2).mean())
    out+=c
  h=ir(rng,rt=rt); wet=np.stack([fftconvolve(out[:,k],h[:,k])[:len(out)] for k in range(2)],1)
  y=0.78*out+0.32*wet
  y=y[:int(dur*SR)]; fo=int(0.7*SR); y[-fo:]*=np.linspace(1,0,fo)[:,None]**2
  y[:int(0.005*SR)]*=np.linspace(0,1,int(0.005*SR))[:,None]
  y/=np.abs(y).max()/0.5
  fn=f"{O}/raw_{cat}.wav"; sf.write(fn,y,SR,subtype="PCM_24")
  json.dump(used,open(f"{O}/mixlog_{cat}.json","w"),indent=0); print(fn,len(used),"layers")
SEED_AWW=int(os.environ.get('SEED_AWW',48))
mix("cheer",31,clap_db=-13)
mix("aww",SEED_AWW,n_main=17,n_late=7,dur=2.6,second_wave=(0.5,1.3),rate=(0.85,1.0),rt=0.7)

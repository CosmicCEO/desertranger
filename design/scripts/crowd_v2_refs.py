# Kokoro energetic reference voices for Chatterbox cloning + excited Kokoro takes (speed 1.2-1.3, +1..+3 st)
import soundfile as sf, numpy as np, warnings, librosa, torch; warnings.filterwarnings("ignore")
torch.set_num_threads(4)
from kokoro import KPipeline
R="/workspace/boardgame/audio/samples/chatterbox/refs_crowd"; T="/workspace/boardgame/audio/samples/crowd/takes_v2"
TXT=("Yes! Yes! Did you see that? That was incredible! Oh my goodness, we actually did it! "
     "Come on, everybody, let's go! That's what I'm talking about! Unbelievable!")
REFS={"w_bella":("af_bella",+1.0),"w_nicole":("af_nicole",+2.0),"w_sky":("af_sky",+0.5),"w_emma":("bf_emma",-1.0),
      "w_kore":("af_kore",+2.5),"m_fenrir":("am_fenrir",-1.5),"m_puck":("am_puck",+1.0),"m_michael":("am_michael",0.0),
      "m_george":("bm_george",-2.5),"m_eric":("am_eric",+2.0)}
pipes={}
def kk(text,v,s):
  lc=v[0]
  if lc not in pipes: pipes[lc]=KPipeline(lang_code=lc, repo_id="hexgrad/Kokoro-82M")
  return np.concatenate([x.numpy() for _,_,x in pipes[lc](text,voice=v,speed=s)])
for k,(v,st) in REFS.items():
  a=kk(TXT,v,1.15); a=librosa.effects.pitch_shift(a,sr=24000,n_steps=st); a=a/np.abs(a).max()*0.9
  sf.write(f"{R}/{k}.wav",a,24000); print(k,round(len(a)/24000,2),flush=True)
# excited Kokoro takes
W={"cheer":["Yeah!!!","Woooo!!!","Huzzah!!!","Woo-hoo!!!","Yeah, baby!!!"],"aww":["Awwwwww!","Ooooohhh!","Oh no!!","Ohhhh nooo!"]}
rng=np.random.default_rng(5)
KV=["af_bella","af_nicole","af_sky","bf_emma","af_kore","af_heart","am_fenrir","am_puck","am_michael","bm_george","am_eric","am_liam"]
for v in KV:
  for cat,ws in W.items():
    for i,w in enumerate(ws):
      s=float(rng.choice([1.2,1.25,1.3])); st=float(rng.uniform(1,3))
      a=kk(w,v,s); a=librosa.effects.pitch_shift(a,sr=24000,n_steps=st)
      sf.write(f"{T}/k{cat}_{v}_w{i}_s{s}_p{st:.1f}.wav",a,24000)
  print("takes",v,flush=True)

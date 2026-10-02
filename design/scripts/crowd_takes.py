import soundfile as sf, numpy as np, os, warnings, sys
warnings.filterwarnings("ignore")
from kokoro import KPipeline
out="/workspace/boardgame/audio/samples/crowd/takes"
voices="af_alloy af_aoede af_bella af_heart af_jessica af_kore af_nicole af_nova af_river af_sarah af_sky am_adam am_echo am_eric am_fenrir am_liam am_michael am_onyx am_puck am_santa bf_alice bf_emma bf_isabella bf_lily bm_daniel bm_fable bm_george bm_lewis".split()
words={"cheer":["Yeah!","Yeahhh!","Woot!","Huzzah!","Woo!","Whoo-hoo!","Woo hoo!","Yeah! Woo!"],
       "aww":["Awww.","Aww!","Ooooh.","Oh no!","Ohhh.","Aww man.","Oh no.","Awww, no."]}
speeds=[0.8,1.0,1.2]
pipes={}; ok=[]; bad=[]
rng=np.random.default_rng(0)
for v in voices:
  lc=v[0]
  if lc not in pipes: pipes[lc]=KPipeline(lang_code=lc, repo_id="hexgrad/Kokoro-82M")
  try:
    for cat,ws in words.items():
      for i,w in enumerate(ws):
        for s in speeds:
          a=[x.numpy() if hasattr(x,'numpy') else x for _,_,x in pipes[lc](w,voice=v,speed=s)]
          if not a: continue
          a=np.concatenate(a)
          sf.write(f"{out}/{cat}_{v}_w{i}_s{s}.wav",a,24000)
    ok.append(v); print("ok",v,flush=True)
  except Exception as e:
    bad.append(v); print("FAIL",v,repr(e)[:200],flush=True)
print("OK",len(ok),ok); print("BAD",bad)

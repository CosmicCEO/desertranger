import torch, torchaudio as ta, warnings, time, glob, os, sys; warnings.filterwarnings("ignore")
torch.set_num_threads(4)
from chatterbox.tts import ChatterboxTTS
R="/workspace/boardgame/audio/samples/chatterbox/refs_crowd"; O="/workspace/boardgame/audio/samples/crowd/takes_v2"
m=ChatterboxTTS.from_pretrained(device="cpu")
texts={"cheer":["YEAH!!!","WOOOO!!!","Huzzah!!!","Woo-hoo!!!","Yeah, baby!!!","YEAH!!! WOOOO!!!"],
       "aww":["Awwwwww!","Ooooohhh!","Oh NO!!","Ohhhh nooo!","Awwwww, nooo!"]}
refs=sorted(glob.glob(f"{R}/*.wav"))
for ref in refs:
  rk=os.path.basename(ref)[:-4]
  for cat,ts in texts.items():
    for i,t in enumerate(ts):
      fn=f"{O}/cb{cat}_{rk}_w{i}.wav"
      if os.path.exists(fn): continue
      torch.manual_seed(100+i); t0=time.time()
      w=m.generate(t,audio_prompt_path=ref,exaggeration=1.0,cfg_weight=0.3)
      # guard against runaway generations
      w=w[:, :int(m.sr*3.0)]
      ta.save(fn,w,m.sr); print(fn,round(w.shape[-1]/m.sr,2),round(time.time()-t0,1),flush=True)

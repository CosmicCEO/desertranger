import torch, torchaudio as ta, warnings, time; warnings.filterwarnings("ignore")
torch.set_num_threads(4)
from chatterbox.tts import ChatterboxTTS
R="/workspace/boardgame/audio/samples/chatterbox/refs"; O="/workspace/boardgame/audio/samples/crowd/takes"
m=ChatterboxTTS.from_pretrained(device="cpu")
texts={"cheer":["Yeah! Woo!","Whoo-hoo! Yeah!","Huzzah!"],"aww":["Awww, no!","Ohhh no!","Aww man."]}
for ref in ["hr","rough","ranger"]:
  for cat,ts in texts.items():
    for i,t in enumerate(ts):
      torch.manual_seed(i+7); t0=time.time()
      w=m.generate(t,audio_prompt_path=f"{R}/{ref}.wav",exaggeration=1.0,cfg_weight=0.3)
      fn=f"{O}/cb{cat}_{ref}_w{i}.wav"; ta.save(fn,w,m.sr); print(fn,round(w.shape[-1]/m.sr,2),round(time.time()-t0,1),flush=True)

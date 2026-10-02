import torch, torchaudio as ta, warnings, time; warnings.filterwarnings("ignore")
from chatterbox.tts import ChatterboxTTS
R="/workspace/boardgame/audio/samples/chatterbox"
m=ChatterboxTTS.from_pretrained(device="cpu")
jobs=[("01","Grievance upheld.","refs/hr.wav",[(0.35,0.5),(0.5,0.5)]),
("02","Truck broke down. Have to tow it.","refs/rough_p.wav",[(0.6,0.4),(0.8,0.3)]),
("03","Backed into a cactus!","refs/ranger_p.wav",[(0.7,0.4),(0.9,0.3)])]
for k,t,ref,params in jobs:
  for ex,cfg in params:
    for seed in (1,2):
      torch.manual_seed(seed); t0=time.time()
      w=m.generate(t,audio_prompt_path=f"{R}/{ref}",exaggeration=ex,cfg_weight=cfg)
      fn=f"{R}/{k}_cb_ex{ex}_cfg{cfg}_seed{seed}.wav"; ta.save(fn,w,m.sr); print(fn, round(w.shape[-1]/m.sr,2),"s", round(time.time()-t0,1),"sec gen", flush=True)

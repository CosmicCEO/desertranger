import soundfile as sf, numpy as np, os, warnings
warnings.filterwarnings("ignore")
from kokoro import KPipeline
out="/workspace/boardgame/audio/samples/candidates"
lines={
 "01":("Grievance upheld.",["af_heart","af_bella","af_nicole","af_sarah","bf_emma","bf_isabella"],[0.85,0.95]),
 "02":("Truck broke down. Have to tow it.",["am_fenrir","am_onyx","am_michael","am_adam","am_eric","bm_george","bm_lewis"],[0.9,1.0]),
 "03":("Backed into a cactus!",["am_puck","am_echo","am_liam","am_eric","am_michael","bm_fable"],[1.1,1.2]),
}
pipes={}
for k,(text,voices,speeds) in lines.items():
  for v in voices:
    lc=v[0]
    if lc not in pipes: pipes[lc]=KPipeline(lang_code=lc, repo_id="hexgrad/Kokoro-82M")
    for s in speeds:
      audio=np.concatenate([a.numpy() if hasattr(a,'numpy') else a for _,_,a in pipes[lc](text,voice=v,speed=s)])
      fn=f"{out}/{k}_{v}_s{s}.wav"; sf.write(fn,audio,24000); print(fn, round(len(audio)/24000,2))

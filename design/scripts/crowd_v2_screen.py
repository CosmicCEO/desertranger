import librosa, numpy as np, glob, json, os, warnings; warnings.filterwarnings("ignore")
from faster_whisper import WhisperModel
m=WhisperModel("base.en",device="cpu",compute_type="int8",cpu_threads=4)
res={}
for f in sorted(glob.glob("/workspace/boardgame/audio/samples/crowd/takes_v2/*.wav")):
  y,sr=librosa.load(f,sr=16000); yt,_=librosa.effects.trim(y,top_db=35)
  segs,_=m.transcribe(np.pad(yt,(4000,4000)).astype(np.float32),beam_size=3,language="en")
  t="".join(s.text for s in segs).strip()
  res[os.path.basename(f)]={"dur":round(len(yt)/sr,2),"peak":float(np.abs(y).max()),"text":t}
  print(os.path.basename(f),res[os.path.basename(f)]["dur"],t,flush=True)
json.dump(res,open("/workspace/boardgame/audio/samples/crowd/takes_v2_screen.json","w"),indent=0)

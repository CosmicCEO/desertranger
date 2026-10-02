import librosa, numpy as np, glob, sys, os
from faster_whisper import WhisperModel
m=WhisperModel("base.en",device="cpu",compute_type="int8")
for f in sorted(glob.glob(sys.argv[1])):
  y,sr=librosa.load(f,sr=16000)
  f0,v,_=librosa.pyin(y,fmin=60,fmax=500,sr=sr)
  f0=f0[~np.isnan(f0)]
  segs,_=m.transcribe(y.astype(np.float32),beam_size=5); t="".join(s.text for s in segs).strip()
  print(f"{os.path.basename(f):32s} F0med={np.median(f0):6.1f}Hz F0sd={np.std(f0):5.1f} | {t}")

import subprocess,re,sys
def meas(f):
  o=subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",f,"-af","ebur128=peak=true","-f","null","-"],capture_output=True,text=True).stderr
  s=o[o.rfind("Summary"):]
  return float(re.search(r"I:\s+(-?[\d.]+)",s).group(1)),float(re.search(r"Peak:\s+(-?[\d.]+)",s).group(1))
for c in sys.argv[1:]:
  src=f"raw_{c}.wav"; I0,_=meas(src); g=-16-I0
  for it in range(8):
    af=f"volume={g:.2f}dB,aresample=192000,alimiter=limit=-2.2dB:attack=1.5:release=60:level=false,aresample=48000"
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",src,"-af",af,"-c:a","pcm_s24le",f"crowd-{c}.wav"],check=True)
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",f"crowd-{c}.wav","-c:a","libmp3lame","-b:a","192k",f"crowd-{c}.mp3"],check=True)
    I,P=meas(f"crowd-{c}.wav"); Im,Pm=meas(f"crowd-{c}.mp3")
    print(c,it,f"gain={g:.2f} wav I={I} TP={P} | mp3 I={Im} TP={Pm}")
    if abs(Im+16)<=0.2 and Pm<=-1.5: break
    g+= -16-Im

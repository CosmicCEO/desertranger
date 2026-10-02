import subprocess,re,sys
D="/workspace/boardgame/audio/samples/crowd"
def meas(f):
  o=subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",f,"-af","ebur128=peak=true","-f","null","-"],capture_output=True,text=True).stderr
  s=o[o.rfind("Summary"):]
  return float(re.search(r"I:\s+(-?[\d.]+)",s).group(1)),float(re.search(r"Peak:\s+(-?[\d.]+)",s).group(1))
TGT=-12.0
for c in sys.argv[1:]:
  src=f"{D}/raw_{c}_v2.wav"; I0,_=meas(src); g=TGT-I0; lim=-1.25
  for it in range(12):
    af=f"volume={g:.2f}dB,aresample=192000,alimiter=limit={lim}dB:attack=1:release=50:level=false,aresample=48000"
    w,m=f"{D}/crowd-{c}-v2.wav",f"{D}/crowd-{c}-v2.mp3"
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",src,"-af",af,"-c:a","pcm_s24le",w],check=True)
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",w,"-c:a","libmp3lame","-b:a","192k",m],check=True)
    I,P=meas(w); Im,Pm=meas(m)
    print(c,it,f"gain={g:.2f} lim={lim} wav I={I} TP={P} | mp3 I={Im} TP={Pm}",flush=True)
    if abs(Im-TGT)<=0.2 and Pm<=-1.0 and P<=-1.0: break
    if Pm>-1.0 or P>-1.0: lim-=0.3
    g+=TGT-Im

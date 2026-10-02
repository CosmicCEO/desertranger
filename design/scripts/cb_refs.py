import soundfile as sf, numpy as np, warnings; warnings.filterwarnings("ignore")
from kokoro import KPipeline
p=KPipeline(lang_code='a', repo_id="hexgrad/Kokoro-82M")
refs={"hr":("af_heart",0.9,"Thank you for your patience. After careful review of the submitted documentation, the committee has reached a decision. Please direct any further questions to the human resources portal."),
"rough":("am_fenrir",0.95,"Yeah, well, look, these things happen, buddy. The engine's shot, the tires are bald, and frankly I don't see it getting fixed anytime soon. Real shame."),
"ranger":("am_eric",1.15,"Oh gosh, okay, so, um, technically the trail is closed! I did put up a sign. Actually I put up three signs. Did nobody read the signs? Oh no.")}
for k,(v,s,t) in refs.items():
  a=np.concatenate([x.numpy() for _,_,x in p(t,voice=v,speed=s)]); sf.write(f"/workspace/boardgame/audio/samples/chatterbox/refs/{k}.wav",a,24000); print(k,len(a)/24000)

import json
S=4913/1024
sq=[
("Start","START","start",{},(195,610)),
("Go to Hawk Canyon","GO TO HAWK CANYON","goto",{"targetName":"Hawk Canyon"},(278,610)),
("Palm Canyon","PALM CANYON","plain",{},(355,615)),
("Promoted","PROMOTED GO TO SACRAMENTO","goto",{"targetName":"Sacramento","cue":"laugh"},(445,605)),
("Sandstone Canyon","SANDSTONE CANYON","plain",{},(490,555)),
("Turkey Track","TURKEY TRACK","plain",{},(520,480)),
("Cut Across Trail","LAND HERE AND YOU MAY USE CUT ACROSS TRAIL","shortcut",{"targetName":"Una Palma","optional":True,"exactLandingOnly":True,"cue":"laugh","note":"Orange arrow drawn from this square up across the path border into Una Palma (square 33). Shortcut target read from the art; arrow is clear."},(585,420)),
("Harper Flat","HARPER FLAT","plain",{},(670,430)),
("Coyote Canyon","COYOTE CANYON","plain",{},(690,490)),
("Vandalized Sign","VANDALIZED SIGN - GO BACK 1 SPACE","move",{"delta":-1,"cue":"sad"},(680,545)),
("Grapevine Canyon","GRAPEVINE CANYON","plain",{},(670,605)),
("Dos Cabezas","DOS CABEZAS","plain",{},(720,650)),
("Ocotillo Wells","OCOTILLO WELLS LOSE 1 TURN","loseTurn",{"turns":1,"cue":"sad","note":"Place square for Ocotillo Wells AND a lose-1-turn square; 'Go to Ocotillo Wells' (41) lands here."},(790,640)),
("Garage","GARAGE","plain",{},(880,650)),
("Off-Road Bust","YOU CATCH TWO OFF-ROAD MOTORCYCLES ~ ROLL AGAIN!","rollAgain",{"cue":"laugh"},(910,560)),
("Fault Wash","FAULT WASH","plain",{},(905,460)),
("No Extra Water","NO EXTRA DRINKING WATER GO BACK 6 SPACES","move",{"delta":-6,"cue":"sad"},(900,375)),
("Middle Willows","MIDDLE WILLOWS","plain",{},(895,290)),
("Vallecito","VALLECITO","plain",{},(895,210)),
("Arroyo Salado","ARROYO SALADO","plain",{},(895,145)),
("Hawk Canyon","HAWK CANYON","plain",{},(870,65)),
("Sacramento","SACRAMENTO","plain",{},(790,60)),
("Grievance Upheld","GRIEVANCE UPHELD MOVE AHEAD 10","move",{"delta":10,"cue":"laugh"},(720,55)),
("Vehicle Breaks Down","VEHICLE BREAKS DOWN GO BACK 10","move",{"delta":-10,"cue":"sad"},(665,50)),
("Sheep Canyon","SHEEP CANYON","plain",{},(610,50)),
("Tamarisk Grove","TAMARISK GROVE","plain",{},(545,55)),
("Found an Olla","YOU FOUND AN OLLA ROLL AGAIN","rollAgain",{"cue":"laugh"},(480,55)),
("VIP Ride Along","V.I.P. RIDE ALONG - BACK TO MIDDLE WILLOWS","goto",{"targetName":"Middle Willows","cue":"sad"},(395,65)),
("Supervisor on Vacation","MOVE AHEAD 5 SUPERVISOR ON VACATION","move",{"delta":5,"cue":"laugh"},(330,120)),
("Shooters Cited","SHOOTERS CITED - ROLL AGAIN","rollAgain",{"cue":"laugh"},(365,200)),
("Backing Accident","BACKING ACCIDENT LOSE 2 TURNS (OUCH!)","loseTurn",{"turns":2,"cue":"sad"},(470,205)),
("Affirmative Action","AFFIRMATIVE ACTION SAYS SWAP PLACES WITH ANOTHER PLAYER","swap",{"note":"Player chooses whom to swap with (see RULES-NOTES)."},(565,200)),
("Yaqui Pass","YAQUI PASS","plain",{},(630,250)),
("Una Palma","UNA PALMA","plain",{},(580,320)),
("Court","COURT","plain",{},(500,315)),
("Elephant Trees Stampede","ELEPHANT TREES ON STAMPEDE MOVE AHEAD 4 SPACES","move",{"delta":4,"cue":"laugh"},(420,315)),
("Schedule Changed","SCHEDULE CHANGED - LOSE 1 TURN","loseTurn",{"turns":1,"cue":"sad"},(340,315)),
("Bow Willow","BOW WILLOW","plain",{},(250,305)),
("17 Palms","17 PALMS","plain",{},(220,265)),
("Fish Creek","FISH CREEK","plain",{},(225,205)),
("Subpoena","SUBPOENA GO TO COURT","goto",{"targetName":"Court","cue":"sad"},(230,150)),
("Go to Ocotillo Wells","GO TO OCOTILLO WELLS","goto",{"targetName":"Ocotillo Wells","cue":"sad","chainsTo":"loseTurn","note":"Target (12) is itself a lose-1-turn square, so this is effectively go back 29 + lose 1 turn unless the rule says otherwise."},(230,85)),
("Stuck in Pinyon","STUCK IN PINYON DROP OFF LOSE 1 TURN","loseTurn",{"turns":1,"cue":"sad"},(150,100)),
("Fonts Point","FONTS POINT","plain",{"note":"Written 'FONTS POINT' (real place: Font's Point)."},(115,135)),
("Reports Overdue","REPORTS OVERDUE ROLL DICE AND GO BACK # SHOWN","dice",{"rule":"rollAndMoveBack","cue":"sad"},(110,180)),
("Barrel Springs","BARREL SPRINGS","plain",{},(105,225)),
("Cholla Flat Tire","CHOLLA CAUSES FLAT TIRE LOSE 1 TURN","loseTurn",{"turns":1,"cue":"sad"},(110,285)),
("Sunset Mountain","SUNSET MOUNTAIN","plain",{},(95,350)),
("Sheep Canyon Closure","SHEEP CANYON CLOSURE - GO BACK 9","move",{"delta":-9,"cue":"sad","note":"Not a goto: it names Sheep Canyon but the effect is simply go back 9 (lands on Fish Creek, 39)."},(95,415)),
("Go to 17 Palms","GO TO 17 PALMS","goto",{"targetName":"17 Palms","cue":"sad"},(90,475)),
("Ground Fire Report","REPORT OF A GROUND FIRE AT ARROYO SALADO - GO CHECK!","goto",{"targetName":"Arroyo Salado","cue":"sad"},(85,550)),
("Finish","FINISH !!!","finish",{"cue":"win"},(85,640)),
]
names={n:i for i,(n,*_) in enumerate(sq)}
out=[]
for i,(n,t,ty,ex,(x,y)) in enumerate(sq):
    d={"i":i,"name":n,"text":t,"type":ty}
    ex=dict(ex)
    if ty in("goto","shortcut"):
        d["target"]=names[ex["targetName"]]
    if ty=="move": d["target"]=i+ex["delta"]
    d.update(ex)
    d["x"]=round(x*S); d["y"]=round(y*S); d["xy"]="approx"
    out.append(d)
# ambiguity notes
out[1]["note"]="Hawk Canyon appears only once as a place square (20)."
out[3]["note"]="Sacramento place square is 21 (adjacent to Hawk Canyon)."
out[27]["note"]="Middle Willows place square is 17 (goes backward 10)."
out[38]["note"]="Not to be confused with Palm Canyon (2) or Una Palma (33)."
out[49]["note"]="17 Palms place square is 38 (go back 11). Not Palm Canyon (2)."
out[50]["note"]="Arroyo Salado place square is 19 (go back 31) - harsh, one square before FINISH."
out[24]["note"]="Only Sheep Canyon place square; square 48 'Sheep Canyon closure' is a go-back-9, not a goto."
b={"id":"desert-ranger","title":"Desert Ranger","die":{"sides":6},"art":"art/desert-ranger-photo.jpg",
   "artSize":{"original":[4913,3583],"xyCoordinateSpace":"original photo pixels; approximate centers, to be re-traced"},
   "squares":out}
json.dump(b,open('board/desert-ranger.json','w'),indent=2)
for d in out: print(d["i"],d["name"],d["type"],d.get("target",""))

"""One-off: writes data/sessions/S{1,2,3}.transcript.jsonl and .gold.json from the dialogue below.
Speakers: T = therapist, P = patient. ts in seconds from the start of the visit."""
import json
import sys
from pathlib import Path

OUT = Path(sys.argv[1])

S1 = [
    (5, "T", "Good morning. Come in and take a seat. How has the knee been since last week?"),
    (14, "P", "Better on most days. Stairs are still the hardest part, and after a long walk it aches in the evening."),
    (26, "T", "That fits with what we saw last time. Did you manage the exercises from the first visit?"),
    (35, "P", "Some of them. Honestly, I was not sure how many to do, so I did a little of everything."),
    (46, "T", "That's very common. Today we'll make a short, clear list, and you'll get it written down so there is no guessing."),
    (57, "P", "Good. My daughter reads English well, but I would prefer to have it in Arabic."),
    (66, "T", "We can do that. The program will be in Arabic. Let me first check how the knee moves today."),
    (90, "T", "Can you bend the right knee as far as is comfortable? Good. And straighten it. Any pain at the end?"),
    (104, "P", "A little pulling at the front when it is fully straight, nothing sharp."),
    (125, "T", "Fine. Now stand up from this chair without using your hands, and sit down slowly."),
    (140, "P", "Like this? It is easier than last week."),
    (152, "T", "Much better. That will be the first exercise at home: standing up from a chair without your hands and sitting down slowly."),
    (164, "T", "Do three sets of ten, every day."),
    (172, "P", "Three sets of ten. With a rest in between?"),
    (179, "T", "Yes, rest a little between the sets."),
    (205, "T", "Next, the band. Sit on a chair, put the band around your right ankle, and straighten the knee slowly against it."),
    (218, "P", "The green band you gave me?"),
    (224, "T", "That one. Do three sets of twelve on the right leg, every other day."),
    (236, "T", "And breathe out as you straighten the knee. With your blood pressure, I don't want you holding your breath."),
    (248, "P", "I take my tablets every morning. The pressure has been fine."),
    (256, "T", "Good. Just keep breathing out on the effort."),
    (290, "T", "Third, the stairs. At home you have stairs up to the bedroom, right?"),
    (298, "P", "Yes, fourteen steps."),
    (306, "T", "Then use the bottom step. Step up leading with your right leg, then step down. Two sets of ten, every day."),
    (320, "T", "Always hold the stair rail when you do it."),
    (330, "P", "That is the one I feel most."),
    (337, "T", "That's why it's on the list. It should get easier week by week."),
    (370, "T", "Now walking. Walking is good for this knee. I'd like you to walk for twenty minutes, five days a week."),
    (384, "P", "Twenty minutes in one go? Last week I stopped after ten."),
    (393, "T", "In one go if you can. You can walk slowly."),
    (403, "T", "Some knee pain while walking is acceptable, as long as it has settled by the next morning."),
    (415, "P", "That is good to know. I was afraid any pain meant I was damaging the knee."),
    (426, "T", "That's a common worry. Some pain is expected with this knee."),
    (460, "T", "Last one, the calf. Stand facing the wall with your right leg behind you, heel on the floor, and lean forward until you feel the stretch."),
    (476, "T", "Hold it for thirty seconds, three times, every day."),
    (486, "P", "Only the right leg?"),
    (490, "T", "Only the right."),
    (540, "P", "So, five things."),
    (548, "T", "Five things: standing up from the chair, the band, the step, walking and the calf stretch. I'll check the written program before you leave."),
    (600, "P", "Thank you. Same time next week?"),
    (606, "T", "Same time next week. Bring the band so we can check the colour."),
]
S1_GOLD = {"S1.1": [12, 13], "S1.2": [16, 18, 19], "S1.3": [24, 25], "S1.4": [28, 31], "S1.5": [34, 35, 37]}

S2 = [
    (5, "T", "Hi, good to see you. How are you getting on with the new prosthesis?"),
    (14, "P", "Better. I wear it in the mornings and in the gym here. At home I still use the crutches mostly."),
    (26, "T", "That's what we agreed for now. How is the skin at the end of the leg?"),
    (35, "P", "It is okay. A little red after the gym, then it goes away."),
    (44, "T", "Good, that sounds normal for this stage."),
    (55, "P", "One thing. Can I get the exercises written in Ukrainian? I understand English when we talk, but at home I forget the details."),
    (68, "T", "Yes, you'll get the program in Ukrainian. Let's go through it."),
    (95, "T", "First, lying on your stomach. It keeps the hip straight, which matters a lot when you sit so much."),
    (106, "T", "Lie on your stomach for ten minutes, twice a day."),
    (115, "P", "On the bed is okay?"),
    (119, "T", "On the bed is fine."),
    (150, "T", "Second, the bridge. Last time we did it with both legs, but for now do it only on the right leg."),
    (163, "T", "Lie on your back, right knee bent, the left leg straight, and lift your hips. Three sets of ten, every day."),
    (176, "P", "Only the right."),
    (180, "T", "Only the right for now."),
    (215, "T", "Third, on your side. Lie on your right side and lift the left leg straight up, then lower it slowly."),
    (228, "T", "Three sets of twelve, every day."),
    (236, "P", "That one is hard. The leg feels light and heavy at the same time."),
    (246, "T", "That's normal at this stage. The muscles are learning again."),
    (285, "T", "Fourth, the band. Sit on a chair with the band around the left leg just below the knee, and straighten the knee against it."),
    (298, "T", "Three sets of twelve, every day, on the left."),
    (305, "P", "Okay."),
    (340, "T", "And the last one. You've been standing on the prosthesis alone here in the gym, and it's going well."),
    (350, "P", "Yes, I can do almost a minute now."),
    (360, "T", "So let's add it at home too. Stand on the left leg with the prosthesis on, three times thirty seconds, every day."),
    (373, "T", "Stand next to the kitchen counter so you can grab it."),
    (382, "P", "At home, alone?"),
    (387, "T", "Yes. Next to the counter you can hold on if you need to."),
    (420, "P", "The prosthetist sees me again on Thursday, for the socket."),
    (428, "T", "Good, tell them how the gym sessions have gone."),
    (470, "T", "So that's five exercises: lying on your stomach, the bridge on the right, the side leg lift on the left, the band on the left, and standing on the prosthesis."),
    (486, "P", "Five. Good."),
    (540, "T", "You're doing well. See you next week, same time."),
    (548, "P", "Thank you. See you next week."),
]
S2_GOLD = {"S2.1": [8, 9], "S2.2": [12, 13, 15], "S2.3": [16, 17], "S2.4": [20, 21], "S2.5": [23, 25, 26]}

S3 = [
    (5, "T", "Hello, welcome. This is your first visit, so tell me about the shoulder."),
    (16, "P", "It is the right shoulder. For two months it hurts when I lift my arm, for example to the kitchen shelf."),
    (29, "T", "Does it hurt at night?"),
    (34, "P", "Sometimes, if I lie on that side."),
    (44, "T", "I see from your papers that you also have osteoporosis, and you take medicine for it."),
    (53, "P", "Yes, for some years now."),
    (70, "T", "Thank you. Let me look at the shoulder. Lift your right arm forward as far as is comfortable."),
    (82, "P", "Here it starts to hurt."),
    (92, "T", "Okay, just below shoulder height. And turning the arm out, like this? Good, that's stronger than I expected."),
    (106, "P", "My son wanted me to have the exercises in Arabic. He will not be there every day."),
    (114, "T", "Of course, you'll get them in Arabic."),
    (140, "T", "The first exercise is the pendulum. Lean on the table with your left hand, and let the right arm hang and swing gently in small circles."),
    (154, "T", "One minute, three times a day."),
    (162, "P", "Only small circles?"),
    (167, "T", "Small and relaxed. The arm just hangs."),
    (195, "T", "The second one is with the band, for the right arm. Keep your elbow tucked in against your side, and turn the forearm outwards against the band."),
    (210, "T", "Three sets of ten, every day."),
    (217, "P", "Tucked in?"),
    (222, "T", "Close to your body, as if you were holding a newspaper under your arm."),
    (250, "T", "Third, rowing with the band. Hold the band with both hands and pull it towards you, squeezing the shoulder blades together."),
    (262, "T", "Two sets of fifteen, every day."),
    (274, "P", "My back is stiff as well. Every morning I do sit-ups for my stomach."),
    (284, "T", "Let's leave the sit-ups out for now. With osteoporosis I don't want you curling the back forward against weight."),
    (297, "P", "Okay. The back of my legs is tight too, from sitting."),
    (306, "T", "Then add the stretch for the back of the thigh. Sit, straighten the leg in front of you, lean forward from the hips, and hold it for a while."),
    (320, "P", "Okay."),
    (345, "T", "Lifting the arm up the wall, the wall slides, we will add when the pain settles. Not yet."),
    (356, "P", "So not the wall now."),
    (361, "T", "Not now. Maybe at the next visit."),
    (400, "T", "So at home: the pendulum, the band turning outwards, the rowing, and the stretch for the back of the thigh."),
    (414, "P", "Four. Good, I can do that."),
    (422, "T", "We'll see how it has gone next week."),
    (430, "P", "Thank you, doctor."),
    (434, "T", "I'm a physiotherapist, but you're welcome. See you next week."),
]
S3_GOLD = {"S3.1": [12, 13], "S3.2": [16, 17], "S3.3": [20, 21], "S3.4": [24, 25], "T3.1": [27, 29], "T3.2": [22, 23]}
S3_STATUS = {"T3.1": "deferred", "T3.2": "withdrawn"}

SPEAKER = {"T": "therapist", "P": "patient"}


def write(sid: str, dialogue, gold, status=None):
    status = status or {}
    lines = [json.dumps({"span_id": f"s{n:03d}", "speaker": SPEAKER[sp], "ts": ts, "text": text}, ensure_ascii=False)
             for n, (ts, sp, text) in enumerate(dialogue, start=1)]
    (OUT / f"{sid}.transcript.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    g = {"_note": "Answer key: the spans that state each slot (and each trap). Ground truth for tests and the evaluation.",
         "session_id": sid,
         "items": [{"slot": slot, "span_ids": [f"s{n:03d}" for n in spans], "status": status.get(slot, "prescribed")}
                   for slot, spans in gold.items()]}
    (OUT / f"{sid}.gold.json").write_text(json.dumps(g, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


write("S1", S1, S1_GOLD)
write("S2", S2, S2_GOLD)
write("S3", S3, S3_GOLD, S3_STATUS)
print("written")

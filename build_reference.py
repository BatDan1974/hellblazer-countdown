#!/usr/bin/env python3
"""Build data/reference.csv: Issue, Era/run, Summary (spoiler-free draft).

Era is derived from issue ranges (the headline writer runs) and cross-checked
against the CLZ Writer column. Summaries are written here by hand, spoiler-free,
premise-level, in my own words - a starting draft for the user to overwrite.
Lines tagged (verify) are lower-confidence tone-level drafts, not confident plot.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLZ = ROOT / "data" / "clz.csv"
OUT = ROOT / "data" / "reference.csv"

# Headline runs by issue range (guest/fill-in issues keep their era's label).
ERA_RANGES = [
    (1, 40, "Delano"), (41, 83, "Ennis"), (84, 84, "Delano (one-shot)"),
    (85, 88, "Eddie Campbell"), (89, 128, "Jenkins"), (129, 133, "Ennis (Son of Man)"),
    (134, 143, "Ellis"), (144, 145, "Darko Macan"), (146, 174, "Azzarello"),
    (175, 215, "Carey"), (216, 229, "Mina"), (230, 249, "Diggle"), (250, 300, "Milligan"),
]
# surname we expect to see in the Writer field for a non-guest issue in that run
ERA_WRITER = {
    "Delano": "Delano", "Ennis": "Ennis", "Delano (one-shot)": "Delano",
    "Eddie Campbell": "Campbell", "Jenkins": "Jenkins", "Ennis (Son of Man)": "Ennis",
    "Ellis": "Ellis", "Darko Macan": "Macan", "Azzarello": "Azzarello",
    "Carey": "Carey", "Mina": "Mina", "Diggle": "Diggle", "Milligan": "Milligan",
}


def era_of(n: int) -> str:
    for lo, hi, label in ERA_RANGES:
        if lo <= n <= hi:
            return label
    return ""


ARC = {
    "The Fear Machine": "John falls in with a group of New Age travellers and uncovers a plot to harvest human fear.",
    "The Family Man": "A methodical serial killer and John's own poisonous family history close in on him at once.",
    "Dangerous Habits": "Diagnosed with terminal lung cancer, John hunts for a supernatural way to cheat his fate.",
    "Royal Blood": "A demon loose among Britain's establishment leaves a trail of murder for John to chase.",
    "Guys and Dolls": "Old debts and old lovers resurface as John's past refuses to stay buried. (verify)",
    "Fear and Loathing": "Trying for a quiet life in London with Kit, John finds old enemies won't let him rest.",
    "Damnation's Flames": "John is dragged through a nightmarish, hallucinatory vision of America. (verify)",
    "Rake At the Gates of Hell": "The First of the Fallen comes for everyone John loves - the end of Ennis's run.",
    "Warped Notions": "An Eddie Campbell story that pushes John somewhere stranger than his usual haunts. (verify)",
    "Critical Mass": "The bill for John's soul comes due as his past bargains with Hell catch up with him.",
    "Difficult Beginnings": "A Jenkins story reaching back into John's roots and early life. (verify)",
    "In the Line of Fire": "John is caught up in buried trauma and old debts, Jenkins-style. (verify)",
    "Last Man Standing": "John's friends and enemies converge in a tense Jenkins arc. (verify)",
    "Widdershins": "A folkloric, backwards-turning Jenkins tale as John's luck sours. (verify)",
    "Up the Down Staircase": "John navigates a haunting that works against the natural order. (verify)",
    "How To Play With Fire": "Jenkins builds toward the 100th issue as John's past bargains flare up. (verify)",
    "Son of Man": "A gangland favour John did years ago - raising a crime boss's dead son - comes back wrong.",
    "Haunted": "John sets out to hunt the person who brutally murdered a former lover.",
    "Ashes & Honey": "A Darko Macan story picking at guilt and consequence in John's wake. (verify)",
    "Hard Time": "John lands in a brutal American maximum-security prison and has to survive it.",
    "Good Intentions": "In a backwoods American town, John stumbles onto buried secrets and homegrown horror.",
    "Freezes Over": "Snowbound in a roadside diner, a trapped group faces a killer out of urban legend.",
    "Lapdogs and Englishmen": "Azzarello sends John down another dark corner of his American road. (verify)",
    "Highwater": "John collides with a violent white-supremacist movement at the end of his US exile.",
    "Ashes & Dust In the City of Angels": "John's American journey reaches Los Angeles for a brutal reckoning.",
    "High On Life": "Back on home ground, John eases into a new era with a death and a favour owed. (verify)",
    "Red Sepulchre": "Back in London, John is drawn toward a dangerous artefact and a powerful family.",
    "Black Flowers": "A Carey story where John's past work returns to demand its price. (verify)",
    "Third Worlds": "John's dealings carry him beyond London into wider, darker territory. (verify)",
    "Bred In the Bone": "Family and inheritance, magical and otherwise, press in on John. (verify)",
    "Staring At the Wall": "An apocalyptic threat stirs as John senses something vast and wrong drawing near.",
    "Out of Season": "A darkly comic Carey detour into the fallout of John's reputation. (verify)",
    "Stations of the Cross": "Hungover and hunted, John stumbles through a pilgrimage of his own sins.",
    "Reasons To Be Cheerful": "John's luck, loves and enemies tangle as Carey's run builds. (verify)",
    "Down In the Ground Where the Dead Men Go": "A long Carey arc pulling John toward the dead and his debts to them. (verify)",
    "R.S.V.P.": "Invitations and old obligations come due as Carey's run closes out. (verify)",
    "Empathy Is the Enemy": "A contagion of raw empathy spreads through Britain, and John is caught in it.",
    "The Red Right Hand": "Mina's run closes as the true cost of that empathy plague is counted. (verify)",
    "In At the Deep End": "Diggle takes over as John throws himself back into dangerous magic. (verify)",
    "Wheels of Chance, Systems of Control": "Chance, control and a con drive a tense Diggle two-parter. (verify)",
    "Joy Ride": "A nastier, pulpier John as Diggle sends him into fresh trouble. (verify)",
    "The Laughing Magician": "John's reputation as a trickster-magician is put to a serious test. (verify)",
    "The Mortification of the Flesh": "John pays a painful toll as Diggle tightens the screws. (verify)",
    "Newcastle Calling": "Jason Aaron revisits the infamous Newcastle disaster that scarred John for life.",
    "The Roots of Coincidence": "Diggle's run races to a climax as John's schemes converge. (verify)",
    "Scab": "Milligan opens his run at a picket line where something is badly, supernaturally wrong. (verify)",
    "Regeneration": "John picks up the pieces as Milligan's era settles in. (verify)",
    "Hooked": "John falls hard for a much younger woman, Epiphany, and the trouble that brings.",
    "India": "John travels to India, chasing love, guilt and a fresh kind of trouble.",
    "No Future": "Punk nostalgia turns dangerous as John's past catches up on the London scene. (verify)",
    "Sectioned": "John's mind and history are put under siege in a tense Milligan arc. (verify)",
    "Bloody Carnations": "John and Epiphany head toward a wedding that half of Hell wants to stop.",
    "Phantom Pains": "Old wounds and the Constantine family flare up around John. (verify)",
    "The Devil's Trench Coat": "John's iconic coat takes on a malign life of its own. (verify)",
    "Another Season In Hell": "Grief and self-destruction drag John toward a bleak low point. (verify)",
    "The Curse of the Constantines": "The family curse closes in as Milligan's run nears its end. (verify)",
    "Death and Cigarettes": "The final arc: every debt, enemy and regret converges on John's last stand.",
}

OVERRIDE = {
    1: "John faces a hungry spirit loose in New York - the debut of his solo series.",
    2: "John confronts a demon feeding on 1980s greed and ambition. (verify)",
    3: "A politically charged early standalone as John runs a con on the powerful. (verify)",
    27: "Neil Gaiman's one-off: John tries to help a frightened, lonely ghost. A fan favourite.",
    40: "Delano's farewell issue, closing out the founding era of the series.",
    51: "A John Smith guest issue slotted into the Ennis run. (verify)",
    63: "The first issue published under the Vertigo imprint.",
    84: "A one-off return by Jamie Delano after his main run. (verify)",
    100: "A double-size 100th-issue milestone reflecting on John's life and losses.",
    200: "The 200th-issue milestone, 'Happy Families', during Azzarello's American run.",
    250: "An all-star 250th-issue anniversary with a line-up of guest writers and artists.",
    300: "The final issue - the end of John Constantine's original 300-issue run.",
}


def main():
    rows = {int(r["Issue"]): r for r in csv.DictReader(open(CLZ, encoding="utf-8-sig"))}
    arc_lookup = {k.lower(): v for k, v in ARC.items()}  # case-insensitive (CLZ capitalisation varies)
    # part numbers: order issues that share an arc name, matched case-insensitively
    arc_members: dict[str, list[int]] = {}
    for n in sorted(rows):
        arc = rows[n]["Story arc"].strip().lower()
        if arc:
            arc_members.setdefault(arc, []).append(n)

    out = []
    missing_arc, mismatches = [], []
    for n in range(1, 301):
        r = rows[n]
        arc = r["Story arc"].strip()
        writer = r["Writer"].strip()
        era = era_of(n)
        # era sanity check
        exp = ERA_WRITER.get(era, "")
        if exp and exp not in writer:
            mismatches.append((n, era, writer))

        if n in OVERRIDE:
            summ = OVERRIDE[n]
        elif arc and arc.lower() in arc_lookup:
            summ = arc_lookup[arc.lower()]
            members = arc_members[arc.lower()]
            if len(members) > 1:
                summ = f"{summ} (Pt {members.index(n) + 1}/{len(members)})"
        elif arc:
            summ = f"'{arc}': {writer} arc - spoiler-free draft to add."
            missing_arc.append(arc)
        else:
            summ = f"Standalone {writer} issue - spoiler-free draft to add."
        out.append({"Issue": n, "Era/run": era, "Summary (spoiler-free, draft)": summ})

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Issue", "Era/run", "Summary (spoiler-free, draft)"])
        w.writeheader()
        w.writerows(out)

    print("wrote", len(out), "rows ->", OUT)
    print("era mismatches (expected at guest issues):", mismatches)
    print("arcs with no written premise:", sorted(set(missing_arc)))
    verify = sum(1 for o in out if "(verify)" in o["Summary (spoiler-free, draft)"])
    draft = sum(1 for o in out if "draft to add" in o["Summary (spoiler-free, draft)"])
    print(f"lines tagged (verify): {verify} | templated 'draft to add': {draft} | confident: {300 - verify - draft}")
    for n in (1, 14, 41, 146, 250, 300):
        print(n, "|", out[n - 1]["Era/run"], "|", out[n - 1]["Summary (spoiler-free, draft)"])


if __name__ == "__main__":
    main()

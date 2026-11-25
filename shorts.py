#!/usr/bin/env python3
"""
Build a vertical (1080x1920) YouTube Short recapping a block of 5 issues.

  python shorts.py --milestone 5                 # recap issues 1-5
  python shorts.py --milestone 10 --source ...   # recap issues 6-10

It reuses the per-issue cards already in public/posts/ plus a generated
intro and a recap outro (with the running Constantine body-count), then
encodes to public/shorts/hb-001-005.mp4 with Ken Burns motion + crossfades.

No audio is baked in — add a music track in the YouTube app when you upload
(baking in commercial tracks risks a Content ID claim on YouTube).
"""
from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

import countdown as C

SW, SH = 1080, 1920
SHORTS_DIR = C.ROOT / "public" / "shorts"
FPS = 30
D_INTRO, D_ISSUE, D_OUTRO, XFADE = 2.6, 4.8, 4.8, 0.5


# --------------------------------------------------------------------------- frame helpers

def vgrad() -> Image.Image:
    grad = Image.linear_gradient("L").resize((SW, SH))
    bg = ImageOps.colorize(grad, black=C.BG_TOP, white=C.BG_BOTTOM).convert("RGB")
    noise = Image.effect_noise((SW, SH), 38).convert("RGB")
    bg = Image.blend(bg, noise, 0.045)
    vig = Image.radial_gradient("L").resize((SW, SH))
    vig = vig.point(lambda v: int(max(0, v - 90) * 0.9))
    bg.paste((0, 0, 0), mask=vig)
    return bg.convert("RGBA")


def shadowed(img: Image.Image, card: Image.Image, x: int, y: int, radius: int = 26) -> None:
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    block = Image.new("RGBA", card.size, (0, 0, 0, 170))
    sh.paste(block, (x, y + 10))
    sh = sh.filter(ImageFilter.GaussianBlur(radius))
    img.alpha_composite(sh)
    img.alpha_composite(card.convert("RGBA"), (x, y))


def save(img: Image.Image, path: Path) -> Path:
    img.convert("RGB").save(path, "JPEG", quality=94, subsampling=0)
    return path


# --------------------------------------------------------------------------- frames

def intro_frame(cfg: dict, lo: int, hi: int, days: int, tmp: Path) -> Path:
    img = vgrad()
    d = ImageDraw.Draw(img)
    C.badge(img, SW // 2 - 110, 300, 220)
    d = ImageDraw.Draw(img)
    C.draw_tracked(d, SW / 2, 690, cfg["series"], C.font(C.ANTON, 104), C.WHITE, 6, "center")
    C.draw_tracked(d, SW / 2, 748, "40TH ANNIVERSARY COUNTDOWN", C.font(C.SEMI, 30), C.BLUE, 5, "center")
    # "THE FIRST FIVE" / "ISSUES lo-hi"
    label = "THE FIRST FIVE" if lo == 1 else "THE NEXT FIVE"
    C.glow_text(img, (SW / 2 - C.tracked_width(label, C.font(C.ANTON, 92), 2) / 2, 980),
                label, C.font(C.ANTON, 92), C.WHITE, C.BLUE, radius=24)
    d = ImageDraw.Draw(img)
    C.draw_tracked(d, SW / 2, 1070, f"ISSUES {lo}–{hi}", C.font(C.BOLD, 46), C.MUTED, 4, "center")
    # days-to-go
    num = str(days)
    f_num = C.font(C.ANTON, 200)
    C.glow_text(img, (SW / 2 - f_num.getlength(num) / 2, 1430), num, f_num, C.WHITE, C.BLUE, radius=26)
    d = ImageDraw.Draw(img)
    C.draw_tracked(d, SW / 2, 1500, "DAYS TO GO", C.font(C.ANTON, 50), C.BLUE, 4, "center")
    C.draw_tracked(d, SW / 2, 1552, "UNTIL #1 TURNS 40", C.font(C.SEMI, 30), C.MUTED, 3, "center")
    return save(img, tmp / "00_intro.jpg")


def issue_frame(cfg: dict, row: dict, card_path: Path, idx: int, total_in_block: int, tmp: Path) -> Path:
    img = vgrad()
    d = ImageDraw.Draw(img)
    # header
    C.badge(img, 56, 70, 96)
    d = ImageDraw.Draw(img)
    C.draw_tracked(d, 176, 118, cfg["series"], C.font(C.ANTON, 44), C.WHITE, 4)
    C.draw_tracked(d, 178, 150, f"RECAP · {idx} OF {total_in_block}", C.font(C.SEMI, 26), C.BLUE, 4)
    # card
    card = Image.open(card_path).convert("RGBA")
    cw = 1000
    card = card.resize((cw, round(card.height * cw / card.width)), Image.LANCZOS)
    cx, cy = (SW - cw) // 2, 232
    shadowed(img, card, cx, cy)
    d = ImageDraw.Draw(img)
    # running-tally footer (the body-count builds across the five)
    fy = cy + card.height + 54
    d.line((80, fy, SW - 80, fy), fill=C.PANEL_LINE, width=2)
    C.draw_tracked(d, SW / 2, fy + 58, "RUNNING TALLY", C.font(C.SEMI, 28), C.MUTED, 6, "center")
    ny = fy + 158  # number baseline, well clear of the label
    f_num = C.font(C.ANTON, 72)
    flame, cig = C.flame_icon(64), C.cigarette_icon(104, 64)
    img.alpha_composite(flame, (268, ny - 64))
    d = ImageDraw.Draw(img)
    d.text((348, ny), f"{row['friends_total']}", font=f_num, fill=C.WHITE, anchor="ls")
    img.alpha_composite(cig, (604, ny - 56))
    d = ImageDraw.Draw(img)
    d.text((724, ny), f"{row['cigs_total']}", font=f_num, fill=C.WHITE, anchor="ls")
    return save(img, tmp / f"{idx:02d}_issue{row['issue']:03d}.jpg")


def outro_frame(cfg: dict, issues: list[dict], days: int, tmp: Path) -> Path:
    total = cfg["total_issues"]
    hi = issues[-1]["issue"]
    img = vgrad()
    d = ImageDraw.Draw(img)
    C.badge(img, SW // 2 - 96, 150, 192)
    d = ImageDraw.Draw(img)
    C.draw_tracked(d, SW / 2, 470, f"{hi} DOWN", C.font(C.ANTON, 110), C.WHITE, 4, "center")
    C.draw_tracked(d, SW / 2, 540, f"{total - hi} TO GO", C.font(C.BOLD, 52), C.BLUE, 4, "center")
    # recap tally
    f_tot = issues[-1]["friends_total"]
    c_tot = issues[-1]["cigs_total"]
    d.line((110, 648, SW - 110, 648), fill=C.PANEL_LINE, width=2)
    C.draw_tracked(d, SW / 2, 716, "THE TALLY SO FAR", C.font(C.SEMI, 32), C.MUTED, 6, "center")

    def stat_block(base_y: int, icon: Image.Image, number, label: str) -> None:
        f = C.font(C.ANTON, 120)
        s = str(number)
        nw = f.getlength(s)
        gap = 30
        x0 = (SW - (icon.width + gap + nw)) / 2
        img.alpha_composite(icon, (int(x0), int(base_y - icon.height + 6)))
        dd = ImageDraw.Draw(img)
        dd.text((x0 + icon.width + gap, base_y), s, font=f, fill=C.WHITE, anchor="ls")
        C.draw_tracked(dd, SW / 2, base_y + 48, label, C.font(C.SEMI, 30), C.EMBER, 3, "center")

    stat_block(848, C.flame_icon(92), f_tot, "FRIENDS BURNED")
    stat_block(1060, C.cigarette_icon(150, 92), c_tot, "CIGARETTES SMOKED")
    d = ImageDraw.Draw(img)
    # pick of the five
    scored = [r for r in issues if r.get("score") is not None]
    if scored:
        best = max(scored, key=lambda r: r["score"])
        d.line((110, 1180, SW - 110, 1180), fill=C.PANEL_LINE, width=2)
        C.draw_tracked(d, SW / 2, 1248, "PICK OF THE FIVE", C.font(C.SEMI, 32), C.MUTED, 6, "center")
        star_size, gap = 58, 12
        star_w = 5 * star_size + 4 * gap
        C.draw_stars(img, int((SW - star_w) / 2), 1296, best["score"], size=star_size, gap=gap)
        d = ImageDraw.Draw(img)
        C.draw_tracked(d, SW / 2, 1430, f"#{best['issue']}   ·   {best['score']:g}/5",
                       C.font(C.BOLD, 50), C.GOLD, 2, "center")
    # CTA
    C.draw_tracked(d, SW / 2, 1560, "DAILY COUNTDOWN", C.font(C.SEMI, 30), C.MUTED, 5, "center")
    C.draw_tracked(d, SW / 2, 1618, cfg["handle"], C.font(C.ANTON, 60), C.BLUE, 2, "center")
    C.draw_tracked(d, SW / 2, 1716, "FULL REVIEWS ON YOUTUBE · BATDAN", C.font(C.SEMI, 30), C.MUTED, 4, "center")
    return save(img, tmp / "99_outro.jpg")


# --------------------------------------------------------------------------- encode

def encode(frames: list[Path], durations: list[float], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    inputs: list[str] = []
    for f, d in zip(frames, durations):
        inputs += ["-loop", "1", "-t", f"{d:.3f}", "-i", str(f)]
    parts = []
    for i, d in enumerate(durations):
        parts.append(
            f"[{i}:v]scale={SW}:{SH},fps={FPS},setsar=1,format=yuv420p[v{i}]"
        )
    # xfade chain
    label = "v0"
    running = durations[0]
    for i in range(1, len(durations)):
        off = running - XFADE
        new = f"x{i}"
        parts.append(f"[{label}][v{i}]xfade=transition=fade:duration={XFADE}:offset={off:.3f}[{new}]")
        label = new
        running += durations[i] - XFADE
    total = running
    parts.append(f"[{label}]fade=t=in:st=0:d=0.4,fade=t=out:st={total - 0.5:.3f}:d=0.5[vout]")
    fc = ";".join(parts)
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[vout]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


# --------------------------------------------------------------------------- command

def build(milestone: int, source: str, require_posted: bool = False, rows: dict | None = None) -> Path | None:
    cfg = C.load_config()
    if rows is None:
        rows = {r["issue"]: r for r in C.load_rows(source)}
    lo, hi = milestone - 4, milestone
    issues = [rows[i] for i in range(lo, hi + 1) if i in rows]
    if len(issues) < 5:
        print(f"Issues {lo}-{hi}: only {len(issues)} present — skipping.")
        return None
    if require_posted:
        not_posted = [r["issue"] for r in issues if r.get("status") != "posted"]
        if not_posted:
            print(f"Issues {lo}-{hi}: {not_posted} not posted yet — skipping.")
            return None
    missing = [r["issue"] for r in issues if not (C.POSTS_DIR / f"hb-{r['issue']:03d}.jpg").exists()]
    if missing:
        print(f"Missing cards for issues {missing} — build/post those first.")
        return None
    days = C.countdown_ctx(cfg, C.today_for(cfg, None))["days"]
    tmp = Path(tempfile.mkdtemp())
    frames = [intro_frame(cfg, lo, hi, days, tmp)]
    durs = [D_INTRO]
    for k, r in enumerate(issues, 1):
        frames.append(issue_frame(cfg, r, C.POSTS_DIR / f"hb-{r['issue']:03d}.jpg", k, len(issues), tmp))
        durs.append(D_ISSUE)
    frames.append(outro_frame(cfg, issues, days, tmp))
    durs.append(D_OUTRO)
    out = SHORTS_DIR / f"hb-{lo:03d}-{hi:03d}.mp4"
    encode(frames, durs, out)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Short -> {out}")
    return out


def build_auto(source: str) -> list[Path]:
    """Build every completed 5-block (all 5 posted, cards present) that has no
    Short yet. Safe to run every day — it no-ops until a block completes."""
    cfg = C.load_config()
    rows = {r["issue"]: r for r in C.load_rows(source)}
    made: list[Path] = []
    for m in range(5, cfg["total_issues"] + 1, 5):
        out = SHORTS_DIR / f"hb-{m - 4:03d}-{m:03d}.mp4"
        if out.exists():
            continue
        res = build(m, source, require_posted=True, rows=rows)
        if res:
            made.append(res)
    if not made:
        print("No new recap Shorts to build.")
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--milestone", type=int, help="last issue of the 5-block (5, 10, 15, ...)")
    ap.add_argument("--auto", action="store_true", help="build any completed 5-block that has no Short yet")
    ap.add_argument("--source", help="CSV/URL; defaults to SHEET_CSV env or tracker.csv")
    a = ap.parse_args()
    src = a.source or __import__("os").environ.get("SHEET_CSV") or "tracker.csv"
    if a.auto:
        build_auto(src)
    elif a.milestone:
        build(a.milestone, src)
    else:
        ap.error("pass --auto or --milestone N")


if __name__ == "__main__":
    main()

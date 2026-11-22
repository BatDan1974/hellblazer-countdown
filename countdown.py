#!/usr/bin/env python3
"""
Hellblazer 40th-anniversary countdown: build the daily post card + caption so you
can post it to Instagram yourself.

Commands
  preview   Render one issue locally (no commit).   --issue 47 --today 2027-02-01
  prepare   Build the next "Ready" issue's card into public/posts/ and write NEXT_POST.md
            (the image + a copy-ready caption, viewable straight from the repo on your phone)

Data source (first match wins): --source, $SHEET_CSV, ./tracker.csv
  A local .csv/.xlsx file or a URL that returns CSV (e.g. a Google Sheet
  published to the web as CSV). Mark an issue's Status "Ready" to queue it;
  set it to "Posted" after you've posted it.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
FONTS = ROOT / "assets" / "fonts"
POSTS_DIR = ROOT / "public" / "posts"
PHOTOS_DIR = ROOT / "photos"
OUT_DIR = ROOT / "out"

DEFAULTS = {
    "series": "HELLBLAZER",
    "anniversary": "2027-09-22",      # US release date of Hellblazer #1
    "total_issues": 300,
    "handle": "@yourhandle",
    "timezone": "Europe/London",
    "friends_label": "FRIENDS BURNED",
    "cigs_label": "CIGS SMOKED",
    "api_version": "v23.0",
    "hashtags": [
        "#hellblazer", "#johnconstantine", "#vertigocomics", "#dccomics",
        "#comicbooks", "#comiccollector", "#comicsofinstagram",
        "#readingchallenge", "#hellblazer40",
    ],
}

W, H = 1080, 1350
BG_TOP, BG_BOTTOM = (6, 9, 14), (13, 27, 42)
WHITE = (242, 245, 248)
MUTED = (138, 151, 166)
BLUE = (23, 150, 210)   # BatDan brand blue (sampled from the BD logo)
EMBER = (255, 107, 26)
GOLD = (255, 200, 61)
PANEL = (15, 26, 39)
PANEL_LINE = (31, 51, 71)
STAR_OFF = (48, 62, 78)


# --------------------------------------------------------------------------- config / data

def load_config() -> dict:
    cfg = dict(DEFAULTS)
    p = ROOT / "config.json"
    if p.exists():
        cfg.update(json.loads(p.read_text(encoding="utf-8")))
    return cfg


def today_for(cfg: dict, override: str | None = None) -> date:
    override = override or os.environ.get("COUNTDOWN_TODAY")
    if override:
        return date.fromisoformat(override)
    return datetime.now(ZoneInfo(cfg["timezone"])).date()


HEADER_MAP = {
    "issue": "issue", "status": "status", "score": "score", "take": "take",
    "friends burned": "friends", "cigs": "cigs", "arc / title": "arc",
    "photo": "photo", "extra tags": "extra_tags",
    "writer": "writer", "artist": "artist", "cover artist": "cover_artist", "story arc": "story_arc",
}

CLZ_FILE = ROOT / "data" / "clz.csv"   # creators + story arc exported from CLZ (fallback if the tracker has none)


def norm_header(h) -> str:
    h = re.sub(r"\(.*?\)", "", str(h or "")).strip().lower()
    return re.sub(r"\s+", " ", h)


def to_int(x, default=0) -> int:
    try:
        return int(float(str(x).strip()))
    except (ValueError, TypeError):
        return default


def load_clz() -> dict[int, dict]:
    if not CLZ_FILE.exists():
        return {}
    out: dict[int, dict] = {}
    with open(CLZ_FILE, newline="", encoding="utf-8-sig") as fh:
        for rec in csv.DictReader(fh):
            n = to_int(rec.get("Issue"), 0)
            if n > 0:
                out[n] = {
                    "writer": (rec.get("Writer") or "").strip(),
                    "artist": (rec.get("Artist") or "").strip(),
                    "cover_artist": (rec.get("Cover artist") or "").strip(),
                    "story_arc": (rec.get("Story arc") or "").strip(),
                }
    return out


def read_table(source: str) -> list[list[str]]:
    if source.startswith(("http://", "https://")):
        r = requests.get(source, timeout=30)
        r.raise_for_status()
        return list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))
    p = Path(source)
    if not p.is_absolute():
        p = ROOT / p
    if p.suffix.lower() in (".xlsx", ".xlsm"):
        import openpyxl  # only needed for .xlsx sources

        wb = openpyxl.load_workbook(p, data_only=True)
        ws = wb["Tracker"] if "Tracker" in wb.sheetnames else wb.active
        return [["" if c is None else str(c) for c in row] for row in ws.iter_rows(values_only=True)]
    with open(p, newline="", encoding="utf-8-sig") as fh:
        return list(csv.reader(fh))


def load_rows(source: str) -> list[dict]:
    table = read_table(source)
    hdr_i = next((i for i, r in enumerate(table) if any(norm_header(c) == "issue" for c in r)), None)
    if hdr_i is None:
        sys.exit(f"No 'Issue' header row found in {source}")
    cols = {i: HEADER_MAP[norm_header(c)] for i, c in enumerate(table[hdr_i]) if norm_header(c) in HEADER_MAP}
    rows = []
    for raw in table[hdr_i + 1:]:
        rec = {name: (raw[i].strip() if i < len(raw) and raw[i] is not None else "") for i, name in cols.items()}
        n = to_int(rec.get("issue"), 0)
        if n <= 0:
            continue
        score = None
        if str(rec.get("score", "")).strip():
            try:
                score = max(0.0, min(5.0, round(float(rec["score"]) * 2) / 2))
            except ValueError:
                score = None
        rows.append({
            "issue": n,
            "status": rec.get("status", "").strip().lower(),
            "score": score,
            "take": rec.get("take", ""),
            "friends": max(0, to_int(rec.get("friends"))),
            "cigs": max(0, to_int(rec.get("cigs"))),
            "arc": rec.get("arc", ""),
            "photo": rec.get("photo", ""),
            "extra_tags": rec.get("extra_tags", ""),
            "writer": rec.get("writer", ""),
            "artist": rec.get("artist", ""),
            "cover_artist": rec.get("cover_artist", ""),
            "story_arc": rec.get("story_arc", ""),
        })
    rows.sort(key=lambda r: r["issue"])
    clz = load_clz()
    for r in rows:  # tracker values win; CLZ fills the gaps; your own "Arc / title" beats CLZ's story arc
        for k in ("writer", "artist", "cover_artist", "story_arc"):
            r[k] = r[k] or clz.get(r["issue"], {}).get(k, "")
        r["arc"] = r["arc"] or r["story_arc"]
    f_tot = c_tot = 0
    for r in rows:  # running totals always follow issue order, whatever the sheet says
        f_tot += r["friends"]
        c_tot += r["cigs"]
        r["friends_total"], r["cigs_total"] = f_tot, c_tot
    return rows


# --------------------------------------------------------------------------- drawing helpers

def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


ANTON, BOLD, SEMI, MED, ITALIC = (
    "Anton-Regular.ttf", "FiraSans-Bold.ttf", "FiraSans-SemiBold.ttf", "FiraSans-Medium.ttf", "FiraSans-Italic.ttf",
)


def tracked_width(text: str, f, tracking: float) -> float:
    return sum(f.getlength(c) for c in text) + tracking * max(0, len(text) - 1)


def draw_tracked(d, x, y, text, f, fill, tracking=0.0, align="left"):
    """Baseline-anchored text with letter spacing."""
    if align == "right":
        x -= tracked_width(text, f, tracking)
    elif align == "center":
        x -= tracked_width(text, f, tracking) / 2
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill, anchor="ls")
        x += f.getlength(ch) + tracking
    return x


def wrap_px(text: str, f, max_w: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            trial = f"{cur} {word}".strip()
            if f.getlength(trial) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def fit_text(text, font_name, max_w, max_h, sizes, line_gap=1.22):
    """Largest size whose wrapped text fits the box; ellipsis-truncates if nothing fits."""
    for size in sizes:
        f = font(font_name, size)
        lines = wrap_px(text, f, max_w)
        if len(lines) * size * line_gap <= max_h:
            return f, lines, size
    size = sizes[-1]
    f = font(font_name, size)
    lines = wrap_px(text, f, max_w)
    keep = max(1, int(max_h // (size * line_gap)))
    lines = lines[:keep]
    while lines[-1] and f.getlength(lines[-1] + "…") > max_w:
        lines[-1] = lines[-1][:-1]
    lines[-1] = lines[-1].rstrip() + "…"
    return f, lines, size


def shape_layer(w, h, painter, ss=4) -> Image.Image:
    layer = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    painter(ImageDraw.Draw(layer), w * ss, h * ss)
    return layer.resize((w, h), Image.LANCZOS)


def star_points(w, h, inset=0.0):
    cx, cy, R = w / 2, h / 2 + h * 0.04, min(w, h) / 2 * (1 - inset)
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        r = R if i % 2 == 0 else R * 0.42
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def draw_stars(img, x, y, score, size=62, gap=10):
    for i in range(5):
        fill_ratio = max(0.0, min(1.0, score - i))
        sx = x + i * (size + gap)
        base = shape_layer(size, size, lambda d, w, h: d.polygon(star_points(w, h), fill=STAR_OFF))
        img.alpha_composite(base, (sx, y))
        if fill_ratio > 0:
            gold = shape_layer(size, size, lambda d, w, h: d.polygon(star_points(w, h), fill=GOLD))
            cut = max(1, int(size * fill_ratio))
            img.alpha_composite(gold.crop((0, 0, cut, size)), (sx, y))


def flame_icon(size=64) -> Image.Image:
    def paint(d, w, h):
        d.ellipse((0.2 * w, 0.38 * h, 0.8 * w, 0.98 * h), fill=EMBER)
        d.polygon([(0.5 * w, 0.0), (0.2 * w, 0.66 * h), (0.8 * w, 0.66 * h)], fill=EMBER)
        d.polygon([(0.62 * w, 0.18 * h), (0.5 * w, 0.62 * h), (0.80 * w, 0.62 * h)], fill=EMBER)
        d.ellipse((0.34 * w, 0.58 * h, 0.66 * w, 0.92 * h), fill=GOLD)
        d.polygon([(0.5 * w, 0.40 * h), (0.36 * w, 0.76 * h), (0.64 * w, 0.76 * h)], fill=GOLD)
    return shape_layer(size, size, paint)


def cigarette_icon(w=104, h=64) -> Image.Image:
    def paint(d, W_, H_):
        y0, y1 = 0.58 * H_, 0.80 * H_
        d.rounded_rectangle((0.02 * W_, y0, 0.30 * W_, y1), radius=0.04 * H_, fill=(217, 166, 107))
        d.rectangle((0.30 * W_, y0, 0.82 * W_, y1), fill=(238, 238, 238))
        d.rounded_rectangle((0.80 * W_, y0 - 0.02 * H_, 0.96 * W_, y1 + 0.02 * H_), radius=0.05 * H_, fill=EMBER)
        d.ellipse((0.90 * W_, y0 + 0.02 * H_, 0.98 * W_, y1 - 0.02 * H_), fill=GOLD)
        smoke = (138, 151, 166, 170)
        for off in (0.0, 0.12):
            pts = []
            for t in range(0, 41):
                u = t / 40
                pts.append((0.92 * W_ + off * W_ + 0.07 * W_ * math.sin(u * 7 + off * 20), y0 - 0.04 * H_ - u * 0.34 * H_))
            d.line(pts, fill=smoke, width=int(0.045 * H_), joint="curve")
    return shape_layer(w, h, paint)


def make_gradient_bg() -> Image.Image:
    grad = Image.linear_gradient("L").resize((W, H))
    bg = ImageOps.colorize(grad, black=BG_TOP, white=BG_BOTTOM).convert("RGB")
    noise = Image.effect_noise((W, H), 38).convert("RGB")
    bg = Image.blend(bg, noise, 0.045)
    vig = Image.radial_gradient("L").resize((W, H))            # black centre -> white edge
    vig = vig.point(lambda v: int(max(0, v - 90) * 0.9))
    bg.paste((0, 0, 0), mask=vig)
    return bg.convert("RGBA")


def glow_text(img, xy, text, f, fill, glow_rgb, radius=22, strength=0.75):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).text(xy, text, font=f, fill=255, anchor="ls")
    mask = mask.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: int(min(255, v * strength * 2)))
    glow = Image.new("RGBA", img.size, glow_rgb + (0,))
    glow.putalpha(mask)
    img.alpha_composite(glow)
    ImageDraw.Draw(img).text(xy, text, font=f, fill=fill, anchor="ls")


def badge(img, x, y, size=84):
    logo = ROOT / "assets" / "logo.png"
    if logo.exists():
        pic = ImageOps.fit(Image.open(logo).convert("RGBA"), (size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
        img.paste(pic, (x, y), mask)
        return

    def paint(d, w, h):
        d.ellipse((0, 0, w - 1, h - 1), fill=(24, 110, 176))
        d.ellipse((0.05 * w, 0.05 * h, 0.95 * w, 0.95 * h), outline=(255, 255, 255), width=int(0.035 * w))
        for cx, cy, r in ((0.5, 0.17, 0.07), (0.2, 0.36, 0.05), (0.8, 0.36, 0.05)):
            pts = star_points(int(2 * r * w), int(2 * r * h))
            d.polygon([(px + (cx - r) * w, py + (cy - r) * h) for px, py in pts], fill=(255, 255, 255))
    img.alpha_composite(shape_layer(size, size, paint), (x, y))
    ImageDraw.Draw(img).text((x + size / 2, y + size * 0.74), "BD", font=font(ANTON, int(size * 0.42)),
                             fill=WHITE, anchor="ms")


def find_photo(row: dict) -> Image.Image | None:
    ref = (row.get("photo") or "").strip()
    try:
        if ref.startswith(("http://", "https://")):
            r = requests.get(ref, timeout=30)
            r.raise_for_status()
            return ImageOps.exif_transpose(Image.open(io.BytesIO(r.content)))
        names = [ref] if ref else []
        n = row["issue"]
        for stem in (f"{n:03d}", f"{n}"):
            names += [f"{stem}{ext}" for ext in (".jpg", ".jpeg", ".png", ".webp")]
        for name in names:
            p = PHOTOS_DIR / name
            if p.is_file():
                return ImageOps.exif_transpose(Image.open(p))
    except Exception as exc:  # a bad photo must never stop the daily post
        print(f"warning: could not load photo for #{row['issue']}: {exc}", file=sys.stderr)
    return None


def draw_cover_panel(img, box, row, photo):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((x0 + 8, y0 + 14, x1 + 8, y1 + 14), 16, fill=(0, 0, 0, 190))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(16)))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), 16, fill=255)
    if photo is not None:
        pic = ImageOps.fit(photo.convert("RGB"), (w, h), Image.LANCZOS, centering=(0.5, 0.5))
    else:
        pic = Image.new("RGB", (w, h), PANEL)
        pd = ImageDraw.Draw(pic)
        for k in range(-h, w, 34):
            pd.line((k, h, k + h, 0), fill=(19, 33, 48), width=10)
        pd.text((w / 2, h * 0.52), f"#{row['issue']}", font=font(ANTON, 170), fill=BLUE, anchor="ms",
                stroke_width=4, stroke_fill=BLUE)
        pd.text((w / 2, h * 0.52), f"#{row['issue']}", font=font(ANTON, 170), fill=PANEL, anchor="ms")
        draw_tracked(pd, w / 2, h * 0.52 + 70, "HELLBLAZER", font(SEMI, 30), MUTED, 8, "center")
    img.paste(pic, (x0, y0), mask)
    ImageDraw.Draw(img).rounded_rectangle((x0, y0, x1 - 1, y1 - 1), 16, outline=BLUE, width=5)


# --------------------------------------------------------------------------- post image + caption

def countdown_ctx(cfg: dict, today: date) -> dict:
    """Days-to-go is the real number of days from the build date to the
    anniversary (22 Sep 2027). The number is a live countdown to that fixed
    date, so cards built on the same day share a number — posting a few issues
    in one day to catch up is expected and correct."""
    anniv = date.fromisoformat(cfg["anniversary"])
    return {"days": (anniv - today).days, "anniv": anniv, "today": today}


def render_post(row: dict, cfg: dict, ctx: dict, out_path: Path, photo: Image.Image | None = None) -> Path:
    img = make_gradient_bg()
    d = ImageDraw.Draw(img)
    total = cfg["total_issues"]
    days = ctx["days"]
    anniv_txt = ctx["anniv"].strftime("%d %b %Y").lstrip("0").upper()

    # header
    draw_tracked(d, 60, 92, cfg["series"], font(ANTON, 56), WHITE, 7)
    draw_tracked(d, 62, 128, "40TH ANNIVERSARY COUNTDOWN", font(SEMI, 25), BLUE, 3.2)
    badge(img, W - 56 - 180, 40, 180)
    d = ImageDraw.Draw(img)

    # countdown
    if days > 0:
        num = str(days)
        f_num = font(ANTON, 250)
        glow_text(img, (54, 392), num, f_num, WHITE, BLUE)
        d = ImageDraw.Draw(img)
        nx = 54 + f_num.getlength(num) + 34
        d.text((nx, 262), "DAY TO GO" if days == 1 else "DAYS TO GO", font=font(ANTON, 60), fill=BLUE, anchor="ls")
        d.text((nx, 308), "UNTIL #1 TURNS 40", font=font(SEMI, 30), fill=MUTED, anchor="ls")
        d.text((nx, 352), anniv_txt, font=font(BOLD, 38), fill=WHITE, anchor="ls")
    else:
        glow_text(img, (54, 392), "40 YEARS", font(ANTON, 230), WHITE, EMBER)
        d = ImageDraw.Draw(img)

    # cover photo (or fallback panel)
    draw_cover_panel(img, (60, 432, 460, 1048), row, photo if photo is not None else find_photo(row))
    d = ImageDraw.Draw(img)

    # right column
    rx = 506
    draw_tracked(d, rx, 466, "ISSUE", font(SEMI, 26), MUTED, 5)
    d.text((rx - 4, 626), f"#{row['issue']}", font=font(ANTON, 176), fill=WHITE, anchor="ls")
    left = total - row["issue"]
    sub = f"OF {total}  ·  {left} TO GO" if left > 0 else f"OF {total}  ·  THE FINAL ISSUE"
    d.text((rx, 668), sub, font=font(MED, 28), fill=MUTED, anchor="ls")

    y = 702
    if row["arc"]:
        f_arc, arc_lines, arc_size = fit_text(row["arc"], BOLD, W - 60 - rx, 82, [36, 32, 28], 1.2)
        for ln in arc_lines:
            y += int(arc_size * 1.05)
            d.text((rx, y), ln, font=f_arc, fill=BLUE, anchor="ls")
        y += 14
    star_y = max(y + 10, 756)
    if row["score"] is not None:
        draw_stars(img, rx, star_y, row["score"])
        d = ImageDraw.Draw(img)
        score_txt = f"{row['score']:g}/5"
        d.text((W - 60, star_y + 56), score_txt, font=font(ANTON, 52), fill=GOLD, anchor="rs")

    # Constantine tallies
    ty = max(862, star_y + 62 + 18) if row["score"] is not None else 862
    d.line((rx, ty, W - 60, ty), fill=PANEL_LINE, width=2)
    rows_ = (
        (flame_icon(66), cfg["friends_label"], row["friends"], row["friends_total"], ty + 22),
        (cigarette_icon(), cfg["cigs_label"], row["cigs"], row["cigs_total"], ty + 108),
    )
    for icon, label, this_issue, running, top in rows_:
        img.alpha_composite(icon, (rx if icon.width < 80 else rx - 8, top + (0 if icon.width < 80 else 4)))
        d = ImageDraw.Draw(img)
        d.text((rx + 120, top + 26), label, font=font(SEMI, 25), fill=MUTED, anchor="ls")
        d.text((rx + 120, top + 62), f"+{this_issue} THIS ISSUE", font=font(BOLD, 28), fill=EMBER, anchor="ls")
        d.text((W - 60, top + 64), f"{running}", font=font(ANTON, 76), fill=WHITE, anchor="rs")

    # the take
    bx0, by0, bx1, by1 = 60, 1074, W - 60, 1262
    d.rounded_rectangle((bx0, by0, bx1, by1), 18, fill=PANEL, outline=PANEL_LINE, width=2)
    d.rounded_rectangle((bx0, by0, bx0 + 10, by1), 5, fill=BLUE)
    take = row["take"].strip() or "Another one down."
    f_take, lines, size = fit_text(take, ITALIC, bx1 - bx0 - 96, by1 - by0 - 40, [42, 38, 34, 31, 28, 26])
    block_h = len(lines) * size * 1.22
    ty0 = by0 + (by1 - by0 - block_h) / 2 + size * 0.95
    d.text((bx0 + 28, by0 + 100), "“", font=font(ANTON, 84), fill=BLUE, anchor="ls")
    for i, ln in enumerate(lines):
        d.text((bx0 + 76, ty0 + i * size * 1.22), ln, font=f_take, fill=WHITE, anchor="ls")

    # footer: progress bar
    pct = min(1.0, row["issue"] / total)
    d.rounded_rectangle((60, 1288, W - 60, 1300), 6, fill=(27, 39, 53))
    d.rounded_rectangle((60, 1288, 60 + max(14, (W - 120) * pct), 1300), 6, fill=BLUE)
    d.text((60, 1334), cfg["handle"], font=font(SEMI, 26), fill=BLUE, anchor="ls")
    d.text((W - 60, 1334), f"{round(pct * 100)}% OF THE RUN READ", font=font(SEMI, 26), fill=MUTED, anchor="rs")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_path, "JPEG", quality=93, subsampling=0, optimize=True)
    return out_path


def stars_text(score) -> str:
    if score is None:
        return ""
    full, half = int(score), (score - int(score)) >= 0.5
    return "★" * full + ("½" if half else "") + "☆" * (5 - full - (1 if half else 0))


def credits_lines(row: dict) -> list[str]:
    out = []
    if row["writer"]:
        out.append(f"✍️ Writer: {row['writer']}")
    if row["artist"]:
        out.append(f"🎨 Art: {row['artist']}")
    if row["cover_artist"]:
        out.append(f"🖼️ Cover: {row['cover_artist']}")
    return out


def build_caption(row: dict, cfg: dict, ctx: dict) -> str:
    days, total = ctx["days"], cfg["total_issues"]
    anniv = ctx["anniv"].strftime("%d %B %Y").lstrip("0")
    head_days = f"T-MINUS {days} DAY{'S' if days != 1 else ''}" if days > 0 else "40 YEARS TODAY"
    title = f"Hellblazer #{row['issue']}" + (f" · {row['arc']}" if row["arc"] else "")
    parts = [f"☠️ {head_days} — {title}"]
    if row["score"] is not None:
        parts.append(f"{stars_text(row['score'])}  {row['score']:g}/5")
    parts.append("")
    if row["take"]:
        parts += [row["take"][:1500], ""]
    credits = credits_lines(row)
    if credits:
        parts += credits + [""]
    parts += [
        f"🔥 Friends burned: +{row['friends']} (total {row['friends_total']})",
        f"🚬 Cigs: +{row['cigs']} (total {row['cigs_total']})",
        "",
        f"📖 Issue {row['issue']}/{total} — reading the whole run before #1 turns 40 on {anniv}.",
        "",
    ]
    tags = " ".join(t for t in [row["extra_tags"].strip(), " ".join(cfg["hashtags"])] if t)
    parts.append(tags)
    return "\n".join(parts).strip()[:2150]


# --------------------------------------------------------------------------- commands

def source_arg(args) -> str:
    return args.source or os.environ.get("SHEET_CSV") or "tracker.csv"


def cmd_preview(args):
    cfg = load_config()
    rows = load_rows(source_arg(args))
    ctx = countdown_ctx(cfg, today_for(cfg, args.today))
    if args.issue:
        row = next((r for r in rows if r["issue"] == args.issue), None)
    else:
        row = next((r for r in rows if r["status"] == "ready"), rows[0] if rows else None)
    if row is None:
        sys.exit("No matching issue found.")
    out = render_post(row, cfg, ctx, OUT_DIR / f"preview-{row['issue']:03d}.jpg")
    print(f"Image  -> {out}\n")
    print(build_caption(row, cfg, ctx))


def write_next_post(row: dict, cfg: dict, ctx: dict, image_rel: str) -> None:
    """Write NEXT_POST.md (image + copyable caption) and a plain caption .txt."""
    caption = build_caption(row, cfg, ctx)
    (POSTS_DIR / f"hb-{row['issue']:03d}.txt").write_text(caption + "\n", encoding="utf-8")
    md = (
        f"# 📮 Next post — Hellblazer #{row['issue']}\n\n"
        f"**{ctx['days']} days to go.**  Save the image, copy the caption, post to Instagram.\n\n"
        f"![Post card]({image_rel})\n\n"
        f"### Caption\n\n"
        f"```\n{caption}\n```\n\n"
        f"---\n"
        f"_After you post this, set issue {row['issue']} to **Posted** in your tracker; the next "
        f"Ready issue then appears here._\n"
    )
    (ROOT / "NEXT_POST.md").write_text(md, encoding="utf-8")


def cmd_prepare(args):
    cfg = load_config()
    ctx = countdown_ctx(cfg, today_for(cfg, args.today))
    rows = load_rows(source_arg(args))
    ready = [r for r in rows if r["status"] == "ready"]          # rows are sorted by issue
    if not ready:
        (ROOT / "NEXT_POST.md").write_text(
            "# 📮 Nothing queued\n\nNo issue is marked **Ready** in your tracker.\n\n"
            "Fill in an issue's score, take, friends and cigs, upload its photo to `photos/`, "
            "and set its status to **Ready** — the finished post will appear here.\n",
            encoding="utf-8")
        print("No issue marked Ready; nothing to build.")
        return
    row = ready[0]
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    out = render_post(row, cfg, ctx, POSTS_DIR / f"hb-{row['issue']:03d}.jpg")
    write_next_post(row, cfg, ctx, str(out.relative_to(ROOT)))
    print(f"Built issue #{row['issue']} -> {out} and NEXT_POST.md")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("preview", help="render one issue locally (no commit)")
    sp.add_argument("--source")
    sp.add_argument("--today", help="pretend today is YYYY-MM-DD")
    sp.add_argument("--issue", type=int)
    sp.set_defaults(fn=cmd_preview)
    sp = sub.add_parser("prepare", help="build the next Ready issue's card + caption into the repo")
    sp.add_argument("--source")
    sp.add_argument("--today", help="pretend today is YYYY-MM-DD")
    sp.set_defaults(fn=cmd_prepare)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()

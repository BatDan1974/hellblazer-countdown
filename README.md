# Hellblazer 40th Countdown

A free robot that builds your daily Hellblazer countdown post — image **and** caption —
ready for you to post to Instagram in about 30 seconds a day, all from your phone.

Each post: the countdown number, the issue, your photo of the comic, a star score, your one-line
take, the creator credits, and the running "friends burned / cigs smoked" tallies.

> **Note:** fully automatic posting to Instagram needs Meta's developer setup, which was a dead end
> (see the end of this file). So instead the robot builds the finished post and hands it to you to
> post yourself — no Instagram login, no token, no Meta account needed. Everything below is free.

```
You fill a row in a Google Sheet + upload the comic photo
        │
        ▼
A free robot (GitHub Actions) builds the finished card + caption
        │
        ▼
You open ONE page on your phone, save the image, copy the caption, post to Instagram
```

---

## Your daily routine (about a minute)

1. **Read the issue.**
2. **In the Google Sheet** (on your phone), fill that issue's row: **Score**, **Take**, **Friends burned**,
   **Cigs smoked** — then set **Status → Ready**.
3. **Upload the comic photo**: take a flat, straight-on photo of the cover, name it by issue number with
   three digits — issue 7 = `007.jpg`, issue 47 = `047.jpg`, issue 150 = `150.jpg` — and upload it into the
   `photos` folder in your repo.
4. **Wait a little.** The robot runs every couple of hours and builds the post. (Want it instantly? Open the
   **Actions** tab → **Build next Hellblazer post** → **Run workflow**.)
5. **Open `NEXT_POST.md`** in your repo on your phone. It shows the finished card and the caption. **Save the
   image** (long-press), **copy the caption**, and **post to Instagram.**
6. **Mark it done**: set that issue's **Status → Posted** in the sheet. The next Ready issue then takes its
   place in `NEXT_POST.md`.

Tip: get ahead by marking several issues **Ready** — the robot always shows the lowest-numbered one that
isn't Posted yet, so you move through them one at a time.

---

## One-time setup

### 1. The repo
You've already got it: a **public** GitHub repo with these files. (It can stay public — only your finished
post cards live there, nothing private.)

### 2. Your tracker (where you type the stats)
Easiest on a phone is Google Sheets:
1. Go to **sheets.google.com**, new blank sheet, **File → Import → Upload**, drop in
   `Hellblazer-40th-Countdown-Tracker.xlsx`, choose **Replace spreadsheet**.
2. **File → Share → Publish to web** → pick the **Tracker** tab and **CSV** → **Publish**, and copy the link.
3. In GitHub: **Settings → Secrets and variables → Actions → New repository secret**, name it
   `SHEET_CSV_URL`, paste the link.

Prefer not to use Google Sheets? Skip the secret and edit `tracker.csv` directly in the repo instead.
(Google's published link can lag a few minutes behind your edits — give it a moment before expecting a build.)

### 3. Make it yours
`config.json` holds your handle (shown on the card) and hashtags. Your **BD logo** is `assets/logo.png` and
the accent colour is already set to your BatDan blue.

That's the whole setup. No Instagram app connection, no Meta developer account, no token to renew — ever.

---

## Preview a post locally (optional, needs a computer)

```bash
pip install -r requirements.txt
python countdown.py preview --issue 47 --today 2027-02-01
# -> out/preview-047.jpg + the caption printed in the terminal
```

---

## What's in the tracker

- **Status** — `To read` / `Ready` / `Posted`. Only `Ready` gets built; set `Posted` once you've posted it.
- **Score, Take, Friends burned, Cigs smoked** — you fill these; they appear on the card.
- **Arc / title, Photo, Extra tags** — optional per-issue overrides. (Photo column can hold a different
  filename or an image URL if you don't want to name the file by issue number.)
- **Writer / Artist / Cover artist / Story arc** — from your CLZ export (some gaps; blank credits are just
  left off).
- **Era / run** and **Summary** — reference columns (the summary is a spoiler-free draft you can rewrite).

Running totals (friends/cigs, % of run) are worked out automatically from every row in issue order — you only
ever enter each issue's own numbers.

## Good to know
- Images are 1080×1350 (Instagram's 4:5), built fresh each run.
- Use photos of **your own copies**.
- `NEXT_POST.md` is the one page to bookmark on your phone — it's always the next post, ready to go.
- Refresh the CLZ creator data later by re-exporting and replacing `data/clz.csv` (columns:
  `Issue, Writer, Artist, Cover artist, Story arc`).

## If you ever want true auto-posting
Automatic posting needs a Meta developer app + a business portfolio that can "claim" the Instagram account,
and that claim kept failing (a known Meta issue). If Meta ever cooperates, the posting step can be added back
on top of this — the card-building half is already done.

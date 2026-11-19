# Hellblazer 40th Countdown — complete beginner's guide

This guide assumes you have **never set up anything like this before**. Follow it top to bottom.
Where you see 🟦, that's a one-off setup step. Where you see 🟩, that's something you'll do day to day.

---

## 1. What this actually does

Every day, a free robot on the internet builds one Instagram image for the next Hellblazer issue —
a countdown number, the issue, your photo of the comic, a star score, your one-line verdict, the
creator credits, and the running "friends burned / cigs smoked" tallies — and posts it to your
Instagram automatically. **You never have to be at your computer for it to post.** You just read the
comic and type a few words into a spreadsheet.

The "robot" is a free service built into GitHub called **GitHub Actions**. Think of it as a kitchen
timer that wakes up once a day, runs the little program in this folder, and goes back to sleep.

---

## 2. What you'll need (all free)

- A **GitHub account** (you already have one: BatDan1974).
- A **Google account** (for the spreadsheet).
- An **Instagram account** that is a *Professional* account (free to switch — step 5).
- A **Facebook account** (Meta makes you have one to use their developer tools, even for Instagram).
- About **45 minutes**, once. After that it runs itself.

You will **not** need to install anything or write any code. Everything is done in a web browser.

---

## 3. The big picture (how the pieces fit)

```
   You type notes            A free robot wakes                It posts to
   into a spreadsheet   -->  up once a day and       -->       your Instagram
   (Google Sheets)          builds the picture                 automatically
                            (GitHub Actions)
```

Setup is just connecting those three things together once. Let's go.

---

## 4. 🟦 Step one: put this code on GitHub

A "repository" (repo) is just a folder that lives on GitHub. You need to create one and put these
files in it.

1. Go to **github.com** and sign in.
2. Top-right, click the **+** then **New repository**.
3. **Repository name:** type something like `hellblazer-countdown`.
4. **IMPORTANT — set it to `Public`.** It has to be public so Instagram can fetch the images. (Only the
   finished post pictures are ever visible; nothing private goes in here.)
5. Leave everything else as-is and click **Create repository**.
6. On the next page click the link **uploading an existing file**.
7. On your computer, **unzip** `hellblazer-countdown.zip`. Open the unzipped folder, select **everything
   inside it**, and drag it all into the GitHub upload box. Wait for every file to list, then click
   **Commit changes**.

> ⚠️ One folder is easy to miss: `.github` (it starts with a dot). If you drag the whole folder contents
> it comes along automatically. After uploading, check your repo shows a `.github` folder — if it's
> missing, the robot won't run. If dragging is fiddly, install **GitHub Desktop** (desktop app, free) and
> drag the folder in there instead; it keeps everything.

You now have the code online. Nothing runs yet — we need to give it your Instagram keys.

---

## 5. 🟦 Step two: make Instagram a "Professional" account

The automatic-posting feature only works with a Professional (Business or Creator) account. It's free
and you can switch back any time.

1. Open the **Instagram app** on your phone, go to your profile.
2. Tap the **menu (≡)** → **Settings and privacy**.
3. Find **Account type and tools** → **Switch to professional account**.
4. Choose **Creator** (or Business — either works), pick a category, and finish.

That's it. Your posts, followers and feed don't change.

---

## 6. 🟦 Step three: create a Meta app and get your two keys

This is the fiddliest part. Meta (Facebook's company) changes this screen often, so follow the landmarks
rather than expecting exact wording. Their official walkthrough is here and is worth keeping open in a
second tab: **https://developers.facebook.com/docs/instagram-platform/content-publishing**

You are getting **two things** out of this step:
- **`IG_USER_ID`** — a long number that identifies your Instagram account.
- **`IG_ACCESS_TOKEN`** — a long password-like string that lets the robot post as you.

Steps:

1. Go to **developers.facebook.com**, click **Get Started / Log in**, and sign in with your **Facebook**
   account. Accept the developer terms if asked.
2. Click **My Apps** (top right) → **Create App**.
3. When asked what you're building, pick the option about **Instagram** / "Other", and app type
   **Business** if it asks. Give it any name (e.g. "Hellblazer Poster"). Create it.
4. On the app's dashboard, find **Instagram** in the product list and click **Set up**. Choose the option
   named roughly **"API setup with Instagram login"**.
5. In that section there's a button to **add / connect an Instagram account** — connect *your* account and
   approve the permissions it asks for (they'll mention *content publishing*).
6. The same page shows your **Instagram account ID** — a long number. **Copy it somewhere safe. That's your
   `IG_USER_ID`.**
7. The same page has a **Generate token** button. Click it, approve, and it gives you a long token string.
   **Copy it.** This first token is short-lived — the next step makes it last 60 days.

### Make the token last 60 days
A fresh token only lasts about an hour. To get the 60-day version, paste this web address into your
browser, replacing the two bits in CAPITALS, and press Enter:

```
https://graph.instagram.com/access_token?grant_type=ig_exchange_token&client_secret=YOUR_APP_SECRET&access_token=YOUR_SHORT_TOKEN
```

- **YOUR_APP_SECRET** is on your Meta app page under **App settings → Basic → App secret** (click *Show*).
- **YOUR_SHORT_TOKEN** is the token you just copied.

The page that loads shows a new, longer token. **That** long one is your `IG_ACCESS_TOKEN`.

Don't worry if this feels clunky — you only do it once, and step 9 keeps it renewed automatically.

---

## 7. 🟦 Step four: give GitHub your keys (secrets)

"Secrets" are where GitHub safely stores passwords. The robot reads them but nobody can see them.

1. In your GitHub repo, click **Settings** (top menu of the repo).
2. Left sidebar: **Secrets and variables** → **Actions**.
3. Click **New repository secret** and add each of these (Name must match **exactly**, capitals included):

| Name (type exactly) | Value to paste |
| --- | --- |
| `IG_USER_ID` | the long number from step 6.6 |
| `IG_ACCESS_TOKEN` | the long 60-day token from step 6 |
| `SHEET_CSV_URL` | *(optional — added in step 8)* |
| `GH_PAT` | *(optional — only for auto-renewal, step 9)* |

Add a secret, click **Add secret**, repeat for the next. Done.

---

## 8. 🟦 Step five: your spreadsheet (where you type your notes)

You have two choices. **Option A (recommended)** lets you edit on your phone in Google Sheets.
**Option B** is simpler but you edit a plain file on GitHub.

### Option A — Google Sheets (recommended)
1. Go to **sheets.google.com**, make a blank sheet.
2. **File → Import → Upload**, and drop in `Hellblazer-40th-Countdown-Tracker.xlsx`. Choose **Replace
   spreadsheet**.
3. Now publish it so the robot can read it: **File → Share → Publish to web**.
4. In the dialog, pick the **Tracker** tab (not "Entire document") and the format **Comma-separated
   values (.csv)**. Click **Publish** and copy the web link it gives you.
5. Back in GitHub (Settings → Secrets, as in step 7), add a secret named `SHEET_CSV_URL` and paste that
   link.

> Note: Google takes a few minutes to update the published link after you edit. If you mark something
> `Ready` just before the daily run, give it ten minutes.

### Option B — edit the file on GitHub
Skip the secret. The robot will read `tracker.csv` from the repo. To edit it, open `tracker.csv` in GitHub,
click the **pencil** icon, change the row, and **Commit**. (Workable, but a spreadsheet is much nicer.)

---

## 9. 🟦 Step six: make it yours

1. In the repo, open `config.json` and click the **pencil** to edit.
2. Change `"@yourhandle"` to your real Instagram handle (this is printed on every image).
3. Change hashtags if you like. Leave `timezone` and the dates as they are. **Commit**.
4. **Optional logo:** upload a square image named `logo.png` into the `assets` folder (Add file → Upload
   files). If you don't, a blue "BD" badge is drawn instead.

---

## 10. 🟦 Step seven: TEST IT before it goes live

Always do a pretend run first.

1. In the repo, mark one issue ready: in your spreadsheet (or `tracker.csv`), set issue #1's **Status** to
   `Ready`, and type a short **Take**. (If using Google Sheets, wait a few minutes for it to publish.)
2. In GitHub, click the **Actions** tab.
3. Click **Daily Hellblazer post** on the left → **Run workflow** (right) → tick **dry run** → **Run
   workflow**.
4. Wait ~1 minute, click into the run, and open the **dry-run-post** artifact at the bottom. That's the
   image it *would* have posted — check it looks right.
5. Happy? Run it again **without** dry run ticked. It posts for real. 🎉

From now on it runs by itself every day at **17:30 UK time**.

---

## 11. 🟩 Your daily routine (the only ongoing work)

1. Read the issue.
2. In your spreadsheet, fill in that issue's row: **Score**, **Take** (your one-liner), **Friends burned**,
   **Cigs**. The Writer/Artist/Era/Summary columns are already filled for reference.
3. *(Optional)* Photograph your copy. Name it by issue number with a leading zero to make three digits —
   issue 7 is `007.jpg`, issue 47 is `047.jpg`, issue 150 is `150.jpg` — and upload it into the `photos`
   folder in the repo. No photo just means a styled "#47" panel instead.
4. Set that row's **Status** to `Ready`.

That's all. The robot posts the lowest-numbered `Ready` issue each day.

**Handy:** you can get a week ahead by marking several rows `Ready` at once — it still only posts one per
day, never two. If you forget and nothing is `Ready`, it simply posts nothing and GitHub emails you, so you
never post the wrong issue by accident.

---

## 12. 🟦 Step eight (optional): never touch the token again

The Instagram token expires every 60 days. You can renew it by hand (re-do the token part of step 6), or
set up auto-renewal:

1. Create a **GitHub personal access token**: github.com → your profile photo → **Settings** →
   **Developer settings** → **Personal access tokens → Fine-grained tokens** → **Generate new token**.
   Give it access to **only this repo**, and under permissions set **Secrets: Read and write**.
2. Copy that token, and add it as a repo secret named `GH_PAT` (step 7).

Now the included monthly job refreshes your Instagram token on its own.

---

## 13. If something goes wrong (troubleshooting)

| What you see | What it means / fix |
| --- | --- |
| The daily run shows a red ✗ and you got an email | Usually nothing was marked `Ready`. That's harmless. Mark an issue `Ready`. |
| Red ✗ mentioning "token" or "OAuth" | Your Instagram token expired. Redo the 60-day token (step 6) and update the `IG_ACCESS_TOKEN` secret. |
| It posted but there's no photo | You didn't add a photo for that issue, or the filename wasn't three digits (e.g. `47.jpg` instead of `047.jpg`). |
| Nothing happens at 17:30 | Check the repo is **Public** and the `.github` folder uploaded. GitHub can also start cron runs a few minutes late — that's normal. |
| The handle on the image is wrong | Edit `config.json` (step 9). |
| I need to re-post an issue | In the repo, open `state/posted.json`, delete that issue's entry, commit, mark it `Ready` again. |

To run it any time without waiting for 17:30: **Actions → Daily Hellblazer post → Run workflow**.

---

## 14. Mini-glossary

- **Repo / repository** — your project folder on GitHub.
- **Commit** — GitHub's word for "save this change".
- **GitHub Actions** — the free robot that runs the daily job.
- **Secret** — a safely-stored password GitHub keeps for the robot.
- **Token** — the Instagram "password" that lets the robot post as you.
- **Dry run** — a pretend run that builds the image but doesn't post.
- **CSV** — a plain spreadsheet format; the link the robot reads your notes from.

---

## 15. Good-to-know notes

- Only Instagram's **official** tool is used — no dodgy "auto-follow" bots that get accounts banned.
- Use photos of **your own copies**, not covers downloaded off the internet.
- Images are the correct Instagram size automatically (1080×1350).
- Your written **Take** is the only thing posted as your words — the summaries in the tracker are just your
  private reference and are never auto-posted.
- The whole thing costs **nothing**: public GitHub repos and the Instagram API are free.

---

## 16. Reference: what's in the tracker columns

- **Status** — `To read` / `Ready` / `Posted`. Only `Ready` triggers a post.
- **Score, Take, Friends burned, Cigs** — you fill these in; they appear on the image.
- **Arc / title, Photo, Extra tags** — optional overrides you can fill per issue.
- **Writer / Artist / Cover artist / Story arc** — from your CLZ export (some gaps; see below).
- **Era / run** — which writer's run the issue belongs to (good for milestone posts).
- **Summary** — a spoiler-free draft you can rewrite. Lines marked **(verify)** are my less-certain guesses;
  "draft to add" ones are blanks for you to fill.

### Data gaps to know about
- The CLZ export has **no artist for 76 issues** (mostly #1–50 and #251–300) and **no story arc for 83**.
  Blank credits are just left off the caption — fill the tracker's own columns to fix any.
- **Plot text** isn't in CLZ, so the summaries are my own spoiler-free drafts, not CLZ's.

### Refreshing the creator data later
Re-export from CLZ Cloud (**Export to CSV/TXT**, tick Series, Issue No., Artist, Cover Artist, Writer, Story
Arc) and replace `data/clz.csv`, keeping the columns `Issue, Writer, Artist, Cover artist, Story arc`.

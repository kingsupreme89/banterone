# BanterONE

Retail district operations mobile web app for **Banter** (Signet jewelry brand).
District reporting, leaderboards, disciplinary tools, and the **Banter Buddy** RPG
companion — built as a single vanilla HTML/JS/CSS file with real-time Firebase
Firestore sync.

## Live

- **App:** <https://banter1ne.github.io/BanterOne/>
- **Repo:** <https://github.com/Banter1ne/BanterOne> (branch: `main`)
- **Hosting:** GitHub Pages, auto-deployed on every push to `main` via
  `.github/workflows/deploy.yml` (publishes the `redesign/` folder)

## Stack

- **Frontend:** vanilla HTML/CSS/JS — no framework, no build step
- **Backend:** Firebase Firestore (compat SDK v10.12.2 via CDN), real-time sync
- **PWA:** installable, fullscreen, no-zoom on iOS
- **Deploy:** GitHub Pages via GitHub Actions

## Run locally

Open `redesign/index.html` directly in a browser, or serve the folder:

```bash
cd redesign
python3 -m http.server 4175
# visit http://127.0.0.1:4175/
```

## Login

Password is the user's **first + last initials, uppercase**
(e.g. Brandy Arguello → `BA`, Tasha Gerold → `TG`). Pick a user from the
dropdown on the login screen. See `HANDOFF.md` for the full roster.

## Structure

```
redesign/
  index.html        # entire app — HTML, CSS, JS
  manifest.json     # PWA manifest
  icon-192.png      # app icon
  buddy-gem.png     # Buddy character art
  docs/             # Playbook source PDFs (linked from the app)
.github/workflows/
  deploy.yml        # GitHub Pages deploy — publishes redesign/ on push to main
HANDOFF.md          # full session handoff & architecture notes
```

## Develop

1. Edit `redesign/index.html` (the entire app lives here).
2. Commit and push to `main` — GitHub Pages redeploys automatically.

> See `HANDOFF.md` for the full architecture, Firestore schema, state shape,
> feature list, and known issues.

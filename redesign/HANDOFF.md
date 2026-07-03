# BanterONE Redesign Handoff

## Current Build

The active demo is a self-contained mobile web app:

- App file: `index.html`
- Docs folder: `docs/`
- Notes: `README.md`

It can be opened directly in a browser:

```text
file:///Users/user/Documents/BanterONE/index.html
```

Or served locally:

```text
http://127.0.0.1:4173/
```

The current workspace was originally empty, so this is a fresh redesign prototype built from the design handoff and then populated with data from:

```text
/Users/user/Claude/Projects/BanterONE
```

## Source Material Used

Design handoff:

```text
/Users/user/Downloads/design_handoff_banterone_redesign 2/
```

Existing BanterONE project data and docs:

```text
/Users/user/Claude/Projects/BanterONE/data/
/Users/user/Claude/Projects/BanterONE/docs/
```

PDFs from the source docs folder were copied into this workspace's `docs/` folder and linked from Playbook.

## Implemented Screens

- Login
- Home
- Store
- Banter Buddy
- Playbook
- Arena
- Settings
- Notifications overlay
- Buddy info sheet
- Daily Feed composer and flair sheet
- Train lesson picker, article view, quiz modal, and result screen

## Login / Demo Accounts

Login is demo-only, client-side, and not connected to a backend.

Current behavior:

- User selects their identity from a dropdown.
- Email fills automatically.
- Password is the user's first and last initials, case-insensitive.

Examples:

- Brandy A. -> `BA`
- Tasha Gerold -> `TG`
- Gina G. -> `GG`

The selected user updates:

- Home header
- Store screen
- Settings profile
- Arena `YOU` labels
- New Daily Feed post author

## Data Included

The app includes the real seeded roster from the existing project:

- 11 CO + NM stores
- Store IDs
- Store names
- Managers
- Malls
- Phone numbers
- Daily plans

Arena is populated with:

- Today / Monthly / YTD store leaderboards
- Sales / Piercings / ESA individual leaderboards
- Seeded daily submissions
- Seeded individual metrics

The source data is currently embedded in `index.html`, not loaded dynamically from CSV.

## Settings

Settings are split into:

- Account Settings
- Workplace Admin

Settings fields are UI-only placeholders for now. Toggles work locally in memory, but they do not persist.

## Current Visual Notes

The app follows the selected dark BanterONE redesign:

- Black fullscreen mobile shell
- Lime accent
- Instrument Serif wordmark and display text
- Inter UI text
- Floating bottom island navigation
- Raised circular `B` Buddy button
- Neon green spacers between major sections

Recent bottom nav tuning:

- Non-`B` labels increased to `12px`
- Island narrowed with `30px` side insets
- Black island height reduced to `44px`
- `B` button adjusted to `52px`
- `B` font adjusted to `24px`

The user has been visually tuning the bottom island proportions. Avoid large jumps; make small 1-4px adjustments.

## Known Limitations

- No real authentication or session persistence.
- No backend.
- No Microsoft SSO.
- No CSV loading at runtime.
- Login initials are a demo lock only.
- Feed posts, reactions, settings, Buddy stats, and training results reset on reload.
- Buddy art is still placeholder text/striped art.
- Monthly/YTD Arena values are scaled from seeded daily data for demo purposes.
- Store/Admin permissions are not enforced yet beyond display context.

## Important Product Direction

If something does not match the handoff or existing BanterONE data, ask before making a judgment-call change.

The design handoff says Store/Arena should carry over the existing leaderboard behavior until fully redesigned. That has now been partially honored by bringing over:

- Real store roster
- Today/Monthly/YTD leaderboard structure
- Store and individual leaderboard tabs

## Suggested Next Steps

1. Finish visual tuning of the bottom island nav.
2. Add role-based settings visibility:
   - District Manager sees Workplace Admin.
   - Store Manager sees some admin tools.
   - Associates see Account Settings only.
3. Move embedded data into JSON files or CSV loading.
4. Add local persistence with `localStorage`.
5. Replace Buddy placeholder art.
6. Decide whether this remains a static PWA-style prototype or gets ported into the existing Streamlit app.
7. If porting, start from:

```text
/Users/user/Claude/Projects/BanterONE/app.py
/Users/user/Claude/Projects/BanterONE/tabs/
/Users/user/Claude/Projects/BanterONE/lib/
```


# BanterONE Redesign

This workspace contains a self-contained mobile web implementation of the BanterONE redesign handoff.

## Open the app

Open `index.html` directly in a browser, or run a local static server from this folder and visit:

```text
http://127.0.0.1:4173/
```

## Included flows

- Login screen
- Home dashboard with KPI cards and Daily Feed
- Daily Feed composer with News, Shoutout, and Update flair
- Store leaderboard placeholder
- Banter Buddy with Feed, Train, and Cheer charge actions
- Train lesson picker, article view, quiz modal, pass/fail result, and 3/3 double XP
- Playbook starter screen
- Arena placeholder
- Notification center
- Buddy info sheet
- Settings with two top-level groups:
  - Account Settings
  - Workplace Admin
- District Arena populated from the existing BanterONE project data:
  - 11 real CO + NM store IDs, malls, managers, phone numbers, and plans
  - Today/Monthly/YTD store leaderboard
  - Sales, Ear Piercings, and ESA individual leaderboards
- Playbook source PDF list copied from the existing `docs/` folder

## Notes

The local workspace was empty, so this build is a fresh app shell based on the design handoff rather than a replacement inside an existing checked-out Streamlit codebase. Arena and Playbook data have now been pulled from `/Users/user/Claude/Projects/BanterONE`.

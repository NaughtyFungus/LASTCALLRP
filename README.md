# Last Call RP — Rules Site

Static rules website for Last Call RP. Hosted on GitHub Pages. Rules content is pulled automatically from Google Docs.

---

## Setup

### 1. Create the GitHub repo

1. Create a new public repo on GitHub (e.g. `lastcall-rp/rules`)
2. Push all these files to the `main` branch
3. Go to **Settings → Pages → Source** and set it to deploy from `main` / `/ (root)`

---

### 2. Connect your Discord

Open `config.json` and update the `discordUrl` field:

```json
{
  "discordUrl": "https://discord.gg/YOUR_INVITE_CODE",
  ...
}
```

---

### 3. Connect your Google Docs

For each section in `config.json`, add the Google Doc ID.

**To find the Doc ID:**
Open the Google Doc. The URL looks like:
```
https://docs.google.com/document/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ/edit
                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                    this is your Doc ID
```

**Make the doc public:**
In Google Docs: Share → Change to "Anyone with the link" → Viewer

**Add it to config.json:**
```json
{
  "sections": [
    {
      "id": "general",
      "title": "General Rules",
      "tag": "Section I",
      "file": "rules/general.html",
      "docId": "1aBcDeFgHiJkLmNoPqRsTuVwXyZ"
    },
    ...
  ]
}
```

---

### 4. Fetch the docs

**First-time fetch (manual):**
```bash
python3 fetch_docs.py
git add rules/
git commit -m "chore: initial rules fetch"
git push
```

**After that — automatic:**
The GitHub Action (`.github/workflows/fetch-docs.yml`) runs every 6 hours and re-fetches all docs automatically. If you want to trigger it manually: go to **Actions → Fetch Rules from Google Docs → Run workflow**.

---

## Adding or renaming sections

Edit the `sections` array in `config.json`. The site reads this file at runtime — no HTML edits needed. Run the fetch workflow after making changes.

---

## Local development

Just open `index.html` in a browser that allows local file fetching, or spin up a quick server:

```bash
python3 -m http.server 8080
```

Then visit `http://localhost:8080`.

---

## File structure

```
/
├── index.html              Main site
├── config.json             Discord URL + sections config
├── fetch_docs.py           Fetches Google Docs → rules/*.html
├── rules/
│   ├── general.html        Auto-generated (don't edit manually)
│   ├── rp-standards.html
│   ├── vehicle.html
│   ├── criminal.html
│   └── staff.html
└── .github/
    └── workflows/
        └── fetch-docs.yml  Auto-fetch schedule
```

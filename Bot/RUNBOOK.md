# WhatsApp Simple Bot - Runbook (Operations & Recovery)

This runbook explains how to operate, diagnose, and fully recover the WhatsApp Simple Bot on Windows/VPS.

## Directory Layout

- `Bot/bot.js`                 → Main bot (overlap-proof, daily limit, CSV)
- `Bot/bot.template.js`        → Known-good backup of bot.js (use to restore)
- `Bot/restore_bot_from_template.bat` → One-click restore of bot.js from template
- `Bot/send_history.json`      → Persistent history; prevents re-sends across restarts
- `Bot/schedules.simple.json`  → Saved schedules (daily & one-time)
- `Bot/.wwebjs_auth/`          → WhatsApp session (QR once; keep this folder)
- `Bot/catalog.pdf`            → Catalog to send (fallback: `Bot/catelog.pdf`)
- `output/all_contacts.csv`    → Contacts (A column = Name; `phone_number` col = phone)
- `Bot/Log.txt`                → Bot logs

## Common Operations

### Start the bot
```powershell
cd Bot
node bot.js
```
Scan the QR on first run (WhatsApp → Settings → Linked Devices → Link a device).

### Create a Daily CSV Schedule
- Menu option `3` → time `HH:MM` → optional message (blank = preset) → daily limit (default 100)
- At time, bot loads CSV, skips already-sent numbers (send_history.json), takes next `limit`, sends once, then waits for next day.

### One-time Schedule
- Menu option `4` → numbers comma-separated → message (blank = preset) → time `HH:MM` (today) or `YYYY-MM-DD HH:MM`.

### Send to CSV Immediately (Batch)
- Menu option `5` → message (blank = preset). Skips already-sent numbers.

### View/Cancel Schedules
- Menu option `6` → select schedule number to cancel.

## Troubleshooting

### 1) No QR / stuck on init
- Stop the bot
- Delete auth and cache folders:
```powershell
rmdir /s /q .wwebjs_auth
rmdir /s /q .wwebjs_cache
```
- Start again: `node bot.js` and scan QR.

### 2) Duplicate/overlapping sends
This bot is hardened against overlaps:
- Global run queue serializes all campaigns
- Daily schedule has `_running` lock & `_lastKey` (one run per minute)
- Per-run dedupe (`sendToMany`)
- Per-number in-flight guard & cooldown (2 minutes)
If you still see duplicates:
- Check `Bot/Log.txt` for "Running daily CSV schedule ..." repeated in same minute
- Ensure only one bot process is running (PM2/Systemd)

### 3) It’s re-sending numbers after restart
- `send_history.json` is the **source of truth**; if missing, it will resend
- Do not delete `send_history.json` unless you intend to reset targeting

### 4) Message failing
- Verify catalog file exists: `Bot/catalog.pdf` (or `Bot/catelog.pdf`)
- Verify CSV exists: `output/all_contacts.csv`
- Check the phone column is `phone_number` (fallback: `phone`, `Phone`)
- Phones must normalize to valid formats; 10-digit assumes India (91)

## Full Recovery (bot file corrupted)
1) Restore `bot.js` from the known-good template:
```powershell
cd Bot
restore_bot_from_template.bat
```
This overwrites `bot.js` with `bot.template.js`.

2) Reset WhatsApp session (if needed):
```powershell
rmdir /s /q .wwebjs_auth
node bot.js
```
Scan QR again.

3) Keep files between restarts:
- `.wwebjs_auth/`, `send_history.json`, `schedules.simple.json`.

## Self-check
Run the quick self-check script:
```powershell
cd Bot
node self_check.js
```
This validates presence of CSV, catalog, and readability of JSON files.

## Deployment (PM2 on VPS)
```bash
npm install -g pm2
pm2 start bot.js --name whatsapp-bot
pm2 save
pm2 startup   # follow printed instructions
pm2 logs whatsapp-bot -f
```

## Notes
- Default country code is `91` for 10-digit numbers. Change in `normalizePhone` if needed.
- All logs go to `Bot/Log.txt`.
- Daily schedules show as `Daily HH:MM (limit N/day)` in menu.

---
If anything breaks beyond this, restore from template and re-run. The template is the working, overlap-proof version.

#!/usr/bin/env node
/**
 * WhatsApp Simple Bot (overlap-proof)
 * - QR login (works on UI-less VPS)
 * - Send 1 / many / CSV
 * - One-time schedule (exact time)
 * - Daily CSV schedule at HH:MM with daily limit
 * - No overlapping runs, no duplicate sends
 */

const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');

// ---------- Helpers / Paths ----------
const DATA_DIR = __dirname;
const CATALOG_PATH = path.join(DATA_DIR, 'catalog.pdf'); // preferred
const CATELOG_FALLBACK = path.join(DATA_DIR, 'catelog.pdf'); // fallback
const PRESET_MESSAGE = `Dear {name},

Socho apke clients jab daily apka Logo dekhen
Keychain ya Phone Stand use karte waqt –
Tab apka Brand unke mind me hamesha rahega

 Perfect for Events, Gifting & Corporate Promotions
 Stylish + Useful Branding Combo

– Krishna Plastic`;

const SCHEDULES_PATH = path.join(DATA_DIR, 'schedules.simple.json');
const LEGACY_SENT_PATH = path.join(DATA_DIR, 'sent.simple.json'); // old file, read-only
const HISTORY_PATH = path.join(DATA_DIR, 'send_history.json'); // primary
const CONTACTS_CSV = path.join(DATA_DIR, '..', 'output', 'all_contacts.csv');
const LOG_PATH = path.join(DATA_DIR, 'Log.txt');

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(msg);
  try { fs.appendFileSync(LOG_PATH, line + '\n'); } catch {}
}

function ensureJsonFile(file, fallback) {
  if (!fs.existsSync(file)) {
    fs.writeFileSync(file, JSON.stringify(fallback, null, 2));
    return fallback;
  }
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch {
    fs.writeFileSync(file, JSON.stringify(fallback, null, 2));
    return fallback;
  }
}

function normalizePhone(raw) {
  let p = (raw || '').toString().trim();
  p = p.replace(/[^\d]/g, '');
  if (!p) return null;
  p = p.replace(/^0+/, '');
  if (p.length === 10) return '91' + p;          // default 91 for 10-digit local
  if (p.length === 12 && p.startsWith('91')) return p;
  if (p.length >= 11 && p.length <= 15) return p;
  return null;
}
function toJid(raw) {
  const n = normalizePhone(raw);
  return n ? n + '@c.us' : null;
}
function nextId() { return Date.now().toString(36); }

// ---------- Bot ----------
class SimpleWhatsAppBot {
  constructor() {
    this.client = new Client({
      authStrategy: new LocalAuth({
        clientId: 'simple-bot',
        dataPath: path.join(DATA_DIR, '.wwebjs_auth')
      }),
      puppeteer: {
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-gpu',
          '--no-first-run',
        ],
        timeout: 120000
      }
    });

    this.rl = null;
    this.schedules = ensureJsonFile(SCHEDULES_PATH, []);
    this.legacySent = ensureJsonFile(LEGACY_SENT_PATH, []); // read-only
    this.history = ensureJsonFile(HISTORY_PATH, { byNumber: {} }); // {byNumber: {'9198...':{firstAt,lastAt,count}}}

    // Overlap-proof guards
    this.queuePromise = Promise.resolve(); // serialize all runs
    this.inFlight = new Set();            // per-number currently being processed
    this.lastSendAt = Object.create(null);
    this.cooldownMs = 2 * 60 * 1000;      // 2 minutes cooldown per number (adjust if needed)

    this.schedulerTimer = null;

    this.setupEvents();
    log('Starting WhatsApp Simple Bot...');
    this.client.initialize();
  }

  // ---- Run serialization ----
  enqueueRun(fn) {
    this.queuePromise = this.queuePromise.then(async () => {
      try { await fn(); }
      catch (e) { log('Run error: ' + (e?.message || e)); }
    });
    return this.queuePromise;
  }

  // ---- Session Events ----
  setupEvents() {
    this.client.on('qr', (qr) => {
      log('QR: WhatsApp → Settings → Linked Devices → Link a Device');
      qrcode.generate(qr, { small: true });
    });
    this.client.on('authenticated', () => log('Authenticated successfully'));
    this.client.on('ready', () => {
      log('WhatsApp client is ready');
      this.startScheduler();
      this.mainMenu();
    });
    this.client.on('auth_failure', (m) => log('Auth failure: ' + m));
    this.client.on('disconnected', (r) => log('Disconnected: ' + r));
    this.client.on('error', (e) => log('Client error: ' + (e?.message || e)));
  }

  // ---- Scheduler ----
  startScheduler() {
    if (this.schedulerTimer) clearInterval(this.schedulerTimer);
    this.schedulerTimer = setInterval(() => this.tickSchedules(), 10 * 1000); // every 10s
    log('Scheduler started (tick every 10s)');
  }
  saveSchedules() { fs.writeFileSync(SCHEDULES_PATH, JSON.stringify(this.schedules, null, 2)); }
  saveHistory() { fs.writeFileSync(HISTORY_PATH, JSON.stringify(this.history, null, 2)); }

  hasAlreadySent(numberRaw) {
    const n = normalizePhone(numberRaw);
    if (!n) return false;
    if (this.history?.byNumber?.[n]) return true; // primary
    // fallback legacy
    const jid = n + '@c.us';
    return this.legacySent.some(e => e.jid === jid || (e.jid || '').replace('@c.us', '') === n);
  }

  async tickSchedules() {
    // One-time schedules: run once when due
    // Daily CSV schedules: run once per day at HH:MM with limit N

    const nowMs = Date.now();
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, '0');
    const mm = String(now.getMinutes()).padStart(2, '0');
    const hhmmNow = `${hh}:${mm}`;

    for (const s of this.schedules) {
      if (s.type === 'one-time') {
        if (s.executed) continue;
        const whenMs = new Date(s.when).getTime();
        if (!isFinite(whenMs)) continue;

        if (nowMs >= whenMs) {
          log(`Running schedule ${s.id} - ${s.title}`);
          try {
            await this.enqueueRun(() => this.sendToMany(s.numbers, s.message));
            s.executed = true;
            s.executedAt = new Date().toISOString();
            this.saveSchedules();
            log(`Schedule ${s.id} completed`);
          } catch (e) {
            log(`Schedule ${s.id} failed: ${e?.message || e}`);
          }
        }
      } else if (s.type === 'daily-csv') {
        const limit = Math.max(1, Number(s.dailyLimit) || 100);

        // unique key = today at HH:MM
        const todayKey = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')} ${hhmmNow}`;

        if (s._lastKey === todayKey) continue; // already done this minute
        if (!s.hhmm || s.hhmm !== hhmmNow) continue;
        if (s._running) continue; // already running

        // lock & mark minute before sending
        s._running = true;
        s._lastKey = todayKey;
        this.saveSchedules();

        log(`Running daily CSV schedule ${s.id} at ${hhmmNow}`);
        try {
          const contacts = await this.readContactsFromCsv();
          // filter out already-sent numbers and take only 'limit'
          const filtered = [];
          for (const c of contacts) {
            if (filtered.length >= limit) break;
            if (!this.hasAlreadySent(c.raw)) filtered.push(c);
          }
          await this.enqueueRun(() => this.sendToMany(filtered, s.message || ''));
          log(`Daily CSV schedule ${s.id} completed`);
        } catch (e) {
          log(`Daily CSV schedule ${s.id} failed: ${e?.message || e}`);
        } finally {
          s._running = false;
          this.saveSchedules();
        }
      }
    }
  }

  // ---- Sending ----
  async sendToOne(recipient, message) {
    const usePreset = !message || !message.trim();

    const isObj = typeof recipient === 'object' && recipient !== null;
    const rawNumber = isObj ? recipient.raw : recipient;
    const csvName = isObj ? (recipient.name || '') : '';

    const norm = normalizePhone(rawNumber);
    const jid = norm ? norm + '@c.us' : null;
    if (!jid) {
      log(`Invalid phone number: "${rawNumber}"`);
      return false;
    }

    // Skip if already sent (persisted)
    if (this.hasAlreadySent(rawNumber)) {
      log(`Skipping already-sent number: ${norm}`);
      return true;
    }

    // Per-number in-flight guard
    if (this.inFlight.has(norm)) {
      log(`In-flight skip: ${norm} is already being processed`);
      return true;
    }
    // Cooldown (optional)
    const last = this.lastSendAt[norm];
    const nowTs = Date.now();
    if (last && nowTs - last < this.cooldownMs) {
      log(`Cooldown skip: ${norm} sent ${Math.round((nowTs - last)/1000)}s ago`);
      return true;
    }

    this.inFlight.add(norm);
    try {
      log(`Sending to ${jid} ...`);

      // 1) Catalog
      let catPath = CATALOG_PATH;
      if (!fs.existsSync(catPath) && fs.existsSync(CATELOG_FALLBACK)) {
        catPath = CATELOG_FALLBACK;
      }
      if (fs.existsSync(catPath)) {
        try {
          const media = MessageMedia.fromFilePath(catPath);
          await this.client.sendMessage(jid, media);
          log(`Catalog sent to ${jid}`);
          await new Promise(r => setTimeout(r, 1500));
        } catch (e) {
          log(`Catalog send failed to ${jid}: ${e?.message || e}`);
        }
      } else {
        log(`Catalog not found (checked: catalog.pdf / catelog.pdf) – skipping attachment`);
      }

      // 2) Text
      const nameGuess = csvName || 'Sir/Madam';
      const finalText = usePreset ? PRESET_MESSAGE.replace('{name}', nameGuess) : message;
      await this.client.sendMessage(jid, finalText);
      log(`Text sent to ${jid}`);

      // 3) Update history immediately after text
      try {
        const now = new Date().toISOString();
        if (!this.history.byNumber[norm]) {
          this.history.byNumber[norm] = { firstAt: now, lastAt: now, count: 1 };
        } else {
          this.history.byNumber[norm].lastAt = now;
          this.history.byNumber[norm].count += 1;
        }
        this.saveHistory();
        this.lastSendAt[norm] = Date.now();
      } catch (e) {
        log('History write failed: ' + (e?.message || e));
      }

      // 4) Archive
      try {
        const chat = await this.client.getChatById(jid);
        if (chat && chat.archive) {
          await chat.archive();
          log(`Archived chat for ${jid}`);
        }
      } catch (e) {
        log(`Archive failed for ${jid}: ${e?.message || e}`);
      }

      return true;
    } catch (e) {
      log(`Send failed to ${jid}: ${e?.message || e}`);
      return false;
    } finally {
      this.inFlight.delete(norm);
    }
  }

  async sendToMany(numbersRaw, message) {
    // Deduplicate within this run
    const seen = new Set();
    let ok = 0, fail = 0;

    for (const entry of (numbersRaw || [])) {
      const item = (typeof entry === 'object' && entry.raw) ? entry : { raw: entry, name: undefined };
      const norm = normalizePhone(item.raw);
      if (!norm) continue;
      if (seen.has(norm)) continue;
      seen.add(norm);

      const success = await this.sendToOne(item, message || '');
      if (success) ok++; else fail++;

      await new Promise(r => setTimeout(r, 1500 + Math.random() * 1500));
    }
    log(`Batch done. Success: ${ok}, Fail: ${fail}`);
  }

  // ---- CSV ----
  async readContactsFromCsv() {
    return new Promise((resolve) => {
      const contacts = [];
      if (!fs.existsSync(CONTACTS_CSV)) {
        log(`CSV not found at ${CONTACTS_CSV}`);
        return resolve([]);
      }
      fs.createReadStream(CONTACTS_CSV)
        .pipe(csv())
        .on('data', (row) => {
          const keys = Object.keys(row);
          const firstCol = keys.length ? row[keys[0]] : '';
          const name = (firstCol || row.name || row.Name || '').toString().trim();
          const raw = (row.phone_number || row.phone || row.Phone || '').toString().trim();
          if (!raw) return;
          contacts.push({ name, raw });
        })
        .on('end', () => resolve(contacts))
        .on('error', (e) => { log('CSV read error: ' + e.message); resolve([]); });
    });
  }

  // ---- UI ----
  readline() {
    if (this.rl) this.rl.close();
    const rl = require('readline').createInterface({ input: process.stdin, output: process.stdout });
    this.rl = rl; return rl;
  }

  mainMenu() {
    const rl = this.readline();
    console.log('\n' + '='.repeat(50));
    console.log('WhatsApp Simple Bot');
    console.log('='.repeat(50));
    console.log('1) Send message to ONE number');
    console.log('2) Send message to MULTIPLE numbers (comma-separated)');
    console.log('3) Create DAILY schedule (send to CSV at HH:MM every day)');
    console.log('4) Create ONE-TIME schedule');
    console.log('5) Send to CSV (output/all_contacts.csv)');
    console.log('6) View/Cancel schedules');
    console.log('7) Reset WhatsApp session (clear auth, keep history)');
    console.log('8) Reset send history (clear send_history.json)');
    console.log('9) Exit');

    rl.question('Choose option: ', (ans) => {
      rl.close();
      switch ((ans || '').trim()) {
        case '1': return this.menuSendOne();
        case '2': return this.menuSendMany();
        case '3': return this.menuCreateDailySchedule();
        case '4': return this.menuCreateOneTimeSchedule();
        case '5': return this.enqueueRun(() => this.menuSendFromCsv());
        case '6': return this.menuSchedules();
        case '7': return this.menuResetAuth();
        case '8': return this.menuResetHistory();
        case '9':
          log('Goodbye');
          process.exit(0);
        default:
          console.log('Invalid option');
          return this.mainMenu();
      }
    });
  }

  menuSendOne() {
    const rl = this.readline();
    rl.question('Enter phone (e.g. 919876543210 or 9876543210): ', (num) => {
      rl.question('Enter message: ', async (msg) => {
        rl.close();
        await this.enqueueRun(() => this.sendToOne(num, msg));
        this.mainMenu();
      });
    });
  }

  menuSendMany() {
    const rl = this.readline();
    rl.question('Enter numbers comma-separated: ', (line) => {
      const numbers = (line || '').split(',').map(s => s.trim()).filter(Boolean);
      rl.question('Enter message: ', async (msg) => {
        rl.close();
        await this.enqueueRun(() => this.sendToMany(numbers, msg));
        this.mainMenu();
      });
    });
  }

  menuCreateOneTimeSchedule() {
    const rl = this.readline();
    rl.question('Enter numbers comma-separated: ', (line) => {
      const numbers = (line || '').split(',').map(s => s.trim()).filter(Boolean);
      rl.question('Enter message: ', (msg) => {
        rl.question('Enter date/time (YYYY-MM-DD HH:MM, or HH:MM for today): ', (dt) => {
          rl.close();
          const whenIso = this.parseDateTime(dt);
          if (!whenIso) {
            console.log('Invalid date/time format. Use YYYY-MM-DD HH:MM or HH:MM (24h).');
            return this.mainMenu();
          }
          const s = {
            id: nextId(),
            type: 'one-time',
            title: `One-time ${new Date(whenIso).toLocaleString()}`,
            numbers,
            message: msg || '',
            when: whenIso,
            executed: false
          };
          this.schedules.push(s);
          this.saveSchedules();
          log(`Created one-time schedule ${s.id} at ${whenIso}`);
          this.mainMenu();
        });
      });
    });
  }

  parseDateTime(input) {
    const s = (input || '').trim();
    let m = s.match(/^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})$/);
    if (!m) {
      const m2 = s.match(/^(\d{2}):(\d{2})$/);
      if (!m2) return null;
      const now = new Date();
      const [_, hh, mm] = m2;
      const dt = new Date(now.getFullYear(), now.getMonth(), now.getDate(), Number(hh), Number(mm), 0, 0);
      return isNaN(dt.getTime()) ? null : dt.toISOString();
    }
    const [_, y, mo, d, h, mi] = m;
    const dt = new Date(Number(y), Number(mo) - 1, Number(d), Number(h), Number(mi), 0, 0);
    return isNaN(dt.getTime()) ? null : dt.toISOString();
  }

  async menuSendFromCsv() {
    const contacts = await this.readContactsFromCsv();
    if (!contacts.length) {
      console.log('No contacts found in CSV.');
      return this.mainMenu();
    }
    console.log(`Loaded ${contacts.length} contacts from CSV.`);
    const rl = this.readline();
    rl.question('Enter message (leave empty to use preset): ', async (msg) => {
      rl.close();
      await this.enqueueRun(() => this.sendToMany(contacts, msg));
      this.mainMenu();
    });
  }

  menuCreateDailySchedule() {
    const rl = this.readline();
    rl.question('Enter time HH:MM (24h): ', (time) => {
      rl.question('Enter message (leave empty to use preset): ', (msg) => {
        rl.question('Enter daily limit (default 100): ', (lim) => {
          rl.close();
          const dailyLimit = Math.max(1, parseInt(lim || '100', 10) || 100);
          const s = {
            id: nextId(),
            type: 'daily-csv',
            title: `Daily ${time} (limit ${dailyLimit}/day)`,
            hhmm: time,
            message: msg || '',
            dailyLimit
          };
          this.schedules.push(s);
          this.saveSchedules();
          log(`Created daily schedule ${s.id} at ${time} (limit ${dailyLimit}/day)`);
          this.mainMenu();
        });
      });
    });
  }

  async clearAuthFolder() {
    const dir = path.join(DATA_DIR, '.wwebjs_auth');
    try {
      if (fs.existsSync(dir)) {
        fs.rmSync(dir, { recursive: true, force: true });
        log('Cleared WhatsApp auth (.wwebjs_auth)');
      } else {
        log('Auth folder not found (.wwebjs_auth)');
      }
    } catch (e) {
      log('Failed to clear auth: ' + (e?.message || e));
    }
  }

  menuResetAuth() {
    const rl = this.readline();
    console.log('This will clear WhatsApp auth and require re-scanning QR. Send history is kept.');
    rl.question('Proceed? (y/N): ', async (ans) => {
      rl.close();
      if ((ans || '').trim().toLowerCase() !== 'y') return this.mainMenu();
      try {
        // stop client if needed
        try { await this.client.destroy(); } catch {}
        await this.clearAuthFolder();
        // re-init client
        this.client = new Client({
          authStrategy: new LocalAuth({ clientId: 'simple-bot', dataPath: path.join(DATA_DIR, '.wwebjs_auth') }),
          puppeteer: { headless: true, args: ['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage','--disable-gpu','--no-first-run'], timeout: 120000 }
        });
        this.setupEvents();
        this.client.initialize();
        log('Client re-initialized. Please scan the new QR code.');
      } catch (e) {
        log('Reset auth failed: ' + (e?.message || e));
      }
      this.mainMenu();
    });
  }

  menuResetHistory() {
    const rl = this.readline();
    console.log('This will clear send_history.json. The bot may re-send to previous numbers.');
    rl.question('Proceed? (y/N): ', (ans) => {
      rl.close();
      if ((ans || '').trim().toLowerCase() !== 'y') return this.mainMenu();
      try {
        this.history = { byNumber: {} };
        this.saveHistory();
        log('Cleared send_history.json');
      } catch (e) {
        log('Reset history failed: ' + (e?.message || e));
      }
      this.mainMenu();
    });
  }

  menuSchedules() {
    if (!this.schedules.length) {
      console.log('No schedules.');
      return this.mainMenu();
    }
    console.log('\nActive schedules:');
    this.schedules.forEach((s, i) => {
      if (s.type === 'daily-csv') {
        console.log(`${i + 1}. [DAILY] ${s.id} - Daily ${s.hhmm} (limit ${s.dailyLimit || 100}/day)`);
      } else {
        console.log(`${i + 1}. [${s.executed ? 'DONE' : 'PENDING'}] ${s.id} - ${s.title}`);
      }
    });
    const rl = this.readline();
    rl.question('Enter number to cancel, or press Enter to go back: ', (ans) => {
      rl.close();
      const idx = Number(ans) - 1;
      if (!ans) return this.mainMenu();
      if (isNaN(idx) || idx < 0 || idx >= this.schedules.length) {
        console.log('Invalid selection');
        return this.mainMenu();
      }
      const del = this.schedules.splice(idx, 1)[0];
      this.saveSchedules();
      log(`Cancelled schedule ${del.id}`);
      this.mainMenu();
    });
  }
}

// Start
new SimpleWhatsAppBot();

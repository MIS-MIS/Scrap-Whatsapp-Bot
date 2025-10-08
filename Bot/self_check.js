#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const files = [
  { p: path.join(ROOT, 'bot.js'),       req: true,  desc: 'Main bot file' },
  { p: path.join(ROOT, 'bot.template.js'), req: false, desc: 'Template fallback' },
  { p: path.join(ROOT, 'send_history.json'), req: false, desc: 'Send history (skip re-sends)' },
  { p: path.join(ROOT, 'schedules.simple.json'), req: false, desc: 'Schedules storage' },
  { p: path.join(ROOT, 'catalog.pdf'),  req: false, desc: 'Catalog (preferred)' },
  { p: path.join(ROOT, 'catelog.pdf'),  req: false, desc: 'Catalog fallback' },
  { p: path.join(ROOT, '..', 'output', 'all_contacts.csv'), req: false, desc: 'Contacts CSV' },
];

let ok = true;
console.log('Self-check:');
for (const f of files) {
  const exists = fs.existsSync(f.p);
  console.log(`- ${f.desc}: ${exists ? 'OK' : 'Missing'} (${f.p})`);
  if (f.req && !exists) ok = false;
}

if (!ok) {
  console.log('Some required files are missing. Please restore or run restore_bot_from_template.bat');
  process.exit(1);
}
console.log('All checks passed.');

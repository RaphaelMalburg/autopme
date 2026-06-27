'use strict';

// Baileys WhatsApp gateway for AutoPME Demo Studio.
// Node sidecar (default port 3001). Provides QR, send text, send media, and
// forwards incoming messages (with media) to the FastAPI app at
//   http://localhost:8000/api/whatsapp/webhook
//
// Start:
//   npm install
//   node index.js
// Then scan the QR printed in the terminal with WhatsApp > Linked devices,
// or fetch it from GET http://localhost:3001/qr.
//
// Env overrides:
//   GATEWAY_PORT     (default 3001)
//   APP_WEBHOOK_URL  (default http://localhost:8000/api/whatsapp/webhook)

const express = require('express');
const qrcode = require('qrcode-terminal');
const path = require('path');
const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
  downloadContentFromMessage,
} = require('baileys');

const PORT = parseInt(process.env.PORT || process.env.GATEWAY_PORT || '3001', 10);
const APP_WEBHOOK = process.env.APP_WEBHOOK_URL || 'http://localhost:8000/api/whatsapp/webhook';
// AUTH_DIR override permite montar um volume persistente em cloud (ex.: /data/baileys_auth)
// para a sessao WhatsApp nao se perder a cada redeploy.
const AUTH_DIR = process.env.AUTH_DIR || path.join(__dirname, 'baileys_auth');

const app = express();
app.use(express.json({ limit: '64mb' }));

// --- State shared between Baileys and the REST API ---
let sock = null;
let lastQR = null;
let connectionStatus = 'connecting'; // connecting | waiting | connected | disconnected

// --- Baileys connection ---
async function startSocket() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

  let version;
  try {
    const fetched = await fetchLatestBaileysVersion();
    version = fetched && fetched.version;
  } catch (e) {
    console.warn('[gateway] fetchLatestBaileysVersion failed, using bundled default:', e.message);
  }

  const socketOpts = {
    auth: state,
    printQRInTerminal: false, // we print the QR ourselves below
    browser: ['AutoPME Demo', 'Chrome', '1.0.0'],
  };
  if (version) socketOpts.version = version;

  sock = makeWASocket(socketOpts);

  sock.ev.on('creds.update', saveCreds);

  sock.ev.on('connection.update', (update) => {
    const { connection, qr, lastDisconnect } = update || {};
    if (qr) {
      lastQR = qr;
      connectionStatus = 'waiting';
      console.log('[gateway] Scan this QR with WhatsApp > Linked devices:');
      qrcode.generate(qr, { small: true });
    }
    if (connection === 'open') {
      connectionStatus = 'connected';
      lastQR = null;
      console.log('[gateway] WhatsApp connected');
    }
    if (connection === 'close') {
      const statusCode =
        lastDisconnect && lastDisconnect.error && lastDisconnect.error.output
          ? lastDisconnect.error.output.statusCode
          : undefined;
      connectionStatus = 'disconnected';
      if (statusCode === DisconnectReason.loggedOut) {
        console.log('[gateway] Logged out. Remove the "baileys_auth" folder to re-scan.');
      } else {
        console.log('[gateway] Connection closed (%s), reconnecting...', statusCode);
        startSocket().catch((e) => console.error('[gateway] reconnect error:', e));
      }
    }
  });

  sock.ev.on('messages.upsert', async ({ messages, type }) => {
    // Only process live (not historical) messages.
    if (type !== 'notify') return;
    for (const msg of messages || []) {
      try {
        await handleIncomingMessage(msg);
      } catch (e) {
        console.error('[gateway] handleIncomingMessage error:', e);
      }
    }
  });
}

async function handleIncomingMessage(msg) {
  if (!msg.message || msg.key.fromMe) return;

  const from = msg.key.remoteJid; // e.g. 3519xxxxxxxx@s.whatsapp.com
  const messageContent = extractText(msg.message);
  const mediaInfo = detectMedia(msg.message);
  const hasMedia = !!mediaInfo;

  let mediaBase64 = null;
  let mimetype = null;
  let filename = null;

  if (hasMedia) {
    try {
      const buffer = await downloadMediaBuffer(msg, mediaInfo);
      if (buffer) {
        mediaBase64 = buffer.toString('base64');
        mimetype = mediaInfo.mimetype || 'application/octet-stream';
        filename = mediaInfo.fileName || defaultFilename(mimetype);
      }
    } catch (e) {
      console.error('[gateway] media download error:', e);
    }
  }

  const payload = {
    from,
    message: messageContent,
    hasMedia,
    mediaBase64,
    mimetype,
    filename,
  };

  // Forward to the FastAPI app (fire-and-forget with logging).
  try {
    const res = await fetch(APP_WEBHOOK, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    console.log('[gateway] webhook -> %s (from %s)', res.status, from);
  } catch (e) {
    console.error('[gateway] webhook POST failed:', e.message);
  }
}

const MEDIA_TYPES = {
  imageMessage: 'image',
  videoMessage: 'video',
  stickerMessage: 'sticker',
  documentMessage: 'document',
  audioMessage: 'audio',
};

function detectMedia(message) {
  if (!message) return null;
  for (const [key, type] of Object.entries(MEDIA_TYPES)) {
    const m = message[key];
    if (m) {
      return { key, type, mimetype: m.mimetype, fileName: m.fileName };
    }
  }
  return null;
}

function extractText(message) {
  if (!message) return '';
  return (
    message.conversation ||
    (message.extendedTextMessage && message.extendedTextMessage.text) ||
    (message.imageMessage && message.imageMessage.caption) ||
    (message.videoMessage && message.videoMessage.caption) ||
    ''
  );
}

function defaultFilename(mimetype) {
  const sub = (mimetype || '').split('/')[1] || 'bin';
  return `media.${sub.split('+')[0]}`;
}

async function downloadMediaBuffer(msg, mediaInfo) {
  // Preferred: sock.downloadMediaMessage (returns a Buffer in Baileys 6.x).
  if (sock && typeof sock.downloadMediaMessage === 'function') {
    try {
      const buf = await sock.downloadMediaMessage(msg);
      if (buf) return Buffer.from(buf);
    } catch (e) {
      console.warn('[gateway] downloadMediaMessage failed, falling back:', e.message);
    }
  }
  // Fallback: downloadContentFromMessage stream.
  const m = msg.message && msg.message[mediaInfo.key];
  if (!m || typeof downloadContentFromMessage !== 'function') return null;
  const stream = await downloadContentFromMessage(m, mediaInfo.type);
  const chunks = [];
  for await (const chunk of stream) chunks.push(chunk);
  return Buffer.concat(chunks);
}

// --- REST API ---
app.get('/health', (req, res) => res.json({ ok: true, status: connectionStatus }));

app.get('/qr', (req, res) => {
  res.json({ qr: lastQR, status: connectionStatus });
});

app.get('/status', (req, res) => {
  res.json({ status: connectionStatus });
});

app.post('/send', async (req, res) => {
  const { to, message } = req.body || {};
  if (!to || !message) {
    return res.status(400).json({ ok: false, error: 'to and message are required' });
  }
  if (!sock || connectionStatus !== 'connected') {
    return res.status(503).json({ ok: false, error: `whatsapp_not_connected:${connectionStatus}` });
  }
  try {
    const sent = await sock.sendMessage(normalizeJid(to), { text: message });
    res.json({ ok: true, messageId: sent && sent.key && sent.key.id });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.post('/send-media', async (req, res) => {
  const { to, fileBase64, filename, mimetype, caption } = req.body || {};
  if (!to || !fileBase64) {
    return res.status(400).json({ ok: false, error: 'to and fileBase64 are required' });
  }
  if (!sock || connectionStatus !== 'connected') {
    return res.status(503).json({ ok: false, error: `whatsapp_not_connected:${connectionStatus}` });
  }
  try {
    const buffer = Buffer.from(fileBase64, 'base64');
    const mt = mimetype || 'application/octet-stream';
    const opts = { caption: caption || '' };
    if (mt.startsWith('image/')) {
      opts.image = buffer;
      opts.mimetype = mt;
    } else {
      opts.document = buffer;
      opts.mimetype = mt;
      opts.fileName = filename || 'documento';
    }
    const sent = await sock.sendMessage(normalizeJid(to), opts);
    res.json({ ok: true, messageId: sent && sent.key && sent.key.id });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

function normalizeJid(to) {
  if (to.includes('@')) return to;
  const digits = to.replace(/\D/g, '');
  return `${digits}@s.whatsapp.com`;
}

app.listen(PORT, () => {
  console.log(`[gateway] REST listening on http://localhost:${PORT}`);
  console.log(`[gateway] forwarding incoming messages to ${APP_WEBHOOK}`);
  startSocket().catch((e) => console.error('[gateway] startSocket error:', e));
});

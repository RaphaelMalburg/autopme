# AutoPME WhatsApp Gateway (Baileys)

Node.js sidecar that connects to WhatsApp via [Baileys](https://github.com/WhiskeySockets/Baileys)
and exposes a small REST API for the AutoPME Demo Studio backend. It prints a QR for
linking a device, sends text/media, and forwards every incoming message (with media)
to the FastAPI app's webhook so documents can be ingested.

## Prerequisites

- Node.js >= 18 (uses the global `fetch` API).
- A phone with WhatsApp installed (to scan the QR and link this as a "Linked device").

## Install & run

```bash
cd app/whatsapp/gateway
npm install
node index.js
```

A QR code is printed in the terminal. Open WhatsApp on the phone > **Settings >
Linked devices > Link a device** and scan it. The session is persisted in
`./baileys_auth` (gitignored), so you only scan once.

## Configuration (env, all optional)

| Variable         | Default                                          | Purpose                                  |
|------------------|--------------------------------------------------|------------------------------------------|
| `GATEWAY_PORT`   | `3001`                                           | REST port the Python client talks to.    |
| `APP_WEBHOOK_URL`| `http://localhost:8000/api/whatsapp/webhook`     | Where incoming messages are forwarded.   |

## REST API

### `GET /qr`
Returns `{"qr": "<ascii qr string or null>", "status": "waiting|connected|connecting|disconnected"}`.

### `GET /status`
Returns `{"status": "..."}`.

### `GET /health`
Returns `{"ok": true, "status": "..."}`.

### `POST /send`
Send a text message.
```json
{ "to": "351912345678", "message": "Ola" }
```
Returns `{"ok": true, "messageId": "..."}`. `to` may be a bare number or a full JID.

### `POST /send-media`
Send an image or document as base64 (JSON, no multipart).
```json
{
  "to": "351912345678",
  "fileBase64": "<base64>",
  "filename": "menu.png",
  "mimetype": "image/png",
  "caption": ""
}
```
Images are sent as `image`; anything else as `document`. Returns `{"ok": true, "messageId": "..."}`.

## Incoming message flow

On `messages.upsert` (live messages only), the gateway:

1. Extracts the sender JID and any text/caption.
2. Detects media (image/video/document/sticker/audio) and downloads it as a Buffer.
3. POSTs to `APP_WEBHOOK_URL`:
   ```json
   {
     "from": "3519xxxxxxxx@s.whatsapp.com",
     "message": "<text or caption>",
     "hasMedia": true,
     "mediaBase64": "<base64 or null>",
     "mimetype": "image/png",
     "filename": "menu.png"
   }
   ```
4. The FastAPI `/api/whatsapp/webhook` handler decodes the media, runs document
   ingestion, emails the result, and replies to the sender.

## Notes

- Only the three deps in `package.json` are required: `baileys`, `express`,
  `qrcode-terminal`. No `multer`/`boom` — media upload uses base64 JSON and error
  status codes are read directly from the Baileys error object.
- `baileys_auth/` and `node_modules/` are gitignored.
- Baileys pins to the stable 6.x line (`^6.7.23`); the 7.0 RC is avoided.

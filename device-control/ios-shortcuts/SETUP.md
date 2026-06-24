# Eric on iPhone — Shortcuts + Pushcut setup

Apple does not allow any third-party service to remotely control an iPhone
directly — this is a deliberate iOS security boundary, not a gap in this
build. The sanctioned way around it is **Shortcuts**, triggered by a push
notification from **Pushcut** (free tier: 30 notifications/month, enough
for personal use; upgrade only if you outgrow it).

## How it works
1. Eric (n8n) decides a phone action is needed (e.g. "turn on HomeKit lights",
   "send me a text", "set a 10 minute timer", "open Maps to X").
2. n8n calls Pushcut's webhook API with the shortcut name + parameters.
3. Pushcut sends a silent or visible push notification to your iPhone.
4. The notification triggers a Shortcut, which runs natively on your phone —
   full access to HomeKit, Reminders, Messages, Maps, Calendar, Files, etc.
5. The Shortcut can optionally call back to n8n with the result, which Eric
   then logs to Telegram.

## Setup steps

### 1. Install Pushcut (free) on your iPhone
- App Store -> Pushcut
- Open it, go to Notifications tab, create a new notification named `eric_action`
- Under "Actions", add: Run Shortcut -> (you'll build this next)
- Copy your personal API key from Pushcut Settings -> API

### 2. Build the receiving Shortcut
- Open Shortcuts app -> + -> name it `Eric Run Action`
- Add action: "Get Contents of URL" is NOT needed here — Pushcut already
  delivers the payload as Shortcut input.
- Add action: "Get Dictionary from Input" to parse the JSON Pushcut sends.
- Add a "Choose from Menu" or series of "If" blocks keyed on a `command`
  field, e.g.:
  - If command is `lock_home` -> Control HomeKit accessory -> Lock front door
  - If command is `lights_on` -> Control HomeKit accessory -> turn on scene
  - If command is `send_text` -> Send Message action using the `message` and
    `recipient` fields from input
  - If command is `set_timer` -> Start Timer using `duration` field
- At the end, add "Get Contents of URL" -> POST to
  `https://YOUR_N8N_HOST/webhook/eric-device-result`
  with body `{ "device": "iphone", "result": "<describe what happened>" }`
  so Eric reports back to you on Telegram.

### 3. Wire it into n8n
In the Eric orchestrator, add an HTTP Request node:
- URL: `https://api.pushcut.io/v1/notifications/eric_action`
- Method: POST
- Header: `API-Key: YOUR_PUSHCUT_API_KEY`
- Body:
  ```json
  {
    "title": "Eric",
    "text": "Running: {{ $json.command }}",
    "input": {
      "command": "{{ $json.deviceAction }}",
      "params": "{{ $json.deviceParams }}"
    }
  }
  ```

## What this realistically gets you
- HomeKit device control (lights, locks, plugs, thermostats — anything
  already in your Apple Home app)
- Sending texts/iMessages on your behalf
- Setting timers, reminders, calendar events
- Opening apps/URLs, running any other native Shortcut action

## What it does NOT get you
- Reading your screen, screenshots, or arbitrary app control outside what
  Shortcuts actions expose
- Working when your phone is off, in airplane mode, or has no signal
- Anything Apple's Shortcuts sandbox doesn't expose as an action — this is
  an Apple-imposed ceiling, not something workaroundable

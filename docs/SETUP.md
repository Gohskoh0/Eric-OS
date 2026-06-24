# Eric — Setup Guide

Everything Eric needs has been generated. This is the order to wire it up.
Nothing here costs money if you stay on free tiers, with one caveat noted
in step 6 (LinkedIn).

## 0. What you're deploying
- **n8n** — Eric's brain. Routes every command, checks memory, fires actions.
- **Chroma** — Eric's memory. Stores your corrections, gets queried before
  every decision.
- **Lovable web app** — voice UI in your browser/phone.
- **Telegram bot** — voice/text input + the channel ALL logs come back to.
- **Hugging Face** — hosts the open-source models (Whisper for speech-to-text,
  Qwen2.5-Coder for code generation) — both free via the Inference API.
- **Windows agent** — small script on your laptop, polls for commands.
- **iPhone (Pushcut + Shortcuts)** — receives push-triggered actions.

## 1. Stand up the backend (n8n + Chroma)
1. Create a free account on Render.com (or Railway/Fly.io).
2. New "Web Service" -> connect this repo (or upload the docker-compose.yml).
3. Set environment variables from `.env.example` — fill in real values.
4. Deploy. Your n8n instance will be live at `https://your-app-name.onrender.com`.
5. Log into n8n with the basic auth user/password you set.
6. Import both workflow files from `n8n-workflows/`:
   `eric-main-orchestrator.json` and `eric-device-queue.json`
   (n8n -> Workflows -> Import from File).

**Free tier reality check**: Render's free web services sleep after 15
minutes of no traffic and take ~30-60s to wake on the next request. For an
assistant you talk to occasionally, this means your first command after a
gap gets a delayed response — not broken, just slow to wake. If this
bothers you, Railway's free tier behaves similarly; there's no fully free
tier anywhere that stays warm 24/7 without eventually asking for a card.

## 2. Create the Telegram bot ("Eric")
1. Message **@BotFather** on Telegram.
2. `/newbot` -> name it Eric -> get your `TELEGRAM_BOT_TOKEN`.
3. Send Eric a message once, then visit
   `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your `chat.id`.
4. Put both into your `.env`.
5. In n8n, add Telegram credentials (Credentials -> New -> Telegram API).
6. In the Telegram bot settings (BotFather -> /setdomain or webhook), point
   the bot's webhook to: `https://your-app-name.onrender.com/webhook/eric-inbound`

## 3. Get Hugging Face access (free)
1. Create an account at huggingface.co.
2. Settings -> Access Tokens -> create a read token.
3. Put it in `.env` as `HUGGINGFACE_API_TOKEN`.
4. In n8n, create a "Header Auth" credential: `Authorization: Bearer <token>`,
   attach it to the Whisper and Qwen2.5-Coder HTTP Request nodes.

**Reality check on free HF inference**: the free Inference API has rate
limits and the larger models (like the 32B coder model) may show as
"loading" on first call (cold start, ~20-60s) or occasionally be
unavailable on the free shared infra. If Qwen2.5-Coder-32B is flaky, swap
the URL in the "HF Code Generation" node for a smaller model like
`Qwen/Qwen2.5-Coder-7B-Instruct` — noticeably faster, slightly less capable.

## 4. Build the Lovable web app
1. Open Lovable.dev, start a new project.
2. Paste the prompt from `docs/lovable-prompt.md`.
3. After generation, set the webhook URL to
   `https://your-app-name.onrender.com/webhook/eric-inbound`
4. Set `LOVABLE_SHARED_SECRET` to match your `.env` value.

## 5. Wire Zapier for storage
1. Create a free Zapier account.
2. New Zap -> Trigger: "Catch Hook" (Webhooks by Zapier).
3. Copy the webhook URL Zapier gives you into n8n's
   "Trigger Zapier — Store Files" node (replace the placeholder URL).
4. Add a Zapier action step: Google Drive "Create File" (or Airtable
   "Create Record", or S3 "Upload File") — map the `generatedCode` and
   `projectId` fields from the webhook payload.
5. Zapier's free tier gives 100 tasks/month — fine for occasional project
   generation, tight if you generate many projects per day.

## 6. Connect GitHub + Vercel (deploy path)
1. GitHub: Settings -> Developer settings -> Personal access tokens ->
   generate one with `repo` scope. Put in `.env`.
2. In n8n, Header Auth credential: `Authorization: token <GITHUB_TOKEN>`.
3. Vercel: Account Settings -> Tokens -> create one. Put in `.env`.
4. Attach credentials to the "GitHub — Push Code" and "Vercel — Deploy" nodes.
5. Both have generous free tiers for personal projects.

## 7. LinkedIn — the one real caveat
LinkedIn's official API for posting (`w_member_social` scope) requires
your app to go through LinkedIn's **Developer review/approval process** —
this isn't optional and isn't instant. It is free, but it's a manual
application, not a self-serve token. Until approved, you can only read
your own basic profile data, not post on your behalf via API.
**Realistic workaround**: use Zapier's native LinkedIn integration instead
of raw API calls — Zapier already has approved LinkedIn access, so you
authenticate through Zapier's OAuth instead of building your own app
review submission. I've left the raw API node in the workflow for when/if
you get approved; swap it for a Zapier LinkedIn action in the meantime.

## 8. Device control
- **Windows**: copy `device-control/windows-agent/eric_windows_agent.py`
  to your laptop, `pip install requests`, set the two env vars at the top,
  run it (add to Startup folder for it to persist across reboots).
- **iPhone**: follow `device-control/ios-shortcuts/SETUP.md` exactly —
  Pushcut + a Shortcut you build once.

## 9. Test the loop end to end
1. Send Eric a Telegram message: "Eric, build a simple todo list app."
2. Confirm: Telegram logs the received command, n8n calls Qwen2.5-Coder,
   Zapier saves the output, and you get a Telegram log confirming storage.
3. Say: "Eric, deploy that to Vercel." Confirm GitHub push + Vercel deploy
   logs appear.
4. Say: "No, that's wrong, the button should be on the left." Confirm a
   correction gets written to Chroma — check by asking a similar question
   again and confirming the memory note appears in n8n's execution log.
5. Try: "Eric, lock my laptop" and "Eric, turn on the lights" to confirm
   device routing fires (laptop needs the agent running; iPhone needs
   Pushcut/Shortcuts set up).

## What "fully autonomous" honestly means here
Eric will reliably do exactly what's wired above. It will not invent new
integrations on its own, discover new devices automatically, or take
actions you haven't defined a route for — every capability above is a
specific webhook you built. That's the trade-off for "free and modular":
nothing here is a black box, but nothing happens that you didn't wire.

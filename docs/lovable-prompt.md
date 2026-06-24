# Prompt to paste into Lovable.dev

Copy everything between the lines below into a new Lovable project.

---

Build a voice command web app called "Eric" with this spec:

VISUAL DESIGN
- Dark, minimal, single-screen interface. Centered layout.
- Large circular microphone button in the center (idle state: subtle pulse animation).
- When listening: button glows and animates with an audio waveform.
- Below the button: a live transcript text area showing what's being heard.
- Below that: a scrolling activity feed showing the last 10 commands sent and their status (pending / sent / error), each with a timestamp.
- Top right: small status pill showing "Connected" or "Disconnected" based on whether the backend webhook is reachable.
- Use a single accent color (electric blue or teal) against near-black background.

FUNCTIONALITY
1. Use the Web Speech API (webkitSpeechRecognition / SpeechRecognition) for voice-to-text, continuous listening mode toggled by clicking the mic button.
2. When the mic button is clicked, start listening. Click again to stop and submit.
3. On submit, POST the transcribed text to this webhook URL (store as an environment variable, not hardcoded):
   `https://YOUR_N8N_HOST/webhook/eric-inbound`
   Send this JSON body:
   ```json
   {
     "source": "lovable",
     "user_id": "primary_user",
     "text": "<the transcribed text>",
     "audio_url": null,
     "secret": "<LOVABLE_SHARED_SECRET env var>"
   }
   ```
4. Show the request in the activity feed immediately as "pending", then update to "sent" on a 200 response or "error" on failure.
5. Add a text input fallback below the mic button for typing commands when voice isn't available or the user prefers typing.
6. Add a settings icon (top left) that opens a small panel to edit the webhook URL and shared secret, stored in local component state (not localStorage — keep it in memory only for the session, and explain in a tooltip that it resets on refresh).
7. Include a "Eric is listening..." vs "Tap to talk to Eric" label that toggles with mic state.
8. Make it fully responsive for mobile, since I may use this on my phone.

TECHNICAL NOTES
- Use plain fetch() for the webhook POST, no auth headers needed beyond the secret in the body.
- Handle the case where Web Speech API isn't supported (Firefox) by gracefully falling back to text-only input with a small notice.
- No backend database needed in this app — it's a thin client. All logic and memory lives in the external n8n backend.

---

After Lovable generates the project, replace `YOUR_N8N_HOST` with your actual n8n webhook URL and set the `LOVABLE_SHARED_SECRET` env var in Lovable's project settings to match the value in your backend `.env` file.

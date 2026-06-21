# Autonomous Problem Solver Marketing Engine

Publishes one high-quality LinkedIn post every day at 8:00 AM UTC — entirely on GitHub Actions free tier.

Positions you as an **Operations Consultant / Revenue Recovery Expert / Business Systems Architect** to an audience of Founders, COOs, CEOs, and Revenue Leaders.

---

## How It Works

1. GitHub Actions wakes up at 8:00 AM UTC daily
2. A random content category is selected (Revenue Leakage, Cost Optimization, etc.)
3. GPT-4o generates a structured LinkedIn post + Twitter/X condensed version
4. The post is published to LinkedIn (public, text-only)
5. A full preview is delivered to Telegram as a backup/review channel

---

## Setup (5 minutes)

### 1 — Fork or clone this repo into your GitHub account

### 2 — Add GitHub Actions Secrets

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Where to get it |
|---|---|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn Developer App → OAuth 2.0 token with `w_member_social` scope |
| `LINKEDIN_MEMBER_ID` | Your LinkedIn profile numeric ID (from the API or profile URL) |
| `TELEGRAM_BOT_TOKEN` | Create a bot via [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | Your chat ID — send a message to your bot then call `getUpdates` |

### 3 — Enable GitHub Actions

Go to **Actions** tab → enable workflows if prompted.

### 4 — Test manually

Go to **Actions → Daily LinkedIn Post → Run workflow** to trigger a test run immediately.

---

## Content Categories

Each run randomly picks one of:

- Revenue Leakage
- Cost Optimization
- Process Bottlenecks
- Workflow Automation
- Operational Efficiency
- Supply Chain Optimization
- Scaling Operations
- Customer Operations
- Business Systems Design
- Productivity Improvement

---

## LinkedIn Post Structure

```
HOOK       — Powerful opening about a business problem or financial loss
BLEED      — 2-4 short paragraphs: root cause, money lost, why leaders miss it
SOLUTION   — ✓ Three specific action bullets
INSIGHT    — One authoritative closing statement
CTA        — Comment AUDIT if you want the framework.
HASHTAGS   — 3-5 relevant hashtags
```

---

## Getting Your LinkedIn Member ID

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  "https://api.linkedin.com/v2/me"
```

The `id` field in the response is your `LINKEDIN_MEMBER_ID`.

---

## Getting Your LinkedIn Access Token

1. Go to https://www.linkedin.com/developers/apps and create an app
2. Add the `w_member_social` and `r_liteprofile` OAuth scopes
3. Use the OAuth 2.0 flow or LinkedIn Token Generator to get a token
4. Token expires in 60 days — refresh before expiry

---

## Getting Your Telegram Chat ID

1. Start your bot by sending it `/start` in Telegram
2. Call: `https://api.telegram.org/botYOUR_TOKEN/getUpdates`
3. Copy the `chat.id` value from the response

---

## Logs

All runs output structured logs:

```
[INFO]    — informational steps
[SUCCESS] — successful operations
[ERROR]   — failures (non-fatal, workflow continues)
```

View logs under **Actions → Daily LinkedIn Post → latest run**.

---

## Cost

| Service | Cost |
|---|---|
| GitHub Actions | Free (2,000 min/month free tier) |
| OpenAI GPT-4o | ~$0.01–0.03 per run |
| LinkedIn API | Free |
| Telegram Bot API | Free |

Monthly cost: **< $1**

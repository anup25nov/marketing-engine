import os
import json
import random
import datetime
import requests
from openai import OpenAI

# ── Configuration ────────────────────────────────────────────────────────────

OPENAI_API_KEY        = os.environ.get("OPENAI_API_KEY", "")
LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_MEMBER_ID    = os.environ.get("LINKEDIN_MEMBER_ID", "")
TELEGRAM_BOT_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID      = os.environ.get("TELEGRAM_CHAT_ID", "")

CONTENT_CATEGORIES = [
    "Revenue Leakage",
    "Cost Optimization",
    "Process Bottlenecks",
    "Workflow Automation",
    "Operational Efficiency",
    "Supply Chain Optimization",
    "Scaling Operations",
    "Customer Operations",
    "Business Systems Design",
    "Productivity Improvement",
]

SYSTEM_PROMPT = """You are a senior operations consultant with 20+ years of experience helping 
mid-market and enterprise companies fix revenue leakage, operational inefficiencies, and scaling 
failures. Your writing is direct, data-driven, and authoritative. You never use motivational 
language, startup clichés, AI hype, or generic self-improvement advice.

Your audience: Founders, COOs, CEOs, Operations Managers, Revenue Leaders, Supply Chain Leaders.

Rules:
- Focus only on measurable business problems: money lost, revenue leakage, bottlenecks, hidden 
  costs, scaling failures, process breakdowns, systems thinking.
- Never discuss software engineering, programming, coding, or AI tools.
- Never fabricate statistics or invent research studies.
- Short paragraphs. Maximum two lines each. High readability.

Return ONLY valid JSON. No markdown, no explanations, no extra text."""

def build_user_prompt(category: str) -> str:
    return f"""Generate a LinkedIn post about: {category}

Return this exact JSON schema:
{{
  "topic": "string — concise topic title",
  "linkedin_post": "string — full post using this structure:

HOOK: One powerful opening statement about a business problem or financial loss.

[blank line]

BLEED: 2-4 short paragraphs explaining what causes the problem, where money is lost, and why leaders miss it.

[blank line]

SOLUTION:
✓ First specific action
✓ Second specific action
✓ Third specific action

[blank line]

INSIGHT: One authoritative closing statement.

[blank line]

CTA: Comment AUDIT if you want the framework.

[blank line]

HASHTAGS: 3-5 relevant hashtags (e.g. #Operations #RevenueOperations #ProcessImprovement — never #Motivation #Success #Mindset)",

  "twitter_post": "string — max 280 chars, plain text, no line breaks, no emojis, strong business hook, end with 1-2 hashtags",
  "hashtags": ["string"],
  "cta": "string",
  "source_links": ["string — only real URLs if referencing known industry research, otherwise empty array"]
}}"""

# ── Logging ──────────────────────────────────────────────────────────────────

def log(level: str, message: str):
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level}] {ts} — {message}", flush=True)

# ── Content Generation ────────────────────────────────────────────────────────

def generate_content(category: str, client: OpenAI, retry: bool = False) -> dict:
    log("INFO", f"Generating content for category: {category}")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_user_prompt(category)},
            ],
            temperature=0.85,
            max_tokens=1200,
        )
        raw = response.choices[0].message.content.strip()

        # Strip accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)
        log("SUCCESS", "Content generated successfully")
        return data

    except json.JSONDecodeError as e:
        if not retry:
            log("INFO", f"JSON parse error, retrying once: {e}")
            return generate_content(category, client, retry=True)
        log("ERROR", f"JSON parse failed on retry: {e}")
        return fallback_content(category)

    except Exception as e:
        log("ERROR", f"OpenAI call failed: {e}")
        return fallback_content(category)


def fallback_content(category: str) -> dict:
    log("INFO", "Using fallback content")
    post = (
        "Most companies bleed 5–10% of annual revenue through operational gaps they never measure.\n\n"
        "The problem isn't effort. It's the absence of systems designed to capture and retain value.\n\n"
        "Revenue doesn't disappear overnight. It erodes through small, compounding process failures "
        "that leadership only notices when the P&L reflects the damage.\n\n"
        "✓ Map every revenue touchpoint against a standard operating procedure\n"
        "✓ Measure cycle time and error rate at each handoff\n"
        "✓ Eliminate manual steps that introduce inconsistency\n\n"
        "Operational excellence is not a cost centre. It is a profit lever.\n\n"
        "Comment AUDIT if you want the framework.\n\n"
        f"#Operations #RevenueOperations #ProcessImprovement #OperationalExcellence"
    )
    twitter = (
        "Companies lose 5-10% of revenue through operational gaps they never measure. "
        "Fix the system before the P&L reflects the damage. #Operations #RevenueOperations"
    )
    return {
        "topic": f"{category} — Revenue Impact",
        "linkedin_post": post,
        "twitter_post": twitter[:280],
        "hashtags": ["#Operations", "#RevenueOperations", "#ProcessImprovement", "#OperationalExcellence"],
        "cta": "Comment AUDIT if you want the framework.",
        "source_links": [],
    }

# ── LinkedIn Publishing ───────────────────────────────────────────────────────

def publish_to_linkedin(post_text: str) -> bool:
    if not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_MEMBER_ID:
        log("ERROR", "LinkedIn credentials missing — skipping LinkedIn publish")
        return False

    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "author": f"urn:li:person:{LINKEDIN_MEMBER_ID}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": post_text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code in (200, 201):
            log("SUCCESS", f"LinkedIn post published — status {resp.status_code}")
            return True
        else:
            log("ERROR", f"LinkedIn publish failed — status {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        log("ERROR", f"LinkedIn request exception: {e}")
        return False

# ── Telegram Delivery ─────────────────────────────────────────────────────────

def send_telegram(content: dict, linkedin_ok: bool) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log("ERROR", "Telegram credentials missing — skipping Telegram delivery")
        return False

    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    li_status = "✅ Published" if linkedin_ok else "❌ Failed / Skipped"

    message = (
        f"🗓 *Daily Marketing Post — {ts}*\n\n"
        f"*Topic:* {content.get('topic', 'N/A')}\n"
        f"*LinkedIn:* {li_status}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*LinkedIn Post:*\n\n"
        f"{content.get('linkedin_post', '')}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*Twitter/X Post:*\n\n"
        f"{content.get('twitter_post', '')}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*Source Links:* {', '.join(content.get('source_links', [])) or 'None'}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            log("SUCCESS", "Telegram message delivered")
            return True
        else:
            log("ERROR", f"Telegram delivery failed — status {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        log("ERROR", f"Telegram request exception: {e}")
        return False

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("INFO", "=== Autonomous Problem Solver Marketing Engine — START ===")

    if not OPENAI_API_KEY:
        log("ERROR", "OPENAI_API_KEY is not set — cannot continue")
        raise SystemExit(1)

    client = OpenAI(api_key=OPENAI_API_KEY)

    category = random.choice(CONTENT_CATEGORIES)
    log("INFO", f"Selected category: {category}")

    content = generate_content(category, client)

    log("INFO", f"Topic: {content.get('topic')}")
    log("INFO", "LinkedIn post preview:")
    print(content.get("linkedin_post", "")[:300] + "...", flush=True)

    linkedin_ok = publish_to_linkedin(content.get("linkedin_post", ""))

    telegram_ok = send_telegram(content, linkedin_ok)

    log("INFO", "=== Summary ===")
    log("INFO", f"Content generation : SUCCESS")
    log("INFO" if linkedin_ok  else "ERROR", f"LinkedIn publish    : {'SUCCESS' if linkedin_ok else 'FAILED'}")
    log("INFO" if telegram_ok  else "ERROR", f"Telegram delivery  : {'SUCCESS' if telegram_ok else 'FAILED'}")
    log("INFO", "=== Autonomous Problem Solver Marketing Engine — END ===")


if __name__ == "__main__":
    main()

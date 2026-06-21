import os
import json
import random
import datetime
import requests
from openai import OpenAI

# ── Configuration ─────────────────────────────────────────────────────────────

OPENAI_API_KEY        = os.environ.get("OPENAI_API_KEY", "")
LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_MEMBER_ID    = os.environ.get("LINKEDIN_MEMBER_ID", "")
TELEGRAM_BOT_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID      = os.environ.get("TELEGRAM_CHAT_ID", "")

# Set to True to skip LinkedIn/Telegram and only test content generation
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() in ("1", "true", "yes")

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


# ── Logging ───────────────────────────────────────────────────────────────────

def log(level: str, message: str):
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level:<7}] {ts} — {message}", flush=True)

def log_separator(title: str = ""):
    line = "─" * 60
    if title:
        print(f"\n{'─'*20} {title} {'─'*20}\n", flush=True)
    else:
        print(f"\n{line}\n", flush=True)

def log_block(label: str, content: str):
    log_separator(label)
    print(content, flush=True)
    log_separator()


# ── Content Generation ────────────────────────────────────────────────────────

def generate_content(category: str, client: OpenAI, retry: bool = False) -> dict:
    attempt = "retry" if retry else "attempt 1"
    log("INFO", f"Calling OpenAI GPT-4o [{attempt}] — category: '{category}'")
    log("INFO", f"Model     : gpt-4o")
    log("INFO", f"Temp      : 0.85  |  Max tokens: 1200")
    log("INFO", f"System prompt length : {len(SYSTEM_PROMPT)} chars")
    log("INFO", f"User prompt length   : {len(build_user_prompt(category))} chars")

    try:
        log("INFO", "Sending request to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_user_prompt(category)},
            ],
            temperature=0.85,
            max_tokens=1200,
        )

        usage = response.usage
        log("SUCCESS", f"OpenAI responded — tokens used: {usage.prompt_tokens} prompt + {usage.completion_tokens} completion = {usage.total_tokens} total")

        raw = response.choices[0].message.content.strip()
        log("INFO", f"Raw response length: {len(raw)} chars")
        log("INFO", f"Finish reason: {response.choices[0].finish_reason}")

        # Strip accidental markdown fences
        if raw.startswith("```"):
            log("INFO", "Stripping markdown code fences from response")
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        log("INFO", "Parsing JSON response...")
        data = json.loads(raw)
        log("SUCCESS", "JSON parsed successfully")

        # Validate expected keys
        expected_keys = ["topic", "linkedin_post", "twitter_post", "hashtags", "cta", "source_links"]
        missing = [k for k in expected_keys if k not in data]
        if missing:
            log("WARNING", f"Missing keys in response: {missing}")
        else:
            log("SUCCESS", f"All expected keys present: {expected_keys}")

        return data

    except json.JSONDecodeError as e:
        log("ERROR", f"JSON parse failed: {e}")
        log("ERROR", f"Raw content that failed: {raw[:500]}")
        if not retry:
            log("INFO", "Retrying once with fresh request...")
            return generate_content(category, client, retry=True)
        log("ERROR", "Retry also failed — using fallback content")
        return fallback_content(category)

    except Exception as e:
        log("ERROR", f"OpenAI API call failed: {type(e).__name__}: {e}")
        return fallback_content(category)


def fallback_content(category: str) -> dict:
    log("INFO", "Generating fallback content (no API call)")
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
        "#Operations #RevenueOperations #ProcessImprovement #OperationalExcellence"
    )
    twitter = (
        "Companies lose 5-10% of revenue through operational gaps they never measure. "
        "Fix the system before the P&L reflects the damage. #Operations #RevenueOperations"
    )
    return {
        "topic": f"{category} — Revenue Impact (fallback)",
        "linkedin_post": post,
        "twitter_post": twitter[:280],
        "hashtags": ["#Operations", "#RevenueOperations", "#ProcessImprovement", "#OperationalExcellence"],
        "cta": "Comment AUDIT if you want the framework.",
        "source_links": [],
    }


# ── LinkedIn Publishing ───────────────────────────────────────────────────────

def publish_to_linkedin(post_text: str) -> bool:
    log_separator("LINKEDIN PUBLISH")

    if DRY_RUN:
        log("INFO", "DRY_RUN=true — skipping LinkedIn publish")
        return False

    if not LINKEDIN_ACCESS_TOKEN:
        log("ERROR", "LINKEDIN_ACCESS_TOKEN is not set — skipping")
        return False
    if not LINKEDIN_MEMBER_ID:
        log("ERROR", "LINKEDIN_MEMBER_ID is not set — skipping")
        return False

    log("INFO", f"LinkedIn Member ID  : {LINKEDIN_MEMBER_ID}")
    log("INFO", f"Post length         : {len(post_text)} chars")
    log("INFO", "Sending POST to https://api.linkedin.com/v2/ugcPosts ...")

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
        log("INFO", f"LinkedIn API response status : {resp.status_code}")
        if resp.status_code in (200, 201):
            post_id = resp.headers.get("x-restli-id", "unknown")
            log("SUCCESS", f"LinkedIn post published — post ID: {post_id}")
            return True
        else:
            log("ERROR", f"LinkedIn publish failed — {resp.status_code}: {resp.text[:300]}")
            return False
    except Exception as e:
        log("ERROR", f"LinkedIn request exception: {type(e).__name__}: {e}")
        return False


# ── Telegram Delivery ─────────────────────────────────────────────────────────

def send_telegram(content: dict, linkedin_ok: bool) -> bool:
    log_separator("TELEGRAM DELIVERY")

    if DRY_RUN:
        log("INFO", "DRY_RUN=true — skipping Telegram delivery")
        return False

    if not TELEGRAM_BOT_TOKEN:
        log("ERROR", "TELEGRAM_BOT_TOKEN is not set — skipping")
        return False
    if not TELEGRAM_CHAT_ID:
        log("ERROR", "TELEGRAM_CHAT_ID is not set — skipping")
        return False

    log("INFO", f"Telegram Chat ID : {TELEGRAM_CHAT_ID}")

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

    log("INFO", f"Telegram message length : {len(message)} chars")
    log("INFO", "Sending message to Telegram Bot API...")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}

    try:
        resp = requests.post(url, json=payload, timeout=30)
        log("INFO", f"Telegram API response status : {resp.status_code}")
        if resp.status_code == 200:
            msg_id = resp.json().get("result", {}).get("message_id", "unknown")
            log("SUCCESS", f"Telegram message delivered — message_id: {msg_id}")
            return True
        else:
            log("ERROR", f"Telegram delivery failed — {resp.status_code}: {resp.text[:300]}")
            return False
    except Exception as e:
        log("ERROR", f"Telegram request exception: {type(e).__name__}: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    start_time = datetime.datetime.utcnow()

    log_separator("AUTONOMOUS PROBLEM SOLVER MARKETING ENGINE — START")
    log("INFO", f"Run timestamp : {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log("INFO", f"DRY_RUN mode  : {DRY_RUN}")
    log("INFO", f"OPENAI_API_KEY      : {'SET ✓' if OPENAI_API_KEY else 'MISSING ✗'}")
    log("INFO", f"LINKEDIN_ACCESS_TOKEN: {'SET ✓' if LINKEDIN_ACCESS_TOKEN else 'not set (skipped)'}")
    log("INFO", f"LINKEDIN_MEMBER_ID  : {'SET ✓' if LINKEDIN_MEMBER_ID else 'not set (skipped)'}")
    log("INFO", f"TELEGRAM_BOT_TOKEN  : {'SET ✓' if TELEGRAM_BOT_TOKEN else 'not set (skipped)'}")
    log("INFO", f"TELEGRAM_CHAT_ID    : {'SET ✓' if TELEGRAM_CHAT_ID else 'not set (skipped)'}")

    if not OPENAI_API_KEY:
        log("ERROR", "OPENAI_API_KEY is not set — cannot continue")
        raise SystemExit(1)

    # ── Step 1: Select category
    log_separator("STEP 1 — CATEGORY SELECTION")
    category = random.choice(CONTENT_CATEGORIES)
    log("INFO", f"Available categories : {len(CONTENT_CATEGORIES)}")
    log("INFO", f"Selected category    : '{category}'")

    # ── Step 2: Initialize OpenAI client
    log_separator("STEP 2 — OPENAI CLIENT INIT")
    log("INFO", "Initializing OpenAI client...")
    client = OpenAI(api_key=OPENAI_API_KEY)
    log("SUCCESS", "OpenAI client initialized")

    # ── Step 3: Generate content
    log_separator("STEP 3 — CONTENT GENERATION")
    content = generate_content(category, client)

    # ── Step 4: Display full generated content
    log_separator("STEP 4 — GENERATED CONTENT PREVIEW")

    log("INFO", f"Topic       : {content.get('topic')}")
    log("INFO", f"Hashtags    : {' '.join(content.get('hashtags', []))}")
    log("INFO", f"CTA         : {content.get('cta')}")
    log("INFO", f"Source links: {content.get('source_links', []) or 'None'}")

    log_block("LINKEDIN POST", content.get("linkedin_post", ""))
    log_block("TWITTER/X POST", content.get("twitter_post", ""))

    twitter_len = len(content.get("twitter_post", ""))
    log("INFO", f"Twitter post length : {twitter_len}/280 chars {'✓' if twitter_len <= 280 else '✗ EXCEEDS LIMIT'}")

    # ── Step 5: LinkedIn
    log_separator("STEP 5 — LINKEDIN")
    linkedin_ok = publish_to_linkedin(content.get("linkedin_post", ""))

    # ── Step 6: Telegram
    log_separator("STEP 6 — TELEGRAM")
    telegram_ok = send_telegram(content, linkedin_ok)

    # ── Final summary
    elapsed = (datetime.datetime.utcnow() - start_time).total_seconds()
    log_separator("FINAL SUMMARY")
    log("INFO",    f"Run duration        : {elapsed:.2f}s")
    log("SUCCESS", f"Content generation  : SUCCESS")
    log("INFO" if linkedin_ok  else "INFO",  f"LinkedIn publish    : {'SUCCESS' if linkedin_ok else 'SKIPPED (DRY_RUN)' if DRY_RUN else 'FAILED'}")
    log("INFO" if telegram_ok  else "INFO",  f"Telegram delivery   : {'SUCCESS' if telegram_ok else 'SKIPPED (DRY_RUN)' if DRY_RUN else 'FAILED'}")
    log_separator("ENGINE — END")


if __name__ == "__main__":
    main()

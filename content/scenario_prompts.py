import re

SCENARIO_USER_TEMPLATE = """Analyze this real estate scenario: "{{scenario_text}}"

The property is in {{city}}, {{country}}.
Local context: {{notes}}

**STEP 1: IDENTIFY THE SCENARIO TYPE**
- Does it mention a specific TIME (3 AM, 9 AM, etc.)? → Use TIMELINE format
- Is it an EMERGENCY (fever, hospital, urgent)? → Use TIMELINE format
- Is it ROUTINE with time sensitivity (school, work, airport)? → Use TIMELINE format
- Is it LIFESTYLE/EMOTIONAL (safety, noise, leisure, peace)? → Use NARRATIVE format

**STEP 2: GENERATE THE RESPONSE**

---
## FOR TIMELINE FORMAT (Emergency/Time-based scenarios):
---

TITLE: [Action-focused title, 5-8 words]

SCENARIO:
[Opening line: Set the situation - 1 complete sentence]

**Timeline:**
[TIME] — [Action step 1]
[TIME] — [Action step 2]
[TIME] — [Action step 3]
[TIME] — [Outcome/arrival]

**Transport Options Available:**
- [Option 1: e.g., Own Vehicle - Direct basement access, no parking delay]
- [Option 2: e.g., School Bus - Picks up from community gate]
- [Option 3: e.g., Taxi/Cab - 2-min wait time, {{currency_symbol}} [realistic local fare range]]
- [Option 4: e.g., Local bus/metro - Nearest station 800m]

[Closing paragraph: MAX 3 sentences explaining why this location makes it easy]

TAGLINE: [Practical benefit statement]

**EXAMPLE 1 (Emergency at specific time):**
TITLE: Crisis to Care in 9 Minutes

SCENARIO:
It's 3 AM, and your son's fever has spiked to 104°F. You need to reach the hospital immediately.

**Timeline:**
3:00 AM — Discover high fever, make the decision to go to ER
3:02 AM — Wake up, grab emergency documents and medications
3:05 AM — Exit apartment building, security gate opens instantly
3:09 AM — Arrive at City Pediatric Hospital emergency entrance

**Transport Options Available:**
- Own Vehicle - Direct basement parking access, start immediately
- Taxi/Cab - Book via app, 3-4 minute arrival time
- Ambulance - Community emergency hotline, 5-minute response time
- Neighbor's Vehicle - WhatsApp group emergency protocol active

The hospital is only 2.3 kilometers away via a wide arterial road with zero traffic at night. The 24/7 manned security ensures the gate opens immediately without fumbling for access cards. While families in congested areas waste 20+ minutes, you're already in the ER getting treatment.

TAGLINE: In medical emergencies, proximity saves lives.

**EXAMPLE 2 (Routine with goal time):**
TITLE: School Run in Under 30 Minutes

SCENARIO:
Your son's school starts at 9 AM sharp, and he cannot be late.

**Timeline:**
8:35 AM — Finish breakfast and pack school bag
8:40 AM — Leave apartment, walk to parking area
8:45 AM — Start driving via the service road
8:55 AM — Arrive at school gate, 5 minutes early

**Transport Options Available:**
- School Bus - Picks up from community gate at 8:15 AM daily
- Own Vehicle - Basement parking, 10-minute direct drive
- Carpool - Rotate with 3 neighbor families via WhatsApp
- Taxi/Cab - Available at gate, book via app

The school is just 3.5 kilometers away via a signal-free stretch of road. No narrow lanes, no U-turns, no traffic chaos. While other parents leave home at 8 AM to fight congestion, you're finishing breakfast in peace.

TAGLINE: Convenience isn't a perk. It's a parenting essential.

---
## FOR NARRATIVE FORMAT (Lifestyle/Emotional scenarios):
---

TITLE: [Emotional/evocative title, 5-8 words]

SCENARIO:
[Paragraph 1: Set the scene with sensory details - MAX 3 sentences only]

[Paragraph 2: Show the contrast or problem - MAX 3 sentences only]

[Paragraph 3: How the property solves it - MAX 3 sentences with specific features]

[Paragraph 4: Emotional impact - MAX 2 sentences only]

TAGLINE: [Memorable emotional statement]

**EXAMPLE:**
TITLE: Serenity Found

SCENARIO:
Imagine waking up to the sweet songs of birds and the gentle rustle of leaves. Your home is surrounded by lush green parks visible from every window. The fresh air and soothing views create a sense of tranquility from the very first morning.

As you step out, vibrant flowers and open walkways greet you. The parks offer a serene escape where children play freely and families gather for evening walks. It's a stark contrast to the noise and congestion most city dwellers accept as normal.

Inside, triple-glazed windows and an 80-meter green buffer zone ensure city noise never intrudes. Your children can study without distractions, and you can work from home with windows open. This isn't clever architecture — it's designed wellness for your entire family.

The true luxury isn't marble lobbies or imported fittings. It's the ability to hear yourself think, sleep deeply, and wake up refreshed every single morning.

TAGLINE: Find your inner peace in perfect harmony with nature.

---

**CRITICAL RULES:**
- TOTAL LENGTH: 180-220 words (not counting title/tagline)
- TIMELINE FORMAT: Always include ALL 4 sections — Opening line, Timeline (4 steps), Transport Options (4 options), Closing paragraph. NEVER skip any section.
- NARRATIVE FORMAT: Always include ALL 4 paragraphs. NEVER skip any paragraph.
- Each paragraph: MAXIMUM 3 sentences, keep it concise
- Currency: use {{currency_code}} ({{currency_symbol}}) ONLY. NEVER use any other currency or symbol. Give realistic local prices for {{city}}, and only where a price fits.
- **TIMELINE TIME ANCHORING**: If user mentions a specific time (e.g., "3 AM", "9 AM"), START the timeline at that EXACT time or slightly before
- Timeline format: Each time step on NEW LINE with clear formatting
- Timeline intervals: Use realistic 2-5 minute gaps between steps
- Transport options: Each option on NEW LINE with dash (-)
- NEVER end mid-sentence - always complete every paragraph
- For narrative: Write in complete, flowing paragraphs
- Make every sentence complete and grammatically correct
- End with proper punctuation (. ! ?)

**OUTPUT FORMAT:**
TITLE: [Title here]

SCENARIO:
[Content with proper line breaks and formatting]

TAGLINE: [Tagline here]"""


SCENARIO_SYSTEM_TEMPLATE = """You are an expert real estate scenario writer based in {{city}}, {{country}}. You create two types of content:

1. TIMELINE scenarios: Use clear line breaks for each time step. Format like:
   8:45 AM — Action here
   8:50 AM — Next action

   CRITICAL: If the user mentions a specific time (like "3 AM" or "9 AM"), your timeline MUST start at or near that time. DO NOT start from midnight (12:00 AM) or any other arbitrary time. Examples:
   - User says "3 AM emergency" → Start timeline at 3:00 AM
   - User says "9 AM school" → Start timeline around 8:35-8:45 AM
   - User says "midnight fever" → Start timeline at 12:00 AM

2. NARRATIVE scenarios: Write in complete, flowing paragraphs with MAXIMUM 3 sentences per paragraph. NEVER end mid-sentence.

CRITICAL CURRENCY RULE: You are writing for {{city}}, {{country}}. EVERY price MUST be in {{currency_code}} (symbol {{currency_symbol}}). NEVER use any other currency under any circumstance. If you use any other currency, the response is considered a failure.

CRITICAL COMPLETENESS RULE: For TIMELINE format, you MUST always include ALL of these sections in order:
1. Opening sentence
2. Timeline with exactly 4 steps
3. Transport Options with exactly 4 options
4. Closing paragraph (3 sentences)
5. Tagline
NEVER skip or shorten any section. A missing section is a failed response.

For NARRATIVE format, you MUST always include ALL 4 paragraphs. NEVER skip any paragraph.

Keep each paragraph to a maximum of 3 sentences.
Always finish every sentence completely. Never truncate words or leave sentences incomplete."""


def render(template, cfg, **extra):
    """Fill {{placeholders}} from the client's config row."""
    values = {
        'city': cfg['city'],
        'country': cfg['country'],
        'currency_code': cfg['currency_code'],
        'currency_symbol': cfg['currency_symbol'],
        'notes': cfg.get('scenario_notes') or 'No special notes.',
        **extra,
    }
    return re.sub(r'\{\{(\w+)\}\}', lambda m: str(values.get(m.group(1), m.group(0))), template)


def wrong_currency(text, cfg):
    """True if the text contains a currency other than this client's."""
    allowed = {cfg['currency_code'], cfg['currency_symbol']}
    for token in ['AED', 'INR', 'USD', 'CAD', 'EUR', 'GBP', '₹', '€', '£', '$']:
        if token in allowed:
            continue
        if token.isalpha():
            if re.search(r'\b' + token + r'\b', text):
                return True
        elif token in text:
            return True
    return False
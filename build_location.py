#!/usr/bin/env python3
"""
build_location.py — Build a QFR location page from Prompt L2 content output.

Usage:
    python3 build_location.py <content-file>

Example:
    python3 build_location.py ~/Desktop/content/durham-nc.txt

What it does:
  1. Parses the content file (Prompt L2 output format)
  2. Looks up phone, GBP embed URL, and LeadSnap API key from the master CSV
  3. Fills all template placeholders
  4. Strips markdown links in service card descriptions (cards wrapped in <a>)
  5. Converts markdown links to HTML in Why Choose Us and FAQ sections
  6. Keeps FAQ schema as plain text (no HTML links — prevents JSON parsing errors)
  7. Fixes image paths for nested directory structure
  8. Saves to locations/<slug>/index.html
"""

import re
import os
import sys
import csv

# ── PATHS ──────────────────────────────────────────────────────────────────────
TEMPLATE = os.path.expanduser(
    '~/Desktop/Queen Site Pages and Templates/location-template/index.html'
)
MASTER_CSV = os.path.expanduser(
    '~/Desktop/Goals & Strategy/qfr-gbp-leadsnap-master.csv'
)
OUTPUT_DIR = os.path.expanduser(
    '~/Desktop/Queen Site Pages and Templates/locations'
)


# ── HELPERS ────────────────────────────────────────────────────────────────────

def md_to_html(text):
    """Convert markdown links to HTML: [text](url) → <a href="url">text</a>"""
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)


def strip_md(text):
    """Strip markdown links to plain text: [text](url) → text"""
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', text)


def strip_html_links(text):
    """Strip HTML links to plain text: <a href="url">text</a> → text"""
    return re.sub(r'<a[^>]*>([^<]+)</a>', r'\1', text)


def digits_only(phone):
    """Extract digits from formatted phone: (216) 243-5157 → 2162435157"""
    return re.sub(r'[^0-9]', '', phone)


# ── CONTENT FILE PARSER ───────────────────────────────────────────────────────

# Every field name that Prompt L2 outputs (in order)
FIELD_NAMES = [
    'LOCATION', 'PAGE_TITLE', 'META_DESCRIPTION', 'CANONICAL_URL',
    'H1_TEXT', 'HERO_SUBTEXT',
    'HERO_BULLET_1', 'HERO_BULLET_2', 'HERO_BULLET_3',
    'SERVICES_H2', 'SERVICES_SUBTEXT',
    'SERVICE_1_DESC', 'SERVICE_2_DESC', 'SERVICE_3_DESC',
    'SERVICE_4_DESC', 'SERVICE_5_DESC', 'SERVICE_6_DESC',
    'HOW_IT_WORKS_H2',
    'STEP_1_TITLE', 'STEP_1_DESC',
    'STEP_2_TITLE', 'STEP_2_DESC',
    'STEP_3_TITLE', 'STEP_3_DESC',
    'STEP_4_TITLE', 'STEP_4_DESC',
    'WHY_CHOOSE_H2', 'WHY_CHOOSE_SUBTEXT',
    'WHY_CHOOSE_HEADING_1', 'WHY_CHOOSE_PARAGRAPH_1',
    'WHY_CHOOSE_HEADING_2', 'WHY_CHOOSE_PARAGRAPH_2',
    'WHY_CHOOSE_HEADING_3', 'WHY_CHOOSE_PARAGRAPH_3',
    'FAQ_H2', 'FAQ_SUBTEXT',
    'FAQ_QUESTION_1', 'FAQ_ANSWER_1',
    'FAQ_QUESTION_2', 'FAQ_ANSWER_2',
    'FAQ_QUESTION_3', 'FAQ_ANSWER_3',
    'FAQ_QUESTION_4', 'FAQ_ANSWER_4',
    'FAQ_QUESTION_5', 'FAQ_ANSWER_5',
    'SCHEMA_LOCAL_BUSINESS',
]


def parse_content(filepath):
    """Parse a Prompt L2 output file into a {field_name: value} dict."""
    with open(filepath, 'r') as f:
        text = f.read()

    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Strip section dividers (--- SEO ---, --- HERO ---, etc.)
    text = re.sub(r'^---.*---\s*$', '', text, flags=re.MULTILINE)

    # Build regex: match any known field name at start of line, followed by colon
    pattern = '|'.join(re.escape(f) for f in FIELD_NAMES)
    parts = re.split(rf'^({pattern}):\s*\n', text, flags=re.MULTILINE)

    # parts = [preamble, field1_name, field1_value, field2_name, field2_value, ...]
    result = {}
    for i in range(1, len(parts) - 1, 2):
        name = parts[i].strip()
        value = parts[i + 1].strip()
        result[name] = value

    return result


# ── CSV LOOKUP ─────────────────────────────────────────────────────────────────

def load_csv():
    """Load master CSV into {location_name: row_dict}."""
    data = {}
    with open(MASTER_CSV, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row['Location'].strip()] = row
    return data


def find_location(csv_data, location_str):
    """Match content file location (e.g. 'Cleveland, OH') to CSV row ('Cleveland OH').

    Tries exact match after removing comma, then falls back to city-name match.
    """
    # Normalize: "Cleveland, OH" → "Cleveland OH"
    normalized = re.sub(r'\s+', ' ', location_str.replace(',', '').strip())

    # Exact match
    if normalized in csv_data:
        return csv_data[normalized]

    # Fuzzy: match on city name
    city = location_str.split(',')[0].strip()
    for key, row in csv_data.items():
        if key.startswith(city + ' '):
            return row

    return None


# ── SLUG EXTRACTION ────────────────────────────────────────────────────────────

def get_slug(canonical_url):
    """Extract the directory slug from a canonical URL.

    Examples:
      .../locations/foundation-repair-cleveland-oh/ → foundation-repair-cleveland-oh
      .../foundation-repair-augusta-ga/             → foundation-repair-augusta-ga
    """
    # Try /locations/slug/ pattern first
    m = re.search(r'/locations/([^/]+)', canonical_url)
    if m:
        return m.group(1)

    # Fallback: last path segment before trailing slash
    m = re.search(r'queenfoundationrepair\.com/([^/]+)', canonical_url)
    if m:
        return m.group(1)

    return 'unknown-location'


# ── MAIN BUILD ─────────────────────────────────────────────────────────────────

def build(content_file):
    """Build a single location page from a content file."""

    # Parse content
    print(f'Reading: {content_file}')
    content = parse_content(content_file)
    location = content.get('LOCATION', 'Unknown')
    print(f'Location: {location}')

    # Look up CSV data
    csv_data = load_csv()
    loc = find_location(csv_data, location)

    if loc:
        phone = loc['Phone'].strip()
        gbp_url = loc['GBP Embed URL'].strip()
        leadsnap = loc['LeadSnap API Key'].strip()
        print(f'  Phone:    {phone}')
        print(f'  GBP:      {"found" if gbp_url else "MISSING"}')
        print(f'  LeadSnap: {"found" if leadsnap else "MISSING"}')
    else:
        print(f'  WARNING: "{location}" not found in master CSV!')
        phone = gbp_url = leadsnap = ''

    # Read template
    with open(TEMPLATE, 'r') as f:
        html = f.read()

    # ── STEP 1: FAQ schema — replace with plain text BEFORE global replacement ──
    #
    # The template FAQPage schema uses the same {{FAQ_QUESTION_N}} and {{FAQ_ANSWER_N}}
    # placeholders as the HTML body. But the schema needs PLAIN TEXT — HTML <a> tags
    # contain double quotes that break JSON parsing.
    #
    # We handle the schema first, then the global replacement only affects the HTML body.

    faq_schema_re = re.compile(
        r'(<script type="application/ld\+json">\s*\{[^}]*"@type"\s*:\s*"FAQPage".*?</script>)',
        re.DOTALL
    )
    match = faq_schema_re.search(html)

    if match:
        block = match.group(0)
        for i in range(1, 6):
            # Questions — escape double quotes for JSON safety
            q = content.get(f'FAQ_QUESTION_{i}', '').replace('\\', '\\\\').replace('"', '\\"')
            block = block.replace(f'{{{{FAQ_QUESTION_{i}}}}}', q)

            # Answers — strip markdown links AND escape for JSON
            a = strip_md(content.get(f'FAQ_ANSWER_{i}', ''))
            a = a.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
            block = block.replace(f'{{{{FAQ_ANSWER_{i}}}}}', a)

        html = html[:match.start()] + block + html[match.end():]

    # ── STEP 2: Build all placeholder replacements ──

    replacements = {
        # SEO
        '{{PAGE_TITLE}}': content.get('PAGE_TITLE', ''),
        '{{META_DESCRIPTION}}': content.get('META_DESCRIPTION', ''),
        '{{CANONICAL_URL}}': content.get('CANONICAL_URL', ''),

        # Hero
        '{{H1_TEXT}}': content.get('H1_TEXT', ''),
        '{{HERO_SUBTEXT}}': content.get('HERO_SUBTEXT', ''),
        '{{HERO_BULLET_1}}': content.get('HERO_BULLET_1', 'Free Estimates'),
        '{{HERO_BULLET_2}}': content.get('HERO_BULLET_2', 'Affordable Pricing'),
        '{{HERO_BULLET_3}}': content.get('HERO_BULLET_3', 'Licensed & Insured'),

        # Phone / GBP / LeadSnap (from CSV)
        '{{PHONE_NUMBER}}': phone,
        '{{PHONE_RAW}}': digits_only(phone),
        '{{LEADSNAP_API_KEY}}': leadsnap,
        '{{GBP_EMBED_URL}}': gbp_url,

        # Services — STRIP markdown links (cards are wrapped in <a>, nested <a> is invalid HTML)
        '{{SERVICES_H2}}': content.get('SERVICES_H2', ''),
        '{{SERVICES_SUBTEXT}}': content.get('SERVICES_SUBTEXT', ''),
        '{{SERVICE_1_DESC}}': strip_md(content.get('SERVICE_1_DESC', '')),
        '{{SERVICE_2_DESC}}': strip_md(content.get('SERVICE_2_DESC', '')),
        '{{SERVICE_3_DESC}}': strip_md(content.get('SERVICE_3_DESC', '')),
        '{{SERVICE_4_DESC}}': strip_md(content.get('SERVICE_4_DESC', '')),
        '{{SERVICE_5_DESC}}': strip_md(content.get('SERVICE_5_DESC', '')),
        '{{SERVICE_6_DESC}}': strip_md(content.get('SERVICE_6_DESC', '')),

        # How It Works
        '{{HOW_IT_WORKS_H2}}': content.get('HOW_IT_WORKS_H2', ''),
        '{{STEP_1_TITLE}}': content.get('STEP_1_TITLE', ''),
        '{{STEP_1_DESC}}': content.get('STEP_1_DESC', ''),
        '{{STEP_2_TITLE}}': content.get('STEP_2_TITLE', ''),
        '{{STEP_2_DESC}}': content.get('STEP_2_DESC', ''),
        '{{STEP_3_TITLE}}': content.get('STEP_3_TITLE', ''),
        '{{STEP_3_DESC}}': content.get('STEP_3_DESC', ''),
        '{{STEP_4_TITLE}}': content.get('STEP_4_TITLE', ''),
        '{{STEP_4_DESC}}': content.get('STEP_4_DESC', ''),

        # Why Choose Us — CONVERT markdown links to HTML <a> tags
        '{{WHY_CHOOSE_H2}}': content.get('WHY_CHOOSE_H2', ''),
        '{{WHY_CHOOSE_SUBTEXT}}': content.get('WHY_CHOOSE_SUBTEXT', ''),
        '{{WHY_CHOOSE_HEADING_1}}': content.get('WHY_CHOOSE_HEADING_1', ''),
        '{{WHY_CHOOSE_PARAGRAPH_1}}': md_to_html(content.get('WHY_CHOOSE_PARAGRAPH_1', '')),
        '{{WHY_CHOOSE_HEADING_2}}': content.get('WHY_CHOOSE_HEADING_2', ''),
        '{{WHY_CHOOSE_PARAGRAPH_2}}': md_to_html(content.get('WHY_CHOOSE_PARAGRAPH_2', '')),
        '{{WHY_CHOOSE_HEADING_3}}': content.get('WHY_CHOOSE_HEADING_3', ''),
        '{{WHY_CHOOSE_PARAGRAPH_3}}': md_to_html(content.get('WHY_CHOOSE_PARAGRAPH_3', '')),

        # FAQ — CONVERT markdown links to HTML (only HTML body; schema already handled above)
        '{{FAQ_H2}}': content.get('FAQ_H2', ''),
        '{{FAQ_SUBTEXT}}': content.get('FAQ_SUBTEXT', ''),
        '{{FAQ_QUESTION_1}}': content.get('FAQ_QUESTION_1', ''),
        '{{FAQ_ANSWER_1}}': md_to_html(content.get('FAQ_ANSWER_1', '')),
        '{{FAQ_QUESTION_2}}': content.get('FAQ_QUESTION_2', ''),
        '{{FAQ_ANSWER_2}}': md_to_html(content.get('FAQ_ANSWER_2', '')),
        '{{FAQ_QUESTION_3}}': content.get('FAQ_QUESTION_3', ''),
        '{{FAQ_ANSWER_3}}': md_to_html(content.get('FAQ_ANSWER_3', '')),
        '{{FAQ_QUESTION_4}}': content.get('FAQ_QUESTION_4', ''),
        '{{FAQ_ANSWER_4}}': md_to_html(content.get('FAQ_ANSWER_4', '')),
        '{{FAQ_QUESTION_5}}': content.get('FAQ_QUESTION_5', ''),
        '{{FAQ_ANSWER_5}}': md_to_html(content.get('FAQ_ANSWER_5', '')),

        # Schema (full <script> block from content file)
        '{{SCHEMA_LOCAL_BUSINESS}}': content.get('SCHEMA_LOCAL_BUSINESS', ''),
    }

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    # ── STEP 3: Fix image paths ──
    # Template uses ../images/ (relative to location-template/)
    # Output is locations/<slug>/index.html — needs ../../images/
    html = html.replace('../images/', '../../images/')

    # ── STEP 4: Final safety — strip any remaining HTML links from FAQ schema ──
    def clean_faq_schema(m):
        return strip_html_links(m.group(0))

    html = faq_schema_re.sub(clean_faq_schema, html)

    # ── STEP 5: Verify no unfilled placeholders ──
    # Ignore {{HERO_BG_IMAGE}} — it's only in the template comment block, not in HTML
    remaining = re.findall(r'\{\{[A-Z_0-9]+\}\}', html)
    ignore = {'{{HERO_BG_IMAGE}}'}
    remaining = [p for p in remaining if p not in ignore]
    if remaining:
        unique = sorted(set(remaining))
        print(f'\n  WARNING: {len(unique)} unfilled placeholder(s):')
        for p in unique:
            print(f'    - {p}')
    else:
        print('  All placeholders filled.')

    # ── STEP 6: Save ──
    slug = get_slug(content.get('CANONICAL_URL', ''))
    out_dir = os.path.join(OUTPUT_DIR, slug)
    out_path = os.path.join(out_dir, 'index.html')
    os.makedirs(out_dir, exist_ok=True)

    with open(out_path, 'w') as f:
        f.write(html)

    print(f'\n  Saved: {out_path}')
    print(f'  Size:  {len(html):,} bytes')
    print(f'  Slug:  {slug}')

    return out_path


# ── ENTRY POINT ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('build_location.py — Build a QFR location page')
        print()
        print('Usage:')
        print('  python3 build_location.py <content-file>')
        print()
        print('The content file should be generated by Prompt L2 (Location Content Writer).')
        print('Phone, GBP embed, and LeadSnap key are pulled from the master CSV automatically.')
        print()
        print('Example:')
        print('  python3 build_location.py ~/Desktop/content/durham-nc.txt')
        sys.exit(1)

    build(sys.argv[1])

with open('backend/ai/services.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    '\u2014': '--',   # em dash
    '\u2013': '-',    # en dash
    '\u2011': '-',    # non-breaking hyphen
    '\u2010': '-',    # hyphen
    '\u2022': '-',    # bullet
    '\u2018': "'",    # left single quote
    '\u2019': "'",    # right single quote
    '\u201c': '"',    # left double quote
    '\u201d': '"',    # right double quote
    '\u2026': '...',  # ellipsis
    '\u00a0': ' ',    # non-breaking space
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open('backend/ai/services.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Replacements done')
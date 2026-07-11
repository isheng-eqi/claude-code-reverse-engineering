"""Claude Code String Extraction - Extract and classify key strings from the binary
Reproducible: python 03_extract_strings.py
"""
import re
import os
import sys

EXE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "claude.exe")
if not os.path.exists(EXE_PATH):
    EXE_PATH = r"C:\Users\HI\Desktop\claude.exe"

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MIN_STR_LEN = 8

def extract_strings(data, min_len=MIN_STR_LEN):
    """Extract printable ASCII strings from binary data."""
    strings = []
    current = []
    for byte in data:
        if 32 <= byte <= 126:
            current.append(chr(byte))
        else:
            if len(current) >= min_len:
                strings.append(''.join(current))
            current = []
    if len(current) >= min_len:
        strings.append(''.join(current))
    return strings

def classify_strings(strings):
    """Classify strings into categories."""
    categories = {
        'system_prompt': [],
        'growthbook': [],
        'auth': [],
        'urls': [],
        'env_vars': [],
        'model_info': [],
        'sandbox': [],
        'endpoints': [],
        'other': [],
    }
    
    for s in strings:
        s_stripped = s.strip()
        if not s_stripped:
            continue
            
        # System Prompt indicators
        if any(kw in s_stripped.lower() for kw in [
            'you are claude', 'system prompt', 'system-reminder',
            'anthropic', 'agent harness', 'tool use', 'tool_use',
            'identity_cli', 'anti_verbosity', 'action_caution',
            'task_continuity', 'fable_identity', 'tool_param_json',
            '__system_prompt', 'heron_brook', 'verify_prompt',
            'sparrow_ledger', 'cedar_lantern', 'silent_harbor',
            'walnut_prism', 'amber_sextant', 'amber_beacon',
        ]):
            if len(s_stripped) > 20:
                categories['system_prompt'].append(s_stripped)
        
        # GrowthBook flags
        elif 'tengu_' in s_stripped.lower():
            categories['growthbook'].append(s_stripped)
        elif 'growthbook' in s_stripped.lower():
            categories['growthbook'].append(s_stripped)
        
        # Auth
        elif any(kw in s_stripped for kw in [
            'CLAUDE_CODE_OAUTH', 'CLAUDE_CODE_API_KEY',
            'CLAUDE_CODE_USE_VERTEX', 'CLAUDE_CODE_USE_BEDROCK',
            'CLAUDE_CODE_USE_FOUNDRY', 'CLAUDE_CODE_USE_MANTLE',
            'CLAUDE_CODE_USE_ANTHROPIC_AWS',
        ]):
            categories['auth'].append(s_stripped)
        
        # URLs
        elif re.match(r'https?://', s_stripped):
            categories['urls'].append(s_stripped)
        
        # Env vars
        elif re.match(r'[A-Z_]{4,40}(?:_[A-Z]+)*$', s_stripped) and '_' in s_stripped:
            categories['env_vars'].append(s_stripped)
        
        # Model info
        elif any(kw in s_stripped.lower() for kw in ['claude', 'haiku', 'sonnet', 'opus', 'fable']):
            if len(s_stripped) > 15:
                categories['model_info'].append(s_stripped)
        
        # Sandbox / security
        elif any(kw in s_stripped.lower() for kw in [
            'sandbox', 'seccomp', 'bubblewrap', 'container',
            'isolation', 'permission', 'security',
        ]):
            if len(s_stripped) > 15:
                categories['sandbox'].append(s_stripped)
        
        # API endpoints
        elif re.search(r'/(?:v\d|api|oauth|graphql|messages|chat)/', s_stripped):
            categories['endpoints'].append(s_stripped)
    
    return categories

def main():
    print("Claude Code String Extraction & Classification")
    print("=" * 60)
    
    file_size = os.path.getsize(EXE_PATH)
    print(f"File: {EXE_PATH}")
    print(f"Size: {file_size:,} bytes")
    
    # Read and extract strings (sample the binary for speed)
    # Focus on .rdata section (contains most readable strings)
    # But also scan the whole file in chunks
    all_strings = []
    
    with open(EXE_PATH, 'rb') as f:
        # Read in 16MB chunks
        chunk_size = 16 * 1024 * 1024
        total_read = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            strings = extract_strings(chunk)
            all_strings.extend(strings)
            total_read += len(chunk)
            if total_read % (64 * 1024 * 1024) == 0:
                print(f"  Scanned: {total_read/1024/1024:.0f} MB / {file_size/1024/1024:.0f} MB")
    
    print(f"\nTotal ASCII strings (>{MIN_STR_LEN} chars): {len(all_strings)}")
    
    # Classify
    categories = classify_strings(all_strings)
    
    # Print results
    for cat_name in ['system_prompt', 'growthbook', 'auth', 'urls', 'model_info', 'sandbox', 'endpoints', 'env_vars']:
        items = categories[cat_name]
        unique = sorted(set(items))
        print(f"\n[{cat_name.upper()}] - {len(unique)} unique strings")
        print("-" * 60)
        
        output_file = os.path.join(OUTPUT_DIR, f"strings_{cat_name}.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Claude Code - {cat_name} Strings\n")
            f.write(f"Total unique: {len(unique)}\n")
            f.write("=" * 60 + "\n\n")
            for s in unique[:200]:
                preview = s[:200] + ('...' if len(s) > 200 else '')
                print(f"  {preview}")
                f.write(f"{s}\n")
            if len(unique) > 200:
                print(f"  ... and {len(unique) - 200} more (see {output_file})")
        
        print(f"  Saved to: {output_file}")
    
    # Special: GrowthBook flags summary
    gb_flags = set()
    for s in categories['growthbook']:
        matches = re.findall(r'tengu_[a-z_]+', s.lower())
        gb_flags.update(matches)
    
    print(f"\n[GROWTHBOOK FLAGS] - {len(gb_flags)} unique tengu_* flags")
    gb_file = os.path.join(OUTPUT_DIR, "growthbook_flags.txt")
    with open(gb_file, 'w', encoding='utf-8') as f:
        for flag in sorted(gb_flags):
            f.write(f"{flag}\n")
    print(f"  Saved to: {gb_file}")
    
    # URLs summary
    urls = set()
    for s in categories['urls']:
        match = re.search(r'(https?://[a-zA-Z0-9._\-/]+)', s)
        if match:
            urls.add(match.group(1))
    
    url_file = os.path.join(OUTPUT_DIR, "urls.txt")
    with open(url_file, 'w', encoding='utf-8') as f:
        for url in sorted(urls):
            f.write(f"{url}\n")
    print(f"\n[URLS & ENDPOINTS] - {len(urls)} unique")
    print(f"  Saved to: {url_file}")
    
    # Print all URLs
    for url in sorted(urls):
        print(f"  {url}")

if __name__ == '__main__':
    main()

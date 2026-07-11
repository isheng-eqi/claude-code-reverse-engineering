"""Claude Code VFS Extraction - Extract the Bun Virtual File System from .bun section
Reproducible: pip install pefile && python 02_extract_vfs.py
"""
import pefile
import os
import re
import sys

EXE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "claude.exe")
if not os.path.exists(EXE_PATH):
    EXE_PATH = r"C:\Users\HI\Desktop\claude.exe"

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def find_bun_section(pe):
    """Find the section most likely to be the Bun VFS container."""
    candidates = []
    for section in pe.sections:
        name = section.Name.decode('utf-8', errors='replace').rstrip('\x00')
        data = section.get_data()
        # Bun VFS contains paths like BUN/root/src/...
        bun_paths = len(re.findall(rb'BUN/root/', data))
        if bun_paths > 10:
            candidates.append((section, bun_paths, len(data)))
    return candidates

def extract_file_paths(data, min_len=5):
    """Extract file paths from binary data."""
    # Match patterns like BUN/root/src/entrypoints/cli.js
    # These appear as null-terminated or length-prefixed strings in the VFS
    paths = set()
    
    # Pattern 1: BUN/root/... paths
    for match in re.finditer(rb'BUN/root/([a-zA-Z0-9_\-./@+()\[\]{}~!$%^&=#,:;\s]{3,200})', data):
        try:
            path = match.group(0).decode('ascii', errors='ignore')
            # Clean up - remove trailing garbage
            path = re.sub(r'[^\x20-\x7E]', '', path)
            if '/' in path and len(path) > 15:
                paths.add(path)
        except:
            pass
    
    # Pattern 2: /src/... paths (internal module paths)
    for match in re.finditer(rb'(?<![a-zA-Z])/(?:src|dist|internal|lib|node_modules)/([a-zA-Z0-9_\-./@+]{5,200})', data):
        try:
            path = match.group(0).decode('ascii', errors='ignore')
            path = re.sub(r'[^\x20-\x7E]', '', path)
            if len(path) > 10:
                paths.add(path)
        except:
            pass
    
    # Pattern 3: .js / .ts / .json / .node filenames
    for match in re.finditer(rb'([a-zA-Z0-9_\-/]{5,100}\.(?:jsx?|tsx?|json|node|mjs|cjs|css|html|md|yaml|yml|toml|wasm)(?:\x00|[^a-zA-Z0-9_\-.]))', data):
        try:
            path = match.group(1).decode('ascii', errors='ignore')
            if '/' in path or '\\' in path:
                path = path.replace('\\', '/')
                paths.add(path)
        except:
            pass
    
    return sorted(paths)

def main():
    pe = pefile.PE(EXE_PATH)
    
    print("Claude Code VFS Extraction")
    print("=" * 60)
    
    # Find Bun VFS sections
    candidates = find_bun_section(pe)
    
    if not candidates:
        # Fallback: search all sections
        print("No obvious .bun section found. Scanning all sections...")
        all_paths = set()
        for section in pe.sections:
            name = section.Name.decode('utf-8', errors='replace').rstrip('\x00')
            data = section.get_data()
            paths = extract_file_paths(data)
            if paths:
                all_paths.update(paths)
                print(f"\nSection '{name}' ({len(data):,} bytes): {len(paths)} file paths found")
        
        paths = sorted(all_paths)
    else:
        all_paths = set()
        for section, bun_count, size in candidates:
            name = section.Name.decode('utf-8', errors='replace').rstrip('\x00')
            print(f"\nBun VFS section: '{name}' ({size:,} bytes, {bun_count} BUN/root/ hits)")
            paths = extract_file_paths(section.get_data())
            all_paths.update(paths)
        paths = sorted(all_paths)
    
    # Categorize
    categories = {}
    for p in paths:
        parts = p.split('/')
        if len(parts) >= 2:
            cat = parts[0] if parts[0] else parts[1] if len(parts) > 1 else 'root'
        else:
            cat = 'root'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p)
    
    print(f"\nTotal unique file paths extracted: {len(paths)}")
    print(f"Categories: {len(categories)}")
    print()
    
    # Print categorized tree
    for cat in sorted(categories.keys()):
        files = categories[cat]
        print(f"[{cat}] ({len(files)} files)")
        for f in files[:30]:
            print(f"  {f}")
        if len(files) > 30:
            print(f"  ... and {len(files) - 30} more files")
        print()
    
    # Save full list
    output_file = os.path.join(OUTPUT_DIR, "vfs_files.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Claude Code VFS File List\n")
        f.write(f"Total: {len(paths)} files\n")
        f.write("=" * 60 + "\n\n")
        for cat in sorted(categories.keys()):
            f.write(f"\n[{cat}] ({len(categories[cat])} files)\n")
            f.write("-" * 40 + "\n")
            for p in categories[cat]:
                f.write(f"  {p}\n")
    
    print(f"Full list saved to: {output_file}")
    pe.close()

if __name__ == '__main__':
    main()

"""
Bun VFS Binary Parser - Structural Analysis
Parses the proprietary Bun VFS serialization format in the .bun PE section.
Not guesswork - based on observed binary patterns.
"""
import struct
import os
import sys

EXE_PATH = r"C:\Users\HI\Desktop\claude.exe"
BUN_OFFSET = 0x04D02400
BUN_SIZE = 145148928

def hexdump(data, offset=0, length=256):
    """Pretty hex dump."""
    lines = []
    for i in range(0, min(length, len(data)), 16):
        chunk = data[i:i+16]
        hex_str = ' '.join(f'{b:02x}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f"  {offset+i:08X}: {hex_str:48s}  {ascii_str}")
    return '\n'.join(lines)

def analyze_bun_structure():
    with open(EXE_PATH, 'rb') as f:
        # Read the full .bun section in chunks for analysis
        f.seek(BUN_OFFSET)
        
        # Header analysis
        header = f.read(256)
        
        print("=" * 70)
        print("  BUN VFS BINARY STRUCTURE ANALYSIS")
        print("=" * 70)
        print(f"  Section offset: 0x{BUN_OFFSET:08X}")
        print(f"  Section size:   {BUN_SIZE:,} bytes ({BUN_SIZE/1024/1024:.1f} MB)")
        
        # First 8 bytes: total embedded size
        total_size = struct.unpack('<Q', header[0:8])[0]
        print(f"\n  Header field 0 (QWORD): {total_size:,} ({total_size/1024/1024:.1f} MB)")
        
        # Scan for all BUN/root paths in first 64KB
        f.seek(BUN_OFFSET)
        scan_region = f.read(65536)
        
        import re
        bun_matches = list(re.finditer(rb'(//[^\x00-\x1f]{10,300}?)(\x00)', scan_region))
        print(f"\n  Found {len(bun_matches)} BUN URL-like paths in first 64KB")
        
        entries = []
        for m in bun_matches:
            raw_path = m.group(1)
            try:
                path = raw_path.decode('ascii', errors='replace')
                # URL decode the path
                from urllib.parse import unquote
                path = unquote(path)
                # The bytes after the path (up to next entry) are metadata
                meta_start = m.end()
                # Look for next path or reasonable boundary
                next_match = None
                for m2 in bun_matches:
                    if m2.start() > m.start():
                        next_match = m2
                        break
                if next_match:
                    meta_end = next_match.start()
                else:
                    meta_end = min(meta_start + 256, len(scan_region))
                
                meta_bytes = scan_region[meta_start:meta_end]
                entries.append({
                    'offset': m.start(),
                    'path': path,
                    'raw_path': raw_path.decode('ascii', errors='replace'),
                    'meta': meta_bytes[:64],
                })
            except:
                pass
        
        print(f"\n  First 30 entries:")
        for i, entry in enumerate(entries[:30]):
            path = entry['path']
            meta_preview = ' '.join(f'{b:02x}' for b in entry['meta'][:32])
            print(f"  [{i:3d}] @+0x{entry['offset']:05X}  {path}")
            print(f"        meta: {meta_preview}")
        
        # Categorize entries
        categories = {}
        for entry in entries:
            path = entry['path']
            parts = path.split('/')
            if 'BUN/root' in path:
                # Extract the relative path after BUN/root/
                idx = path.find('BUN/root/')
                rel = path[idx+9:]  # after 'BUN/root/'
                cat = rel.split('/')[0] if '/' in rel else 'root'
            else:
                cat = 'other'
            
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(entry['path'])
        
        print(f"\n  Entry categories:")
        for cat in sorted(categories.keys()):
            print(f"    [{cat}]: {len(categories[cat])} files")
        
        # Analyze metadata structure
        # The metadata seems to contain: flags, size, and possibly offset information
        print(f"\n  Metadata structure analysis (first 5 entries):")
        for entry in entries[:5]:
            meta = entry['meta']
            path = entry['path'].split('BUN/root/')[-1] if 'BUN/root/' in entry['path'] else entry['path']
            print(f"\n  File: {path}")
            print(f"  Raw meta ({len(meta)} bytes):")
            print(hexdump(meta, 0, 64))
            
            # Try to interpret common fields
            if len(meta) >= 4:
                val32 = struct.unpack('<I', meta[0:4])[0]
                print(f"    [0:4]  uint32 LE: {val32}")
            if len(meta) >= 8:
                val64 = struct.unpack('<Q', meta[0:8])[0]
                print(f"    [0:8]  uint64 LE: {val64}")
            if len(meta) >= 12:
                val32_8 = struct.unpack('<I', meta[8:12])[0]
                print(f"    [8:12] uint32 LE: {val32_8}")

if __name__ == '__main__':
    analyze_bun_structure()

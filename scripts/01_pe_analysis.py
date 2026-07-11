"""Claude Code PE Structure Analysis - Professional PE Parser
Uses pefile to analyze the 215MB claude.exe Bun-compiled binary.
Reproducible: pip install pefile && python 01_pe_analysis.py
"""
import pefile
import math
import hashlib
import os

EXE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "claude.exe")
if not os.path.exists(EXE_PATH):
    EXE_PATH = r"C:\Users\HI\Desktop\claude.exe"

def calc_entropy(data, max_sample=100000):
    if not data:
        return 0.0
    sample = data[:max_sample]
    byte_counts = [0] * 256
    for b in sample:
        byte_counts[b] += 1
    entropy = 0.0
    for count in byte_counts:
        if count > 0:
            p = count / len(sample)
            entropy -= p * math.log2(p)
    return entropy

def main():
    pe = pefile.PE(EXE_PATH)
    
    # Hash
    with open(EXE_PATH, 'rb') as f:
        sha256 = hashlib.sha256()
        while chunk := f.read(4 * 1024 * 1024):
            sha256.update(chunk)
    
    print("=" * 75)
    print("  CLAUDE.EXE - PROFESSIONAL PE STRUCTURE ANALYSIS")
    print("=" * 75)
    print(f"  File:      {EXE_PATH}")
    print(f"  Size:      {os.path.getsize(EXE_PATH):,} bytes")
    print(f"  SHA256:    {sha256.hexdigest()}")
    print()
    
    # File Header
    print("─" * 75)
    print("  COFF FILE HEADER")
    print("─" * 75)
    m = {0x8664: 'AMD64', 0x014C: 'i386', 0xAA64: 'ARM64'}
    print(f"  Machine:              {m.get(pe.FILE_HEADER.Machine, hex(pe.FILE_HEADER.Machine))}")
    print(f"  Number of Sections:   {pe.FILE_HEADER.NumberOfSections}")
    chars = []
    if pe.FILE_HEADER.Characteristics & 0x0002: chars.append('EXECUTABLE')
    if pe.FILE_HEADER.Characteristics & 0x0020: chars.append('LARGE_ADDRESS_AWARE')
    if pe.FILE_HEADER.Characteristics & 0x0100: chars.append('32BIT_MACHINE')
    print(f"  Characteristics:      0x{pe.FILE_HEADER.Characteristics:04X} ({', '.join(chars)})")
    print()
    
    # Optional Header
    oh = pe.OPTIONAL_HEADER
    print("─" * 75)
    print("  OPTIONAL HEADER (PE32+)")
    print("─" * 75)
    print(f"  Entry Point RVA:      0x{oh.AddressOfEntryPoint:08X}")
    print(f"  Image Base:           0x{oh.ImageBase:016X}")
    print(f"  Section Alignment:    0x{oh.SectionAlignment:X} ({oh.SectionAlignment:,})")
    print(f"  File Alignment:       0x{oh.FileAlignment:X} ({oh.FileAlignment:,})")
    print(f"  Size of Image:        {oh.SizeOfImage:,} bytes ({oh.SizeOfImage/1024/1024:.1f} MB)")
    print(f"  Size of Headers:      {oh.SizeOfHeaders:,} bytes")
    print(f"  Subsystem:            {oh.Subsystem} (Console)")
    print(f"  Stack Reserve:        {oh.SizeOfStackReserve/1024/1024:.1f} MB")
    print(f"  Heap Reserve:         {oh.SizeOfHeapReserve/1024/1024:.1f} MB")
    print()
    
    # Data Directories
    print("─" * 75)
    print("  DATA DIRECTORIES (non-empty only)")
    print("─" * 75)
    dir_names = ["EXPORT", "IMPORT", "RESOURCE", "EXCEPTION", "SECURITY",
                 "BASERELOC", "DEBUG", "ARCHITECTURE", "GLOBALPTR", "TLS",
                 "LOAD_CONFIG", "BOUND_IMPORT", "IAT", "DELAY_IMPORT", "CLR_HEADER", "RESERVED"]
    for i, (name, d) in enumerate(zip(dir_names, oh.DATA_DIRECTORY)):
        if d.VirtualAddress != 0 or d.Size != 0:
            print(f"  {name:15s}  RVA=0x{d.VirtualAddress:08X}  Size={d.Size:>10,}")
    print()
    
    # Sections
    print("─" * 75)
    print("  SECTIONS")
    print("─" * 75)
    header = f"  {'Name':<14} {'VirtAddr':>10} {'VirtSize':>14} {'RawPtr':>10} {'RawSize':>14} {'Entropy':>8}  Characteristics"
    print(header)
    print("  " + "-" * (len(header) - 2))
    
    for section in pe.sections:
        name = section.Name.decode('utf-8', errors='replace').rstrip('\x00')
        if not name.strip() or all(c < ' ' for c in name):
            name = f"[{section.Name[:4].hex().upper()}]"
        raw_data = section.get_data()
        ent = calc_entropy(raw_data)
        
        virt_size = section.Misc_VirtualSize
        raw_size = section.SizeOfRawData
        
        vs = f"{virt_size:,}" if virt_size < 10_000_000 else f"{virt_size/1024/1024:.1f} MB"
        rs = f"{raw_size:,}" if raw_size < 10_000_000 else f"{raw_size/1024/1024:.1f} MB"
        
        chars_list = []
        f = section.Characteristics
        if f & 0x20000000: chars_list.append("X")
        if f & 0x40000000: chars_list.append("R")
        if f & 0x80000000: chars_list.append("W")
        if f & 0x00000020: chars_list.append("CODE")
        if f & 0x00000040: chars_list.append("DATA")
        if f & 0x00000080: chars_list.append("BSS")
        char_str = ','.join(chars_list)
        
        print(f"  {name:<14} 0x{section.VirtualAddress:08X} {vs:>14} 0x{section.PointerToRawData:08X} {rs:>14} {ent:>7.3f}  {char_str}")
    
    # High-entropy sections = bytecode / compressed data
    print(f"\n  Note: Entropy > 7.5 indicates compressed/encrypted/bytecode content.")
    print(f"        Low entropy (< 3) indicates text or sparse data.")
    
    pe.close()

if __name__ == '__main__':
    main()

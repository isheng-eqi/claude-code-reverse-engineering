"""
Bun Module Graph Extractor - Extracts source code from Bun-compiled executables.

HOW IT WORKS:
  Bun's `bun build --compile` appends a module graph at the end of the binary:
  1. Search backwards from EOF for "\n---- Bun! ----\n" (16-byte trailer)
  2. Read 32-byte offsets structure just before the trailer
  3. Parse module entries (36 bytes each): name, contents, sourcemap, bytecode
  4. Extract contents and bytecode for each module

Reproducible: python 05_extract_modules.py
"""
import struct
import os
import sys
import re
from urllib.parse import unquote

EXE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "claude.exe")
if not os.path.exists(EXE_PATH):
    EXE_PATH = r"C:\Users\HI\Desktop\claude.exe"

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "decompiled")

TRAILER = b"\n---- Bun! ----\n"
OFFSETS_SIZE = 32
MODULE_ENTRY_SIZE = 36

LOADER_MAP = {0: "jsx", 1: "js", 2: "ts", 3: "tsx", 4: "css", 5: "file",
              6: "json", 7: "toml", 8: "wasm", 9: "napi", 10: "text", 11: "sqlite"}
FORMAT_MAP = {0: "none", 1: "cjs", 2: "esm"}
ENCODING_MAP = {0: "binary", 1: "latin1", 2: "utf8"}

def find_trailer(data):
    """Search backwards for Bun trailer marker."""
    pos = data.rfind(TRAILER)
    return pos if pos >= 0 else None

def extract_modules(filepath, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    file_size = os.path.getsize(filepath)
    
    with open(filepath, 'rb') as f:
        # Search last 4MB for trailer
        search_size = min(4 * 1024 * 1024, file_size)
        f.seek(-search_size, 2)
        tail = f.read(search_size)
        
        trailer_pos_in_tail = find_trailer(tail)
        if trailer_pos_in_tail is None:
            print("ERROR: Bun trailer not found. Is this a bun build --compile binary?")
            return
        
        trailer_pos = file_size - search_size + trailer_pos_in_tail
        print(f"Trailer found at offset: {trailer_pos:,} (0x{trailer_pos:X})")
        
        # Read offsets (32 bytes before trailer)
        f.seek(trailer_pos - OFFSETS_SIZE)
        off_data = f.read(OFFSETS_SIZE)
        
        byte_count = struct.unpack('<I', off_data[0:4])[0]
        modules_off = struct.unpack('<I', off_data[8:12])[0]
        modules_len = struct.unpack('<I', off_data[12:16])[0]
        entry_point_id = struct.unpack('<I', off_data[16:20])[0]
        args_off = struct.unpack('<I', off_data[20:24])[0]
        args_len = struct.unpack('<I', off_data[24:28])[0]
        flags = struct.unpack('<I', off_data[28:32])[0]
        
        data_start = trailer_pos - OFFSETS_SIZE - byte_count
        module_count = modules_len // MODULE_ENTRY_SIZE
        
        print(f"Embedded data: {byte_count:,} bytes ({byte_count/1024/1024:.1f} MB)")
        print(f"Module entries: {module_count} ({modules_len} bytes)")
        print(f"Entry point ID: {entry_point_id}")
        print(f"Flags: 0x{flags:08X}")
        print()
        
        f.seek(data_start + modules_off)
        
        extracted = 0
        for i in range(module_count):
            entry_data = f.read(MODULE_ENTRY_SIZE)
            if len(entry_data) < MODULE_ENTRY_SIZE:
                break
            
            name_off = struct.unpack('<I', entry_data[0:4])[0]
            name_len = struct.unpack('<I', entry_data[4:8])[0]
            contents_off = struct.unpack('<I', entry_data[8:12])[0]
            contents_len = struct.unpack('<I', entry_data[12:16])[0]
            srcmap_off = struct.unpack('<I', entry_data[16:20])[0]
            srcmap_len = struct.unpack('<I', entry_data[20:24])[0]
            bytecode_off = struct.unpack('<I', entry_data[24:28])[0]
            bytecode_len = struct.unpack('<I', entry_data[28:32])[0]
            encoding_byte = entry_data[32]
            loader_byte = entry_data[33]
            format_byte = entry_data[34]
            
            # Validate pointers
            if name_len == 0 or name_len > 10000:
                continue
            if name_off + name_len > byte_count:
                continue
            if contents_len == 0 or contents_len > byte_count:
                continue
            if contents_off + contents_len > byte_count + 1000000:
                continue
            
            # Read name
            name_addr = data_start + name_off
            f.seek(name_addr)
            name = f.read(name_len).decode('utf-8', errors='replace')
            clean_name = name.replace('/$bunfs/root', '').replace('compiled://root', '').lstrip('/')
            
            loader_name = LOADER_MAP.get(loader_byte, str(loader_byte))
            format_name = FORMAT_MAP.get(format_byte, str(format_byte))
            
            # Read contents
            contents_addr = data_start + contents_off
            f.seek(contents_addr)
            contents = f.read(contents_len)
            
            is_entry = "★" if i == entry_point_id else " "
            print(f"[{is_entry}] {clean_name}")
            print(f"    loader={loader_name}, format={format_name}, {contents_len:,} bytes ({contents_len/1024:.1f} KB)")
            
            # Save contents
            safe_name = re.sub(r'[<>:"/\\|?*~]', '_', clean_name)
            out_path = os.path.join(output_dir, safe_name)
            with open(out_path, 'wb') as out:
                out.write(contents)
            print(f"    → {out_path}")
            
            # Save bytecode if present and valid
            if bytecode_len > 0 and bytecode_off + bytecode_len <= byte_count:
                bytecode_addr = data_start + bytecode_off
                f.seek(bytecode_addr)
                bytecode = f.read(bytecode_len)
                bc_path = os.path.join(output_dir, safe_name + '.bytecode')
                with open(bc_path, 'wb') as out:
                    out.write(bytecode)
                print(f"    bytecode: {bc_path} ({bytecode_len:,} bytes)")
            
            extracted += 1
        
        print(f"\nExtracted {extracted} module(s) to {output_dir}")
        
        # Extract additional file:// entries from .bun section
        if byte_count > 50000000:  # Large binaries may have additional VFS entries
            print(f"\nScanning for additional VFS file paths...")
            f.seek(data_start)
            vfs_data = f.read(byte_count)
            
            paths = set()
            for match in re.finditer(rb'file:///([^\x00-\x08\x0b\x0c\x0e-\x1f]{10,200})', vfs_data):
                try:
                    path = unquote(match.group(0).decode('ascii', errors='replace'))
                    paths.add(path)
                except:
                    pass
            
            if paths:
                print(f"  Found {len(paths)} additional file paths:")
                for p in sorted(paths):
                    print(f"    {p}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        exe = sys.argv[1]
    else:
        exe = EXE_PATH
    
    if len(sys.argv) > 2:
        out = sys.argv[2]
    else:
        out = OUTPUT_DIR
    
    if not os.path.exists(exe):
        print(f"ERROR: {exe} not found. Usage: python 05_extract_modules.py <binary> [output_dir]")
        sys.exit(1)
    
    extract_modules(exe, out)

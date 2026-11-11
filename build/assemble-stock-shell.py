"""Build the D-R35 stock-shell prototype from a locally supplied pinned ELF."""
import argparse
import hashlib
from pathlib import Path
import struct
import subprocess
import tempfile


PIN = "8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72"
CORE_PIN = "70d885151b7d3cac05ae69fc9653974c420b49d5cb20f95b09af547f319a8936"
TEXT = 0x1D0000
PATCHES = {
    0xA5014: (0xEBFFFBE7, 0xE3A00001),  # defer open until the ROM has been read
    0xA502C: (0xEAFFFE67, "run_snes"),
    0xA42E8: (0xEBFDB748, "stock_resolve_run"),
    0x98174: (0xEBFFA709, "stock_load_settings"),
    0x81E6C: (0xEBFE3F3B, "stock_language"),
    0x984DC: (0xEBFFD6C0, "stock_settings"),
    0x8E30C: (0xEBFFE015, "stock_settings_input"),
    0x8E2C8: (0xEB0060E2, "stock_settings_frame"),
    0x8E9F8: (0xEB005F16, "stock_settings_frame"),
    0x98360: (0xEBFFBC69, "stock_menu_music"),
    0x87B80: (0xEBFFFE61, "stock_menu_music"),
    0x8920C: (0xEBFE22FE, "stock_state_access"),
    0x91244: (0xEBFE02F0, "stock_state_access"),
    0x91268: (0xEBFE029C, "stock_state_fopen"),
    0x91A24: (0xEBFE00F8, "stock_state_access"),
    0x91A4C: (0xEBFE00A3, "stock_state_fopen"),
    0x91DB4: (0xEBFDFFC9, "stock_state_fopen"),
    0x89228: (0xEB0069C5, "stock_load_state"),
    0x892A4: (0xEB006941, "stock_save_state"),
    0x9152C: (0xEB004904, "stock_load_state"),
    0x91D9C: (0xEB004683, "stock_save_state"),
    0x9AA70: (0xEB00234E, "stock_save_state"),
    0x9B3D8: (0xEB002159, "stock_load_state"),
    0xA47A4: (0xEBFFE087, "stock_save_snap"),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def command(*argv):
    return subprocess.check_output(argv, text=True)


def assemble(vendor, core, out):
    repo = Path(__file__).resolve().parent.parent
    if not any(out.is_relative_to(parent) for parent in
               (repo/"build", Path.home().resolve(), Path(tempfile.gettempdir()).resolve())):
        raise ValueError("output must be in the workspace build directory or Linux scratch space")
    data = bytearray(vendor.read_bytes())
    payload = core.read_bytes()
    if sha(data) != PIN or sha(payload) != CORE_PIN:
        raise ValueError("unexpected stock frontend or optimized core hash")
    out.mkdir()
    code = out / "loader.elf"
    linker = out / "loader.ld"
    linker.write_text("""SECTIONS {
      . = 0x1d0000;
      .payload : { *(.text*) *(.rodata*) }
      .forbidden : { *(.data*) *(.bss*) *(.got*) }
      ASSERT(SIZEOF(.forbidden) == 0, "owned data must use its reserved zero-fill area")
      /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) *(.eh_frame*) }
    }\n""")
    here = Path(__file__).resolve().parent
    prefix = "arm-linux-gnueabihf-"
    command(prefix+"gcc", "-std=gnu11", "-O3", "-Wall", "-Wextra", "-Werror", "-ffreestanding",
            "-fno-builtin", "-fno-pic", "-fno-pie", "-fno-stack-protector",
            "-fno-unwind-tables", "-fno-asynchronous-unwind-tables", "-marm", "-mcpu=cortex-a7",
            "-mfpu=neon-vfpv4", "-mfloat-abi=hard", "-nostdlib", "-static", "-no-pie",
            "-Wl,--build-id=none", "-Wl,-T,"+str(linker),
            "-I"+str(here / "snes9x2005/libretro-common/include"),
            str(here / "stock-shell-loader.c"), "-o", str(code))
    if command(prefix+"nm", "-u", str(code)).strip():
        raise ValueError("owned code contains unresolved imports")
    symbols = {name: int(addr, 16) for line in command(prefix+"nm", "--defined-only", str(code)).splitlines()
               for addr, _, name in [line.split()]}
    blob = out / "loader.bin"
    command(prefix+"objcopy", "-O", "binary", "-j", ".payload", str(code), str(blob))
    text = blob.read_bytes()
    ph = struct.Struct("<8I")
    if struct.unpack_from("<I", data, 28) != (52,) or struct.unpack_from("<HH", data, 42) != (32, 9):
        raise ValueError("unexpected ELF program header layout")
    note, rw = 52+6*ph.size, 52+4*ph.size
    rw_header = list(ph.unpack_from(data, rw))
    if ph.unpack_from(data, note)[0] != 4 or rw_header[:3] != [1, 0x178470, 0x198470]:
        raise ValueError("unexpected loadable segments")
    if rw_header[2]+rw_header[5] > 0x1C4100 or len(text) > 65536:
        raise ValueError("loader or data reservation exceeds the mapped area")
    rw_header[5] = 0x1C5000-rw_header[2]
    ph.pack_into(data, rw, *rw_header)
    at = (len(data)+0xFFFF)&~0xFFFF
    ph.pack_into(data, note, 1, at, TEXT, TEXT, len(text), len(text), 5, 65536)

    for address, (expected, target) in PATCHES.items():
        old, = struct.unpack_from("<I", data, address-0x10000)
        if old != expected:
            raise ValueError(f"unexpected instruction at {address:#x}")
        if isinstance(target, str):
            delta = symbols[target] - address - 8
            if delta % 4 or not -(1 << 25) <= delta < 1 << 25:
                raise ValueError(f"branch out of range: {target}")
            target = (old & 0xFF000000) | ((delta >> 2) & 0xFFFFFF)
        struct.pack_into("<I", data, address-0x10000, target)
    data.extend(bytes(at-len(data)))
    data.extend(text)
    result = out / "vrtemu"
    result.write_bytes(data)
    result.chmod(0o755)
    (out / "libs").mkdir()
    (out / "libs/d35-snes.so").write_bytes(payload)
    print(f"Patched {len(PATCHES)} instruction sites; added {len(text)} bytes of owned code")
    print(f"{sha(data)}  {result}")
    print(f"{CORE_PIN}  {out / 'libs/d35-snes.so'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock", type=Path)
    parser.add_argument("optimized_core", type=Path)
    parser.add_argument("new_local_output", type=Path)
    args = parser.parse_args()
    assemble(args.stock.resolve(), args.optimized_core.resolve(), args.new_local_output.resolve())


if __name__ == "__main__":
    main()

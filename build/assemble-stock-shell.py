"""Build the D-R35 stock-shell prototype from a locally supplied pinned ELF."""
import argparse
import hashlib
from pathlib import Path
import struct
import subprocess
import sys
import tempfile


PIN = "8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72"
CORE_PIN = "70d885151b7d3cac05ae69fc9653974c420b49d5cb20f95b09af547f319a8936"
TEXT = 0x1D0000
TEXT_LIMIT = 0x20000
PATCHES = {
    0xA5014: (0xEBFFFBE7, 0xE3A00001),  # defer open until the ROM has been read
    0xA502C: (0xEAFFFE67, "run_snes"),
    0xA42E8: (0xEBFDB748, "stock_resolve_run"),
    0x98174: (0xEBFFA709, "stock_load_settings"),
    0x81E6C: (0xEBFE3F3B, "stock_language"),
    0x984DC: (0xEBFFD6C0, "stock_settings"),
    0x8E30C: (0xEBFFE015, "stock_settings_key"),
    0x8EA00: (0xEBFFDE58, "stock_settings_key"),
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
    0x83504: (0xEBFFF570, "stock_search_match"),
    0x835C0: (0xEBFFF895, "stock_search_finish_page"),
    0x8A79C: (0xEBFFE0C1, "stock_load_art"),
    0x8E3A0: (0xEBFFD1C0, "stock_load_art"),
    0x8F48C: (0xEBFFCD85, "stock_load_art"),
    0x82B08: (0xEB007F08, "stock_theme_resource"),
    # The text renderer adds 29 pixels to these y positions for the baseline.
    0x8F860: (0xE30021B2, 0xE30021A7),  # first help baseline at 452
    0x8F884: (0xE30021BE, 0xE30021B9),  # second help baseline at 470
}
NATIVE_AUDIO_PATCHES = {
    0xA4704: (0xEBFDB5FF, "stock_game_sleep"),
    0xA4660: (0xEBFFDCE3, "stock_pause_audio"),
    0xA4580: (0xEBFDBE93, "stock_audio_heartbeat"),
}
VESPER_PATCHES = {
    0x1231C: (0xEB000436, "vesper_update"),
    0x135C0: (0xEB024C24, "vesper_update_prepare"),
    0x13178: (0xEBFFFFA7, "vesper_update_percent"),
    0x131A0: (0xEB024D2C, "vesper_update_progress"),
    0x13280: (0xEB024CF4, "vesper_update_complete"),
    0x132AC: (0xEB024CE9, "vesper_update_detail"),
    0x13318: (0xEB024CCE, "vesper_update_detail"),
    0x13950: (0xEBFFFDD2, "vesper_update_program"),
    0x13984: (0xEB024B33, "vesper_update_detail"),
}
GRID_PATCHES = {
    0x13FC0: (0xEBFFFF9A, "stock_home_adc_overlay"),
    0x13E30: (0xE59F215C, "launcher_display_adc"),
    0xA6658: (0xE59FC024, "launcher_display_frame"),
    # Home enters immediately before the original main-menu dispatch.
    0x9846C: (0xE5974008, "stock_home_dispatch"),
    # Enter a specific platform through the stock type browser and return
    # directly to Home on Back.
    0x89DC8: (0xEBFFF166, "stock_home_type_key"),
    0x8A008: (0xEBFFF0D6, "stock_home_type_key"),
    0x8A5C0: (0xE59D300C, "stock_home_type_back"),
    0x8A6D0: (0xEB006FE0, "stock_home_type_frame"),
    0x986F4: (0xEBFFB71B, "launcher_menu_key"),
    0x98818: (0xEBFFB6D2, "launcher_menu_key"),
    0x98ACC: (0xEBFFB625, "launcher_menu_key"),
    0x98C0C: (0xEBFFB5D5, "launcher_menu_key"),
    0x884EC: (0xEBFFF79D, "launcher_menu_key"),
    0x8862C: (0xEBFFF74D, "launcher_menu_key"),
    0x8B754: (0xEBFFEB03, "launcher_menu_key"),
    0x8B884: (0xEBFFEAB7, "launcher_menu_key"),
    0x8BABC: (0xEBFFEA29, "launcher_menu_key"),
    0x8BAE0: (0xEBFFEA20, "launcher_menu_key"),
    0x8C200: (0xEBFFE858, "launcher_menu_key"),
    0x8C224: (0xEBFFE84F, "launcher_menu_key"),
    0x8CB6C: (0xEBFFE5FD, "launcher_menu_key"),
    0x8CDFC: (0xEBFFE559, "launcher_menu_key"),
    0x8CE20: (0xEBFFE550, "launcher_menu_key"),
    0x8D07C: (0xEBFFE4B9, "launcher_menu_key"),
    0x8D4C0: (0xEBFFE3A8, "launcher_menu_key"),
    0x8D4E4: (0xEBFFE39F, "launcher_menu_key"),
    0x8DCA0: (0xEBFFE1B0, "launcher_menu_key"),
    0x8DD10: (0xEBFFE194, "launcher_menu_key"),
    0x8F0EC: (0xEBFFDC9D, "launcher_menu_key"),
}
PAUSE_PATCHES = {
    0x9BBEC: (0xEB002A99, "launcher_pause_frame"),
    0x9BC08: (0xEBFFA9D6, "launcher_pause_key"),
    0x9BC20: (0xEBFFA9D0, "launcher_pause_key"),
    0x9BC2C: (0xEBFFDA07, "launcher_pause_exit"),
    0x92574: (0xEB005037, "launcher_exit_frame"),
    0x92590: (0xEBFFCF74, "launcher_exit_key"),
    0x925B0: (0xEBFFCF6C, "launcher_exit_key"),
    # Replace function entries so the pause menu's dispatch table also uses
    # the wrappers. The wrappers replay the first PC-relative load.
    0x91050: (0xE59F2764, "load_menu"),
    0x91140: (0xEBFE0361, "load_menu_copy"),
    0x91268: (0xEBFE029C, "load_slot_probe"),
    0x91434: (0xEB005487, "load_first_frame"),
    0x914A8: (0xEBFFD3AE, "load_slot_key"),
    0x914AC: (0xE3500040, "load_slot_cancel"),
    0x915A0: (0xEB00542C, "load_next_frame"),
    0x8F5C0: (0xE59FCE34, "controls_menu"),
    0x8F8D0: (0xEB005B60, "controls_first"),
    0x8FA50: (0xEB005B00, "controls_next"),
    0x8F69C: (0xEBFFC341, "controls_panel"),
    0x90034: (0xEBFFC0DB, "controls_panel"),
    0x8F708: (0xEBFFFF8A, "controls_preview"),
    0x8F874: (0xEBFFD906, "controls_help_first"),
    0x8F898: (0xEBFFD8FD, "controls_help_first"),
    0x903C8: (0xEBFFD631, "controls_help_first"),
}
SETTINGS_PATCHES = {
    0x8EA4C: (0xEBFFFC07, "launcher_language_picker"),
    0x96F48: (0xEBFFDAC8, "launcher_language_picker"),
    0x8918C: (0xEBFFFF33, "launcher_menu_mix"),
    0x87754: (0xEBFFFF26, "launcher_menu_sound_close"),
    0x99B2C: (0xEBFFB058, "search_caret"),
    0x81EE4: (0xEBFE4BC7, "launcher_apply_saved_brightness"),
    0x8E794: (0xEBFE199B, "launcher_apply_saved_brightness"),
    0x8F0EC: (0xEBFFDC9D, "launcher_reset_key"),
    0x8EEFC: (0xEB005DD5, "launcher_reset_frame"),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def command(*argv):
    return subprocess.check_output(argv, text=True)


def assemble(vendor, core, out, native_audio=False, vesper=False, grid=False):
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
    options = ["-DD35_STARFOX_NATIVE_AUDIO"] if native_audio else []
    if vesper:
        options.append("-DD35_VESPER_LAUNCHER")
    if grid:
        if not vesper:
            raise ValueError("The home grid uses the Vesper menu and shutdown functions")
        options.append("-DD35_HOME_GRID")
        command(sys.executable, str(here/"make-settings-icons.py"),
                str(out/"stock-shell-settings-icons.h"))
        options.extend(("-I", str(out)))
    command(prefix+"gcc", "-std=gnu11", "-O3", "-Wall", "-Wextra", "-Werror", "-ffreestanding",
            "-fno-builtin", "-fno-pic", "-fno-pie", "-fno-stack-protector",
            "-fno-unwind-tables", "-fno-asynchronous-unwind-tables", "-marm", "-mcpu=cortex-a7",
            "-mfpu=neon-vfpv4", "-mfloat-abi=hard", "-nostdlib", "-static", "-no-pie",
            "-Wl,--build-id=none", "-Wl,-T,"+str(linker),
            "-I"+str(here / "snes9x2005/libretro-common/include"),
            *options, str(here / "stock-shell-loader.c"), "-o", str(code))
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
    if rw_header[2]+rw_header[5] > 0x1C4100 or len(text) > TEXT_LIMIT:
        raise ValueError("loader or data reservation exceeds the mapped area")
    rw_header[5] = 0x1C5000-rw_header[2]
    ph.pack_into(data, rw, *rw_header)
    at = (len(data)+0xFFFF)&~0xFFFF
    ph.pack_into(data, note, 1, at, TEXT, TEXT, len(text), len(text), 5, 65536)

    patches = dict(PATCHES)
    if native_audio:
        patches.update(NATIVE_AUDIO_PATCHES)
    if vesper:
        patches.update(VESPER_PATCHES)
        # Only calls from the menu and list routines, before the game pause UI.
        for address in range(0x88358, 0x9a358, 4):
            expected = 0xEB000000 | (((0x8750C - address - 8) >> 2) & 0xFFFFFF)
            if address not in patches and struct.unpack_from("<I", data, address-0x10000)[0] == expected:
                patches[address] = expected, "vesper_menu_effect"
    if grid:
        patches.update(GRID_PATCHES)
        patches.update(PAUSE_PATCHES)
        patches.update(SETTINGS_PATCHES)
    for address, (expected, target) in patches.items():
        old, = struct.unpack_from("<I", data, address-0x10000)
        if old != expected:
            raise ValueError(f"unexpected instruction at {address:#x}")
        if isinstance(target, str):
            delta = symbols[target] - address - 8
            if delta % 4 or not -(1 << 25) <= delta < 1 << 25:
                raise ValueError(f"branch out of range: {target}")
            branch = (0xEA000000 if address in (0x13E30, 0x91050, 0x8F5C0, 0xA6658) else
                      0xEB000000 if address in GRID_PATCHES or address==0x914AC else old & 0xFF000000)
            target = branch | ((delta >> 2) & 0xFFFFFF)
        struct.pack_into("<I", data, address-0x10000, target)
    data.extend(bytes(at-len(data)))
    data.extend(text)
    result = out / "vrtemu"
    result.write_bytes(data)
    result.chmod(0o755)
    (out / "libs").mkdir()
    (out / "libs/d35-snes.so").write_bytes(payload)
    if native_audio:
        library = out / "libs/d35-starfox-audio.so"
        sysroot = here / "sysroot/lib"
        command(prefix+"gcc", "-std=gnu11", "-O3", "-Wall", "-Wextra", "-Werror",
                "-fPIC", "-fvisibility=hidden", "-fno-stack-protector",
                "-D_TIME_BITS=32", "-D_FILE_OFFSET_BITS=32", "-mcpu=cortex-a7",
                "-mfpu=neon-vfpv4", "-marm", "-mfloat-abi=hard", "-shared", "-nostdlib",
                "-Wl,-z,defs", "-L"+str(sysroot),
                str(here/"stock-shell-audio.c"), str(here/"snes-mvp/audio-owner.c"),
                str(here/"snes-mvp/native-pcm.c"), "-l:libpthread-2.30.so",
                "-l:libc-2.30.so", "-l:libgcc_s.so.1", "-l:ld-2.30.so", "-o", str(library))
        print(f"{sha(library.read_bytes())}  {library}")
    print(f"Patched {len(patches)} instruction sites; added {len(text)} bytes of owned code")
    print(f"{sha(data)}  {result}")
    print(f"{CORE_PIN}  {out / 'libs/d35-snes.so'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock", type=Path)
    parser.add_argument("optimized_core", type=Path)
    parser.add_argument("new_local_output", type=Path)
    parser.add_argument("--starfox-native-audio", action="store_true")
    parser.add_argument("--vesper-launcher", action="store_true")
    parser.add_argument("--home-grid", action="store_true")
    args = parser.parse_args()
    assemble(args.stock.resolve(), args.optimized_core.resolve(), args.new_local_output.resolve(),
             args.starfox_native_audio, args.vesper_launcher, args.home_grid)


if __name__ == "__main__":
    main()

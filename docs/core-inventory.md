# Emulator inventory

These identities come from preserved executable strings/symbols, with the PS1 binary hash checked against the active card during review. Embedded revision strings are not proof of an unmodified upstream tree. Filename alone is not a reliable core identity.

| File/family | Observed identity/path | Limit |
|---|---|---|
| SNES replacement | Snes9x2005 Plus, pinned a79dfe9047e7fec58808aefe48ad2bf499c7af11 | Actual positive adapter/MVP evidence; full rendering in every scene not established |
| NES `emu_nes.so` | FCEUmm family | Modern candidate qualification remains separate |
| GBA `emu_gba.so` | gpSP v0.91 strings; private skip/double-buffer hooks | Present hook is not measured performance |
| `emu_mgba.so` | TGB Dual v0.8.3 9be31d3 | **Not mGBA**, despite filename |
| Mega Drive `emu_md.so` | PicoDrive1.91 cbc93b6; Cyclone symbols | Live per-game behavior unmeasured here |
| MAME `emu_mame.so` | MAME2000; Cyclone68000 symbols | A compiled driver is not proof a ROM fits/runs |
| FBA/NeoGeo | FB Alpha2012 v0.2.97.29 621e371 | ROMset/build identity matters |
| `emu_extend.so` | FB Alpha v0.2.97.42 621e371 | Broad driver presence is not whole-platform compatibility |
| PS1 `emu_pcsx.so` | PCSX-ReARMed r22/44de3b6; ARM dynarec, NEON GTE/software GPU | Live settings, cadence/CPU and raster skip cost remain unmeasured |

PS1 observed hash: `30879f1b5a652d0b6f60bd2ab0e71194c9790b779d94c4c8e5488eb56b07a339`, 1,227,580 bytes. Its `.bss` is about25.61MiB, including a16MiB translation cache; virtual demand-zero size is not RSS. It has ARM new_dynarec/ari64 and NEON CPU raster/GTE paths, not evidence of a usable Vivante GPU.

Its private SetFrameSkip definitely avoids final color conversion and submission; that alone does not prove GPU rasterization was skipped. Config.Cpu selects interpreter vs dynarec, but the live setting was not captured. PS1 playing smoothly is not a control proving spare SNES budget: guest ISA, raster/audio workload, unique frame count, skips and actual emulated speed differ.

The [dated core strategy review](reference/platform-redesign/core-notes.txt) contains candidate portfolios and primary upstream links for NES, SNES, GB/GBC, GBA, Genesis, SMS/GG, PCE, arcade and PS1. They are proposed qualification choices from2026-10-04, not implemented support or promises of playable speed. Current MVP supports only SNES.

A future manifest needs exact source/toolchain/CPU backend, timing, formats, ROMset/BIOS requirements, memory ceiling and state compatibility. Test newer cores on the corrected common host; do not use age, filename, static NEON presence or another system's smooth scene as the decision rule.

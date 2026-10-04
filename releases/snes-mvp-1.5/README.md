# SNES MVP 1.5

Owned ARM launcher/runner and one-shot wrapper. Corrects the shared physical D-pad map. Local checks pass; this correction still needs physical confirmation. Version1.4 is device-confirmed for launcher operation, FF6 start and save-state load.

Required on the device: matching vendor Linux/glibc2.30 runtime, GPIO/chunk/scaler/display/OSS devices, `/usr/retro/driver.so`, and the exact qualified Plus core `/usr/retro/libs/emu_sfc_plus.so`. No ROM, personal state, driver/core/runtime library or full firmware is included.

`manifest.json` pins the executable/wrapper and verification. See [build/test/deployment](../../docs/build-and-test.md) and [boot/hardware contracts](../../docs/boot-and-hardware-contracts.md) before installing on another unit. The current guarded installer expects the tested v11 card baseline, not an arbitrary factory card.

The intended owned directory is `/usr/retro/snes-mvp`. Its wrapper runs before stock main only when `armed` exists, consumes that marker, completes vendor splash cleanup, then starts the runtime. A following reboot automatically takes stock. Private game progress remains under that directory's `saves` namespace, supplied/created by its owner.

First verify all four directions through in-game character movement. A/Start launches, B returns from the library, MENU or Start+Select opens pause actions. Back up and preserve your own original init/progress; another owner's save or init is not a recovery image.

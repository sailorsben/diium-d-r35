# Source and dependency notices

This repository preserves project-authored launcher/runtime, adapter, analysis and investigation material. Existing notices in individual source files remain applicable. No repository-wide license has been substituted for component notices.

The tested SNES core is Snes9x 2005 Plus from [libretro/snes9x2005](https://github.com/libretro/snes9x2005), pinned in `build/core-source-commit.txt`. Obtain upstream source and retain its license and notices. The 2010 comparison pin is recorded separately. Libretro headers come from the pinned upstream source tree.

Device libc, loader, driver, factory launcher and other firmware dependencies are supplied from the owner's device/runtime export. Their binaries are not redistributed here. ROMs and personal save files are also absent. The release executable links dynamically against the device's runtime libraries; it is our userspace prototype, not a firmware image.

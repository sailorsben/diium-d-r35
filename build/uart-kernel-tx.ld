SECTIONS { .tx 0xc01178d8 : { *(.text.tx) } .stop 0xc0117a00 : { *(.text.stop) } /DISCARD/ : { *(.ARM.attributes) *(.comment) } }
ASSERT(SIZEOF(.tx) <= 184, "TX body exceeds original region")
ASSERT(SIZEOF(.stop) <= 16, "stop body exceeds original region")

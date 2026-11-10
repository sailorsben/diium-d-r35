/* Offline census of LOOP locations and their live instruction bytes. */
static uint32_t d35_loops[1024][4];

static void d35_record_loop(void)
{
   uint32_t location = (PBR << 16) | USEX16(R15);
   uint32_t target = USEX16(R13);
   uint32_t bytes = PRGBANK(R15) | ((uint32_t)PRGBANK(target) << 8) |
                    ((uint32_t)PRGBANK(target + 1) << 16) |
                    ((uint32_t)PRGBANK(target + 2) << 24);
   unsigned slot = ((location ^ target ^ bytes) * 2654435761u) >> 22;
   for (unsigned probe = 0; probe < 1024; ++probe, slot = (slot + 1) & 1023) {
      uint32_t *entry = d35_loops[slot];
      if (!entry[3] || (entry[0] == location && entry[1] == target && entry[2] == bytes)) {
         entry[0] = location;
         entry[1] = target;
         entry[2] = bytes;
         ++entry[3];
         return;
      }
   }
}

__attribute__((visibility("default"))) void d35_fx_loops(uint32_t *out)
{
   memcpy(out, d35_loops, sizeof(d35_loops));
   memset(d35_loops, 0, sizeof(d35_loops));
}

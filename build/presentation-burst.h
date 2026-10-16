/* Deliberate extra main-thread CPU; identical for both policies. RAM only. */
static unsigned presentation_load_ms,presentation_load_events;
static uint64_t presentation_load_cpu;
static void presentation_burst_begin(void) {
 const char *value=getenv("D35_PRESENTATION_LOAD_MS");
 presentation_load_ms=value?(unsigned)cost_parse(value):0;
 presentation_load_events=0;presentation_load_cpu=0;
}
static void presentation_burst(unsigned frame) {
 if(!presentation_load_ms||frame<239||frame>959||(frame-239)%120)return;
 uint64_t began=thread_cpu_ns(),end;
 do {end=thread_cpu_ns();}while(end-began<(uint64_t)presentation_load_ms*1000000u);
 presentation_load_cpu+=end-began;++presentation_load_events;
}

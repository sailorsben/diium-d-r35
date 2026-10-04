/* Temporary diagnostic. Two cycles of 12 s normal / 12 s hold / 12 s black,
 * measured in emulated frames. Thereafter normal video permanently resumes.
 * Audio/core/controller callbacks are unchanged. Save state reports phases. */
static bool display_test_disabled;
static uint32_t display_test_counts[3], display_test_last=UINT32_MAX;
static unsigned display_test_mode(uint64_t run)
{
   if (display_test_disabled || run>=4320) return 0;
   return (unsigned)(run/720)%3;
}
static void display_test_reset(void)
{
   const char *test=getenv("D35_DISPLAY_TEST_DISABLE");
   display_test_disabled=test && !strcmp(test,"1");
   memset(display_test_counts,0,sizeof(display_test_counts));
   display_test_last=UINT32_MAX;
}
static bool display_test_save(void)
{
   const char *directory=getenv("D35_CAPTURE_DIRECTORY");
   char path[1100]; FILE *f;
   if (!directory) directory="/usr/retro";
   if (snprintf(path,sizeof(path),"%s/emu_sfc_plus_v8_display_test.txt",directory)>=(int)sizeof(path)) return false;
   f=fopen(path,"w"); if (!f) return false;
   fprintf(f,"Temporary display comparison; unchanged game audio; normal display resumes after run 4320.\n");
   fprintf(f,"test_disabled=%u\nnormal_callbacks=%u\nhold_callbacks=%u\nblack_callbacks=%u\nlast_mode=%u\n",
      display_test_disabled,display_test_counts[0],display_test_counts[1],display_test_counts[2],display_test_last);
   return capture_sync_close(f);
}

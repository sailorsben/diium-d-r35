"""Reuse exact original-command replay qualification; no A7 timing evidence."""
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('audit',ROOT/'build/qualify-architecture-audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
audit.OUT=ROOT/'build/architecture-followup-private-v1'
audit.FIELDS.update({32:'BG_draw_calls',33:'fully_clipped_BG_calls',34:'fully_clipped_BG_rows',36:'fully_clipped_OBJ_calls',37:'fully_clipped_OBJ_rows',40:'color_math_render_entries',41:'no_main_math_recipient_entries',42:'no_main_math_recipient_rows',45:'OBJ_window_searches',46:'OBJ_window_boundaries_advanced',48:'OBJ_line_sprite_visits',49:'OBJ_tile_visits',50:'OBJ_clipped_loop_steps',52:'brightness_rebuild_calls',54:'brightness_entries_rebuilt',56:'DMA_calls',57:'strict_contiguous_VRAM_DMA_bytes',58:'strict_contiguous_VRAM_DMA_calls',59:'strict_span_tile_invalidations'})
if __name__=='__main__':audit.main()

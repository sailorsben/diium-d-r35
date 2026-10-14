"""Original-output qualification with store provenance, no rendering changes."""
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('follow',ROOT/'build/qualify-architecture-followup.py');follow=importlib.util.module_from_spec(spec);spec.loader.exec_module(follow)
audit=follow.audit;audit.OUT=ROOT/'build/architecture-stream-private-v1'
audit.FIELDS.update({64:'tracked_main_RGB_pixel_writes',65:'overwritten_main_RGB_writes',66:'tile_color_math_pixel_writes',67:'overwritten_math_pixel_writes',68:'final_math_pixel_owners',69:'untracked_scalar_backdrop_tail_pixels',70:'palette_cache_queries',71:'palette_cache_misses',73:'palette_cache_epoch_changes',74:'NEON_palette_table_preparations',75:'sub_full_tile_source_row_requests',76:'main_full_tile_source_row_requests',77:'matched_main_sub_source_row_requests',78:'unique_sub_source_row_keys',80:'explicit_depth_initialization_bytes',81:'explicit_scalar_RGB_initialization_bytes',82:'backdrop_bulk_depth_scan_bytes',86:'final_backdrop_math_pixel_writes',90:'brightness_zero_rebuilds',91:'brightness_nonzero_rebuilds',92:'source_observer_table_overflow',93:'unsupported_layout_regions',94:'foreground_depth_pixels_missing_store_provenance'})
if __name__=='__main__':audit.main()

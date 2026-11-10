"""Generate isolated experiments against the corrected five-game core source."""
from hashlib import sha256
from pathlib import Path
import re
import shutil
import sys


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f'Expected one source anchor: {old[:80]}')
    return source.replace(old, new)


def generate(core, mode):
    if mode in ('offset-plain','offset-plain-census'):
        gfx=core/'source/gfx.c'
        s=gfx.read_text()
        anchor='static void DrawBackgroundOffset('
        body='''/* Mode 2: absent the layer enable bit in all offset map words, both
 * offsets reduce to normal line scroll. Leave wrapped/unproved maps alone. */
static bool d35_offset_plain(unsigned bg) {
   unsigned addr=PPU.BG[2].SCBase<<1, shape=PPU.BG[2].SCSize&3;
   unsigned bytes=(1+(shape&1))*(1+(shape>>1))*2048u;
   if(addr+bytes>65536 || bg>1 || IPPU.HalfWidthPixels ||
      IPPU.DoubleWidthPixels || IPPU.DoubleHeightPixels || IPPU.Interlace) return false;
   uint16x8_t mask=vdupq_n_u16(1u<<(bg+13));
   for(unsigned at=0;at<bytes;at+=16) {
      uint16x8_t bits=vandq_u16(mask,vld1q_u16((const uint16_t *)(Memory.VRAM+addr+at)));
      uint64x2_t lanes=vreinterpretq_u64_u16(bits);
      if(vgetq_lane_u64(lanes,0)|vgetq_lane_u64(lanes,1)) return false;
   }
   return true;
}
'''
        branch='''      case 2:
      case 4: /* Used by Puzzle Bobble */
         DrawBackgroundOffset(BGMode, bg, Z1, Z2);
         return;'''
        if mode=='offset-plain':
            replacement='''      case 2:
         if (d35_offset_plain(bg)) break;
         /* Otherwise retain the original offset walker. */
         /* fall through */
      case 4:
         DrawBackgroundOffset(BGMode, bg, Z1, Z2);
         return;'''
        else:
            replacement='''      case 2:
         d35_plain_rows+=(GFX.EndY-GFX.StartY+1);
         if(d35_offset_plain(bg)) d35_plain_hits+=(GFX.EndY-GFX.StartY+1);
         /* fall through */
      case 4:
         DrawBackgroundOffset(BGMode, bg, Z1, Z2);
         return;'''
            body='''static uint64_t d35_plain_rows,d35_plain_hits;
__attribute__((visibility("default"))) void d35_offset_read(uint64_t *out) {
   out[0]=d35_plain_rows;out[1]=d35_plain_hits;d35_plain_rows=d35_plain_hits=0;
}
'''+body
            link=core/'link.T'
            link.write_text(replace_once(link.read_text(),'retro_*;','retro_*; d35_offset_read;'))
        s=replace_once(s,anchor,body+'\n'+anchor)
        gfx.write_text(replace_once(s,branch,replacement),newline='\n')
        return
    if mode in ('offset-row','offset-census'):
        gfx=core/'source/gfx.c'
        s=gfx.read_text()
        a,b=s.index('static void DrawBackgroundOffset('),s.index('static void DrawBackgroundMode5(')
        body=s[a:b]
        start='''            if (BG.TileSize == 8)
               (*DrawClippedTilePtr)(Tile, s, Offset, Count, VirtAlign, Lines);'''
        assert body.count(start)==1
        if mode=='offset-row':
            # Reuse the same resolved renderer pair. Tile number/flip adjustment
            # is identical; only the clipping dispatcher changes at full width.
            at=body.index(start);end=body.index('\n            Left += Count;',at)
            body=body[:at]+'''            if (BG.TileSize != 8) {
               unsigned horizontal = Quot & 1;
               if (Tile & H_FLIP) horizontal ^= 1;
               Tile += ((Tile & V_FLIP) ? t2 : t1) + horizontal;
            }
            if (BGMode == 2 && Offset == 0 && Count == 8 && !IPPU.HalfWidthPixels)
               (*DrawTilePtr)(Tile, s, VirtAlign, Lines);
            else
               (*DrawClippedTilePtr)(Tile, s, Offset, Count, VirtAlign, Lines);
'''+body[end:]
        else:
            body=replace_once(body,start,'''            if (BGMode == 2) {
               ++d35_offset_calls;
               if (Offset == 0 && Count == 8 && !IPPU.HalfWidthPixels) ++d35_offset_full;
            }
'''+start)
            body='''static uint64_t d35_offset_calls,d35_offset_full;
__attribute__((visibility("default"))) void d35_offset_read(uint64_t *out) {
   out[0]=d35_offset_calls;out[1]=d35_offset_full;d35_offset_calls=d35_offset_full=0;
}
'''+body
            link=core/'link.T'
            link.write_text(replace_once(link.read_text(),'retro_*;','retro_*; d35_offset_read;'))
        gfx.write_text(s[:a]+body+s[b:],newline='\n')
        return
    if mode=='span-census':
        gfx=core/'source/gfx.c'
        s=replace_once(gfx.read_text(),'extern bool reduce_sprite_flicker;',
                       'extern bool reduce_sprite_flicker;\n#include "snes-throughput-span.h"')
        s=replace_once(s,'   d35_window_reset();d35_fixed_reset();',
                       '   d35_window_reset();d35_fixed_reset();\n   d35_span_begin();')
        gfx.write_text(replace_once(s,'   endy   = GFX.EndY;',
                       '   endy   = GFX.EndY;\n   d35_span_candidate(starty,endy);'),newline='\n')
        shutil.copyfile(Path(__file__).with_name('snes-throughput-span.h'),core/'source/snes-throughput-span.h')
        link=core/'link.T'
        link.write_text(replace_once(link.read_text(),'retro_*;','retro_*; d35_span_read;'))
        return
    if mode=='reuse-census':
        gfx=core/'source/gfx.c'
        s=replace_once(gfx.read_text(),'extern bool reduce_sprite_flicker;',
                       'extern bool reduce_sprite_flicker;\n#include "snes-throughput-reuse.h"')
        s=replace_once(s,'   d35_window_reset();d35_fixed_reset();',
                       '   d35_window_reset();d35_fixed_reset();\n   reuse.eligible=reuse.match=0;\n   if(!IPPU.RenderThisFrame)reuse.valid=0;')
        gfx.write_text(replace_once(s,'   endy   = GFX.EndY;',
                       '   endy   = GFX.EndY;\n   d35_reuse_candidate(starty,endy);'),newline='\n')
        shutil.copyfile(Path(__file__).with_name('snes-throughput-reuse.h'),core/'source/snes-throughput-reuse.h')
        link=core/'link.T'
        link.write_text(replace_once(link.read_text(),'retro_*;','retro_*; d35_reuse_read;'))
        return
    if mode.startswith('dma-'):
        return generate_dma(core, mode)
    path = core / 'source/fxinst.c'
    original = path.read_bytes()
    source = path.read_text()
    # Source trees may carry CRLF. Pin the normalized source and exact loop/table.
    if sha256(original.replace(b'\r\n', b'\n')).hexdigest() != '171833443fb47fdb99e169fbceeaaaeaacce33f9a2f13f16951b854084f2eb65':
        raise ValueError('Use the exact multigame-fixes-private-v1/core source')
    anchor = 'uint32_t fx_run(uint32_t nInstructions)'
    start = source.index(anchor)
    end = source.index('\n/*** Special table', start)
    if mode == 'baseline':
        return
    if mode == 'census':
        source = replace_once(source, anchor, '''
#include <time.h>
static uint64_t d35_fx_ops[1024], d35_fx_ns, d35_fx_runs;
__attribute__((visibility("default"))) void d35_fx_census(uint64_t *out) {
   memcpy(out,d35_fx_ops,sizeof(d35_fx_ops));
   memset(d35_fx_ops,0,sizeof(d35_fx_ops));
   out[1024]=d35_fx_ns;out[1025]=d35_fx_runs;
   d35_fx_ns=d35_fx_runs=0;
}
static uint64_t d35_fx_clock(void) {
   struct timespec t;
   if(clock_gettime(CLOCK_THREAD_CPUTIME_ID,&t)) return 0;
   return (uint64_t)t.tv_sec*1000000000u+t.tv_nsec;
}
''' + anchor)
        source = replace_once(source, '   while (TF(G) && (GSU.vCounter-- > 0))\n      FX_STEP;', '''
   uint64_t t=d35_fx_clock();
   while (TF(G) && (GSU.vCounter-- > 0)) {
      ++d35_fx_ops[(GSU.vStatusReg&0x300)|PIPE];
      FX_STEP;
   }
   d35_fx_ns+=d35_fx_clock()-t;
   ++d35_fx_runs;''')
        link = core / 'link.T'
        link.write_text(replace_once(link.read_text(), 'retro_*;', 'retro_*; d35_fx_census;'))
    else:
        table = source.split('void (*fx_apfOpcodeTable[])(void) =', 1)[1]
        ops = re.findall(r'&(fx_\w+)', table)
        if len(ops) != 1024 or {i for i, op in enumerate(ops) if op == 'fx_stop'} != {0,256,512,768}:
            raise ValueError('STOP must be opcode zero in all four ALT tables')
        # No opcode except STOP reads/writes vCounter or changes the G bit.
        # Keep its pre-handler value, post-decrement on exhaustion and false-G entry.
        run = '''uint32_t fx_run(uint32_t nInstructions)
{
   uint32_t remaining = nInstructions;
   GSU.vCounter = nInstructions;
   READR14;
   if (TF(G)) {
      while (remaining-- > 0) {
         uint32_t opcode = PIPE;
         FETCHPIPE;
         if (!opcode) {
            GSU.vCounter = remaining;
            fx_stop();
            return nInstructions - GSU.vInstCount;
         }
         uint32_t index = (GSU.vStatusReg & 0x300) | opcode;
         DISPATCH
      }
      GSU.vCounter = remaining;
   }
   return nInstructions - GSU.vInstCount;
}
'''
        if mode == 'counter':
            dispatch = 'fx_apfOpcodeTable[index]();'
        elif mode in ('dispatch','hot'):
            # Inline just the compact register/branch families. The four dynamic
            # PLOT/RPIX slots and all other opcodes keep their original handlers.
            groups = {}
            for index, op in enumerate(ops):
                code = index & 255
                if (mode=='dispatch' and (1 <= code < 0x30 or 0x3c <= code <= 0x3f or 0xb0 <= code <= 0xbf)) or (
                        mode=='hot' and index in (0xd1,0x3c,0x31,0x3d,0x01)):
                    groups.setdefault(op, []).append(index)
            if mode=='dispatch':
                dispatch = 'switch (index) {\n'
                for op, cases in groups.items():
                    dispatch += '         ' + ' '.join(f'case {i:#05x}:' for i in cases) + f' {op}(); break;\n'
                dispatch += '         default: fx_apfOpcodeTable[index](); break;\n         }'
            else:
                dispatch = '\n         '.join(f'if (index=={cases[0]:#05x}) {op}(); else' for op,cases in groups.items())
                dispatch += '\n         fx_apfOpcodeTable[index]();'
        else:
            raise ValueError(mode)
        source = source[:start] + run.replace('DISPATCH', dispatch) + source[end:]
    path.write_text(source, newline='\n')


def generate_dma(core, mode):
    p=core/'source/dma.c'
    s=p.read_text()
    start='               memcpy(Memory.VRAM+v,base+p,count);'
    end='               PPU.VMA.Address+=count/2;count=0;'
    a,b=s.index(start),s.index(end)
    original=s[a:b]
    assert 'memset(IPPU.TileCached[bits]+first,0,last-first+1);' in original
    assert s.count(start)==1 and s.count(end)==1
    if mode=='dma-same':
        replacement='''               /* Identical VRAM does not invalidate decoded tile bytes. */
               if (memcmp(Memory.VRAM+v,base+p,count)) {
'''+''.join('   '+line+'\n' for line in original.splitlines())+'''               }
'''
    elif mode=='dma-delta':
        replacement='''               /* Compare per 2bpp tile boundary, not per transferred byte.
                * Keep the existing raw-source restrictions and DMA finalizer. */
               if (count < 32) {
'''+''.join('   '+line+'\n' for line in original.splitlines())+'''               } else if (memcmp(Memory.VRAM+v,base+p,count)) {
                  unsigned offset=0;
                  while (offset<(unsigned)count) {
                     unsigned addr=v+offset, n=16-(addr&15u);
                     if(n>(unsigned)count-offset)n=(unsigned)count-offset;
                     if(memcmp(Memory.VRAM+addr,base+p+offset,n)) {
                        memcpy(Memory.VRAM+addr,base+p+offset,n);
                        IPPU.TileCached[0][addr>>4]=0;
                        IPPU.TileCached[1][addr>>5]=0;
                        IPPU.TileCached[2][addr>>6]=0;
                     }
                     offset+=n;
                  }
               }
'''
    elif mode=='dma-census':
        replacement='''               ++d35_dma_spans;d35_dma_bytes+=count;
               if(!memcmp(Memory.VRAM+v,base+p,count)) {++d35_dma_same;d35_dma_same_bytes+=count;}
'''+original
    else:
        raise ValueError(mode)
    s=s[:a]+replacement+s[b:]
    if mode=='dma-census':
        s=replace_once(s,'static uint8_t sdd1_decode_buffer', '''static uint64_t d35_dma_spans,d35_dma_bytes,d35_dma_same,d35_dma_same_bytes;
__attribute__((visibility("default"))) void d35_dma_census(uint64_t *out) {
   out[0]=d35_dma_spans;out[1]=d35_dma_bytes;out[2]=d35_dma_same;out[3]=d35_dma_same_bytes;
   d35_dma_spans=d35_dma_bytes=d35_dma_same=d35_dma_same_bytes=0;
}
static uint8_t sdd1_decode_buffer''')
        link=core/'link.T'
        link.write_text(replace_once(link.read_text(),'retro_*;','retro_*; d35_dma_census;'))
    p.write_text(s,newline='\n')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: prepare-snes-throughput.py COPIED_CORE MODE')
    generate(Path(sys.argv[1]), sys.argv[2])

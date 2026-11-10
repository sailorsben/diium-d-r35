/* Preserve the visible sprite list, tile quota and tie order on every row.
 * Transpose that same ordered list across a band only within one tile row. */
static unsigned d35_obj_rows(unsigned y)
{
   unsigned rows = 1;
   while (rows < 8 && y + rows <= GFX.EndY)
   {
      unsigned next = y + rows;
      if (GFX.OBJLines[next].Tiles != GFX.OBJLines[y].Tiles)
         break;
      unsigned i;
      for (i = 0; i < 32; ++i)
      {
         int sprite = GFX.OBJLines[y].OBJ[i].Sprite;
         if (GFX.OBJLines[next].OBJ[i].Sprite != sprite)
            break;
         if (sprite < 0)
         {
            i = 32;
            break;
         }
         int line = GFX.OBJLines[y].OBJ[i].Line;
         int expected = line + (PPU.OBJ[sprite].VFlip ? -(int)rows : (int)rows);
         if ((expected >> 3) != (line >> 3) || GFX.OBJLines[next].OBJ[i].Line != expected)
            break;
      }
      if (i != 32)
         break;
      ++rows;
   }
   return rows;
}

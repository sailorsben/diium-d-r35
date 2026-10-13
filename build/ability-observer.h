/* Frame-boundary RAM only; no instruction hooks, CRC scan or live SD output. */
#ifndef ABILITY_OBSERVER_H
#define ABILITY_OBSERVER_H
static unsigned char *ability_ram,ability_expected[1+8*15];
static uint16_t ability_input[1200];
struct ability_row { unsigned char attack,type,props[14],target_char,target_enemy,status[4],rage[3],dance[3];uint16_t hp[4],mp[4];uint64_t observer_ns; };
static struct ability_row ability_rows[1200];
static unsigned ability_count,ability_matches;
static unsigned ability_number(const char *s,unsigned base) {
 unsigned n=0;while(*s){unsigned d=*s>='0'&&*s<='9'?(unsigned)(*s-'0'):*s>='a'&&*s<='f'?(unsigned)(*s-'a'+10):99;if(d>=base||n>100000)return UINT32_MAX;n=n*base+d;s++;}return n;
}
static int ability_bind(void *ram,size_t size) {
 char line[128];unsigned used=0;FILE *f;const char *input=getenv("D35_ABILITY_INPUT"),*expected=getenv("D35_ABILITY_EXPECTED");
 memset(ability_input,0,sizeof(ability_input));memset(ability_rows,0,sizeof(ability_rows));ability_count=ability_matches=0;
 ability_ram=ram;if(!ram||size<0x20000||!input||!expected)return 0;
 f=fopen(input,"r");if(!f)return 0;
 while(fgets(line,sizeof(line),f)){char *a=strtok(line," \r\n"),*b=strtok(NULL," \r\n");if(!a||!b){fclose(f);return 0;}unsigned n=ability_number(a,10),bits=ability_number(b,16);if(!n||bits>65535||n>1200-used){fclose(f);return 0;}while(n--)ability_input[used++]=(uint16_t)bits;}
 fclose(f);f=fopen(expected,"rb");if(!f)return 0;size_t n=fread(ability_expected,1,sizeof(ability_expected),f);fclose(f);return n>=1&&ability_expected[0]<=8&&n==1u+15u*ability_expected[0];
}
static uint32_t ability_buttons(unsigned frame) {return frame<1200?ability_input[frame]:0;}
static void ability_observe(unsigned frame) {
 if(frame>=1200||!ability_ram)return;uint64_t began=cost_host_ns();struct ability_row *r=&ability_rows[frame];r->attack=ability_ram[0x626a];r->type=ability_ram[0x60ab];memcpy(r->props,ability_ram+0x6273,14);
 r->target_char=ability_ram[0x7b7d];r->target_enemy=ability_ram[0x7b7e];r->status[0]=ability_ram[0x3ee4];r->status[1]=ability_ram[0x3ee6];r->status[2]=ability_ram[0x3ef8];r->status[3]=ability_ram[0x3ef9];
 const unsigned offset[]={0,2,4,8};for(unsigned i=0;i<4;i++){unsigned a=0x3bf4+offset[i];r->hp[i]=ability_ram[a]|(ability_ram[a+1]<<8);a=0x3c08+offset[i];r->mp[i]=ability_ram[a]|(ability_ram[a+1]<<8);}
 for(unsigned i=0;i<3;i++){r->rage[i]=ability_ram[0x33a8+i*2];r->dance[i]=ability_ram[0x32e1+i*2];}
 for(unsigned i=0;i<ability_expected[0];i++){const unsigned char *e=ability_expected+1+i*15;if(r->attack==e[0]&&!memcmp(r->props,e+1,14))ability_matches++;}ability_count=frame+1;r->observer_ns=cost_host_ns()-began;
}
static void ability_finish(const char *dir) {
 char path[1300];snprintf(path,sizeof(path),"%s/animation.csv",dir);FILE *f=fopen(path,"w");if(!f)return;
 fprintf(f,"#observer=frame_boundary_RAM_only\n#matching_property_samples=%u\n#completion=bounded_run_not_instruction_hook_proof\nframe,input,attack,anim_type,properties,target_char,target_enemy,hp_terra,hp_wedge,hp_vicks,hp_enemy,mp_terra,mp_wedge,mp_vicks,mp_enemy,status_terra,status_wedge,status3_terra,status4_terra,rage_terra,rage_wedge,rage_vicks,dance_terra,dance_wedge,dance_vicks,observer_ns\n",ability_matches);
 for(unsigned i=0;i<ability_count;i++){const struct ability_row *r=&ability_rows[i];fprintf(f,"%u,%04x,%02x,%02x,",i,ability_input[i],r->attack,r->type);for(unsigned j=0;j<14;j++)fprintf(f,"%02x",r->props[j]);fprintf(f,",%02x,%02x",r->target_char,r->target_enemy);for(unsigned j=0;j<4;j++)fprintf(f,",%u",r->hp[j]);for(unsigned j=0;j<4;j++)fprintf(f,",%u",r->mp[j]);for(unsigned j=0;j<4;j++)fprintf(f,",%02x",r->status[j]);for(unsigned j=0;j<3;j++)fprintf(f,",%02x",r->rage[j]);for(unsigned j=0;j<3;j++)fprintf(f,",%02x",r->dance[j]);fprintf(f,",%llu\n",(unsigned long long)r->observer_ns);}
 fflush(f);fsync(fileno(f));fclose(f);ability_ram=NULL;
}
#endif

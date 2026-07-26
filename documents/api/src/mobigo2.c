#include "mobigo2.h"

/* Implemented in unsp_bridge.asm because vbcc currently cannot express DS access. */
void mg2_asm_store_far(mg2_u16 value, mg2_u16 offset, mg2_u16 segment);
mg2_u16 mg2_asm_load_far(mg2_u16 offset, mg2_u16 segment);

static mg2_u16 draw_base_lo = 0, draw_base_hi = 8;

static mg2_u16 reg_read(mg2_u16 address)
{ return mg2_asm_load_far(address,0); }
static void reg_write(mg2_u16 address, mg2_u16 value)
{ mg2_asm_store_far(value,address,0); }

static mg2_u16 gpio_base(enum mg2_gpio_port p) { mg2_u16 v=(mg2_u16)p;v<<=3;return (mg2_u16)(0x7860+v); }
static mg2_u16 timer_base(enum mg2_timer t) { mg2_u16 v=(mg2_u16)t;v<<=3;return (mg2_u16)(0x78c0+v); }
static mg2_u16 timebase_reg(mg2_u16 unit) { if(unit>2)unit=2;return (mg2_u16)(0x78b0+unit); }

void mg2_init(void)
{
    mg2_video_timing_default();
    reg_write(0x7063,0xffff);reg_write(0x7abf,0x000f);reg_write(0x78a4,0);reg_write(0x78a5,0);
}

mg2_u16 mg2_read16(mg2_u16 lo,mg2_u16 hi){return mg2_asm_load_far(lo,hi);}
void mg2_write16(mg2_u16 lo,mg2_u16 hi,mg2_u16 v){mg2_asm_store_far(v,lo,hi);}

mg2_u16 mg2_random_status(void) { return reg_read(0x70e0); }

mg2_u16 mg2_rgb565(mg2_u16 r, mg2_u16 g, mg2_u16 b)
{ mg2_u16 v; r>>=3; g>>=2; b>>=3; r<<=11; g<<=5; v=r; v+=g; v+=b; return v; }
mg2_u16 mg2_rgb555(mg2_u16 r, mg2_u16 g, mg2_u16 b)
{ mg2_u16 v; r>>=3; g>>=3; b>>=3; r<<=10; g<<=5; v=r; v+=g; v+=b; return v; }

void mg2_video_timing_default(void)
{
    reg_write(0x7050,0);reg_write(0x7051,0x010f);reg_write(0x7054,0x010f);reg_write(0x7055,0x0400);
}
void mg2_video_set_input(mg2_u16 lo,mg2_u16 hi){reg_write(0x7078,lo&0xfff0);reg_write(0x7079,hi&0x07ff);}
void mg2_video_set_output(mg2_u16 lo,mg2_u16 hi){reg_write(0x707a,lo&0xfff0);reg_write(0x707b,hi&0x07ff);}
void mg2_video_framebuffer_init(mg2_u16 lo,mg2_u16 hi)
{mg2_draw_target(lo,hi);mg2_video_set_input(lo,hi);mg2_video_enable(MG2_PPU_ENABLE|MG2_PPU_FRAME_BASE);}
void mg2_video_enable(mg2_u16 flags) { reg_write(0x707f,flags); }
mg2_u16 mg2_video_scanline(void) { return reg_read(0x7038); }
mg2_u16 mg2_video_irq_status(void) { return reg_read(0x7063); }
void mg2_video_irq_enable(mg2_u16 mask) { reg_write(0x7062,mask); }
void mg2_video_irq_ack(mg2_u16 mask) { reg_write(0x7063,mask); }

enum mg2_result mg2_video_wait_frame(mg2_u16 timeout)
{
    while (timeout--) {
        if (reg_read(0x7063) & 1) { reg_write(0x7063,1); return MG2_OK; }
    }
    return MG2_TIMEOUT;
}

enum mg2_result mg2_video_composite(mg2_u16 timeout)
{
    reg_write(0x707c,1);
    while (timeout--) if (reg_read(0x707c) & 0x8000) return MG2_OK;
    return MG2_TIMEOUT;
}

void mg2_draw_target(mg2_u16 lo,mg2_u16 hi){draw_base_lo=lo;draw_base_hi=hi;}

void mg2_draw_pixel(mg2_s16 x, mg2_s16 y, mg2_u16 c)
{mg2_u16 lo=draw_base_lo,hi=draw_base_hi,i,old;if(x>=0&&x<320&&y>=0&&y<240){for(i=0;i<(mg2_u16)y;++i){old=lo;lo=(mg2_u16)(lo+320);if(lo<old)++hi;}old=lo;lo=(mg2_u16)(lo+(mg2_u16)x);if(lo<old)++hi;mg2_write16(lo,hi&0x3f,c);}}
mg2_u16 mg2_draw_read_pixel(mg2_s16 x, mg2_s16 y)
{mg2_u16 lo=draw_base_lo,hi=draw_base_hi,i,old;if(x>=0&&x<320&&y>=0&&y<240){for(i=0;i<(mg2_u16)y;++i){old=lo;lo=(mg2_u16)(lo+320);if(lo<old)++hi;}old=lo;lo=(mg2_u16)(lo+(mg2_u16)x);if(lo<old)++hi;return mg2_read16(lo,hi&0x3f);}return 0;}

void mg2_draw_fill(mg2_u16 c)
{
    mg2_u16 i;
    for(i=draw_base_lo;i!=0xffff;++i)mg2_asm_store_far(c,i,draw_base_hi);
    mg2_asm_store_far(c,0xffff,draw_base_hi);
    for(i=0;i<11264;++i)mg2_asm_store_far(c,i,(mg2_u16)(draw_base_hi+1));
}

void mg2_draw_rect(mg2_u16 x0, mg2_u16 y0, mg2_u16 w, mg2_u16 h, mg2_u16 c)
{
    mg2_u16 x, y;
    for (y = 0; y < h; ++y) for (x = 0; x < w; ++x)
        mg2_draw_pixel((mg2_s16)(x0 + x), (mg2_s16)(y0 + y), c);
}

void mg2_palette_write(mg2_u16 index, mg2_u16 color)
{ mg2_u16 v=reg_read(0x703a);v=(mg2_u16)((v&~0x000c)|((index>>6)&0x000c));reg_write(0x703a,v);reg_write((mg2_u16)(0x7300+(index&255)),color); }
mg2_u16 mg2_palette_read(mg2_u16 index)
{ mg2_u16 v=reg_read(0x703a);v=(mg2_u16)((v&~0x000c)|((index>>6)&0x000c));reg_write(0x703a,v);return reg_read((mg2_u16)(0x7300+(index&255))); }

void mg2_layer_configure(enum mg2_layer l,mg2_u16 gfxlo,mg2_u16 gfxhi,mg2_u16 x,mg2_u16 y,mg2_u16 attr,mg2_u16 ctrl,mg2_u16 tilemap,mg2_u16 attrmap)
{
    static const mg2_u16 xl[4]={0x7010,0x7016,0x7000,0x7008};
    static const mg2_u16 al[4]={0x7012,0x7018,0x7004,0x700c};
    static const mg2_u16 gl[4]={0x7020,0x7021,0x7023,0x7024};
    static const mg2_u16 gh[4]={0x702b,0x702c,0x702e,0x702f};
    mg2_u16 b=xl[(mg2_u16)l&3],a=al[(mg2_u16)l&3];
    reg_write(gl[(mg2_u16)l&3],gfxlo);reg_write(gh[(mg2_u16)l&3],gfxhi);
    reg_write(b,x);reg_write((mg2_u16)(b+1),y);reg_write(a,attr);
    reg_write((mg2_u16)(a+1),ctrl);reg_write((mg2_u16)(a+2),tilemap);reg_write((mg2_u16)(a+3),attrmap);
}
void mg2_layer_scroll(enum mg2_layer l, mg2_s16 x, mg2_s16 y)
{ static const mg2_u16 b[4]={0x7010,0x7016,0x7000,0x7008}; mg2_u16 a=b[(mg2_u16)l&3]; reg_write(a,(mg2_u16)x); reg_write((mg2_u16)(a+1),(mg2_u16)y); }
void mg2_row_scroll_write(mg2_u16 line, mg2_s16 offset)
{ reg_write(0x707e,(mg2_u16)(reg_read(0x707e)&0xfffe));reg_write((mg2_u16)(0x7100+(line&255)),(mg2_u16)offset); }
void mg2_sprite_enable(mg2_u16 count, mg2_u16 direct)
{ reg_write(0x7042,(mg2_u16)(1|(direct?2:0)|((count&255)<<8))); }
void mg2_sprite_write(mg2_u16 n, mg2_u16 tile, mg2_s16 x, mg2_s16 y, mg2_u16 attr)
{ mg2_u16 b=n&255;b<<=2;b=(mg2_u16)(b+0x7400);reg_write(0x707e,(mg2_u16)(reg_read(0x707e)&0xfffe));reg_write(b,tile);reg_write((mg2_u16)(b+1),(mg2_u16)x);reg_write((mg2_u16)(b+2),(mg2_u16)y);reg_write((mg2_u16)(b+3),attr); }
void mg2_sprite_disable(mg2_u16 n) { mg2_sprite_write(n,0,0,0,0); }
void mg2_video_dma_copy(mg2_u16 s, mg2_u16 d, mg2_u16 n)
{ if(!n)return;reg_write(0x7070,s);reg_write(0x7071,d&0x3ff);reg_write(0x7072,(n-1)&0x3ff); }

mg2_u16 mg2_gpio_read(enum mg2_gpio_port p){return reg_read(gpio_base(p));}
mg2_u16 mg2_gpio_latch(enum mg2_gpio_port p){return reg_read((mg2_u16)(gpio_base(p)+1));}
void mg2_gpio_write(enum mg2_gpio_port p, mg2_u16 v){reg_write(gpio_base(p),v);}
void mg2_gpio_set_output(enum mg2_gpio_port p, mg2_u16 m, mg2_u16 ni)
{mg2_u16 b=gpio_base(p),v=reg_read((mg2_u16)(b+3)),inv=(mg2_u16)(0xffff-m);if(ni)v|=m;else v&=inv;reg_write((mg2_u16)(b+3),v);reg_write((mg2_u16)(b+2),(mg2_u16)(reg_read((mg2_u16)(b+2))|m));}
void mg2_gpio_set_input(enum mg2_gpio_port p, mg2_u16 m){mg2_u16 a,v,inv=(mg2_u16)(0xffff-m);a=gpio_base(p);a=(mg2_u16)(a+2);v=reg_read(a);v&=inv;reg_write(a,v);}

mg2_u16 mg2_matrix_scan_row(mg2_u16 row)
{
    static const mg2_u16 masks[5]={0x80,0x40,0x400,0x200,0x20};
    reg_write(0x7870,(mg2_u16)(reg_read(0x7870)&~0x06e0));reg_write(0x7880,(mg2_u16)(reg_read(0x7880)&~4));
    if(row<5){mg2_u16 m=masks[row];reg_write(0x7873,(mg2_u16)(reg_read(0x7873)|m));reg_write(0x7872,(mg2_u16)(reg_read(0x7872)|m));reg_write(0x7870,(mg2_u16)(reg_read(0x7870)|m));}
    else {reg_write(0x7883,(mg2_u16)(reg_read(0x7883)|4));reg_write(0x7882,(mg2_u16)(reg_read(0x7882)|4));reg_write(0x7880,(mg2_u16)(reg_read(0x7880)|4));}
    return (mg2_u16)(((reg_read(0x7868)>>10)&0x3f)|((reg_read(0x7860)>>5)&0x1c0));
}
mg2_u16 mg2_matrix_scan_all(mg2_u16 rows[6])
{mg2_u16 i,any=0;for(i=0;i<6;++i){rows[i]=mg2_matrix_scan_row(i);any|=rows[i];}return any;}

mg2_u16 mg2_adc_read12(mg2_u16 ch)
{reg_write(0x7961,0x8000);reg_write(0x7961,(mg2_u16)((ch&7)|0x40));while(!(reg_read(0x7961)&0x80));reg_write(0x7961,0x8000);return reg_read(0x7962)>>4;}
mg2_u16 mg2_battery_read(void){return mg2_adc_read12(0);}
mg2_u16 mg2_touch_contact(void)
{reg_write(0x7883,(mg2_u16)(reg_read(0x7883)|0x400));reg_write(0x7882,(mg2_u16)(reg_read(0x7882)|0x400));reg_write(0x7880,(mg2_u16)(reg_read(0x7880)|0x400));return (reg_read(0x7880)&0x100)!=0;}
void mg2_dma_copy(mg2_u16 ch,mg2_u16 sl,mg2_u16 sh,mg2_u16 dl,mg2_u16 dh,mg2_u16 cl,mg2_u16 chigh,mg2_u16 f)
{mg2_u16 b=ch&3;b<<=3;b=(mg2_u16)(b+0x7a80);reg_write(b,MG2_DMA_RESET);reg_write((mg2_u16)(b+1),sl);reg_write((mg2_u16)(b+4),sh);reg_write((mg2_u16)(b+2),dl);reg_write((mg2_u16)(b+5),dh);reg_write((mg2_u16)(b+3),cl);reg_write((mg2_u16)(b+6),chigh);reg_write(b,(mg2_u16)(f|1));}
mg2_u16 mg2_dma_status(void){return reg_read(0x7abf)&15;} void mg2_dma_ack(mg2_u16 m){reg_write(0x7abf,m&15);}
mg2_u16 mg2_irq_status1(void){return reg_read(0x78a0);} mg2_u16 mg2_irq_status2(void){return reg_read(0x78a1);}
void mg2_irq_ack1(mg2_u16 m){reg_write(0x78a0,m);} void mg2_irq_ack2(mg2_u16 m){reg_write(0x78a1,m);}
void mg2_irq_set_routing(mg2_u16 a,mg2_u16 b){reg_write(0x78a4,a);reg_write(0x78a5,b);}

void mg2_timer_start(enum mg2_timer t,mg2_u16 p,mg2_u16 a,mg2_u16 b,mg2_u16 irq)
{mg2_u16 x=timer_base(t);reg_write((mg2_u16)(x+2),p);reg_write(x,(mg2_u16)((a&15)|((b&7)<<4)|0x2000|(irq?0x4000:0)));}
void mg2_timer_stop(enum mg2_timer t){reg_write(timer_base(t),0);}
mg2_u16 mg2_timer_count(enum mg2_timer t){return reg_read((mg2_u16)(timer_base(t)+4));}
mg2_u16 mg2_timer_overflowed(enum mg2_timer t){return (reg_read(timer_base(t))&0x8000)!=0;}
void mg2_timer_ack(enum mg2_timer t){reg_write(timer_base(t),0x8000);}
void mg2_timebase_start(mg2_u16 u,mg2_u16 r,mg2_u16 irq){reg_write(timebase_reg(u),(mg2_u16)(0x2000|(irq?0x4000:0)|(r&3)));}
void mg2_timebase_stop(mg2_u16 u){reg_write(timebase_reg(u),0);} void mg2_timebase_ack(mg2_u16 u){reg_write(timebase_reg(u),0x8000);}
void mg2_rtc_scheduler_start(mg2_u16 r,mg2_u16 irq){reg_write(0x7935,0x100);reg_write(0x7936,irq?0x100:0);reg_write(0x7934,(mg2_u16)(0x100|(r&7)));}
void mg2_rtc_scheduler_stop(void){reg_write(0x7934,0);reg_write(0x7936,0);} mg2_u16 mg2_rtc_status(void){return reg_read(0x7935);}
void mg2_rtc_ack(mg2_u16 m){reg_write(0x7935,m);} mg2_u16 mg2_clock_control(void){return reg_read(0x7807);} mg2_u16 mg2_pll_multiplier(void){return reg_read(0x7817)&0x7f;}

void mg2_watchdog_start(mg2_u16 s,mg2_u16 cpu){reg_write(0x780a,(mg2_u16)(0x8000|(cpu?0x4000:0)|(s&7)));} void mg2_watchdog_stop(void){reg_write(0x780a,0);}
void mg2_watchdog_feed(void){reg_write(0x780b,0xa005);} mg2_u16 mg2_reset_cause(void){return reg_read(0x7806);} void mg2_reset_cause_ack(mg2_u16 m){reg_write(0x7806,m);} void mg2_request_sleep(void){reg_write(0x780e,0xa00a);}

void mg2_spi_init(void){reg_write(0x786b,(mg2_u16)(reg_read(0x786b)|0x10));reg_write(0x786a,(mg2_u16)(reg_read(0x786a)|0x10));reg_write(0x7868,(mg2_u16)(reg_read(0x7868)|0x10));}
void mg2_spi_select(mg2_u16 active){mg2_u16 v=reg_read(0x7868);if(active)v&=(mg2_u16)~0x10;else v|=0x10;reg_write(0x7868,v);}
mg2_u8 mg2_spi_transfer(mg2_u8 v){reg_write(0x7942,v);return (mg2_u8)reg_read(0x7944);}
mg2_u8 mg2_spi_read_byte(mg2_u8 a2,mg2_u8 a1,mg2_u8 a0){mg2_u8 v;mg2_spi_select(1);mg2_spi_transfer(3);mg2_spi_transfer(a2);mg2_spi_transfer(a1);mg2_spi_transfer(a0);v=mg2_spi_transfer(0xff);mg2_spi_select(0);return v;}
void mg2_spi_jedec_id(mg2_u8 id[3]){mg2_spi_select(1);mg2_spi_transfer(0x9f);id[0]=mg2_spi_transfer(0xff);id[1]=mg2_spi_transfer(0xff);id[2]=mg2_spi_transfer(0xff);mg2_spi_select(0);}
mg2_u8 mg2_spi_status(void){mg2_u8 v;mg2_spi_select(1);mg2_spi_transfer(5);v=mg2_spi_transfer(0xff);mg2_spi_select(0);return v;}

mg2_u16 mg2_nand_ready(void){return (reg_read(0x7850)&0x8000)!=0;} void mg2_nand_command(mg2_u8 c){reg_write(0x7851,c);}
void mg2_nand_set_address(mg2_u16 c,mg2_u16 p){reg_write(0x7852,c);reg_write(0x7853,p);} mg2_u8 mg2_nand_data_read(void){return (mg2_u8)reg_read(0x7854);} void mg2_nand_data_write(mg2_u8 v){reg_write(0x7854,v);}
void mg2_nand_read_id(mg2_u8 id[2]){mg2_nand_command(0x90);mg2_nand_set_address(0,0);id[0]=mg2_nand_data_read();id[1]=mg2_nand_data_read();}
mg2_u8 mg2_nand_read_byte(mg2_u16 p,mg2_u16 c){mg2_nand_command(0);mg2_nand_set_address(c,p);mg2_nand_command(0x30);return mg2_nand_data_read();}
void mg2_nand_program_byte(mg2_u16 p,mg2_u16 c,mg2_u8 v){mg2_nand_command(0x80);mg2_nand_set_address(c,p);mg2_nand_data_write(v);mg2_nand_command(0x10);}
void mg2_nand_erase_block(mg2_u16 p){mg2_nand_set_address(0,p);mg2_nand_command(0xd0);}

void mg2_audio_fifo_reset(mg2_u16 c){reg_write(c?0x78fa:0x78f2,0x100);} void mg2_audio_fifo_write(mg2_u16 c,mg2_u16 s){reg_write(c?0x78f9:0x78f1,s);}
mg2_u16 mg2_audio_fifo_level(mg2_u16 c){return reg_read(c?0x78fa:0x78f2)&15;} mg2_u16 mg2_audio_fifo_full(mg2_u16 c){return (reg_read(c?0x78fa:0x78f2)&0x8000)!=0;}
void mg2_audio_dac_control(mg2_u16 v){reg_write(0x78fd,v);} void mg2_cache_flush(void){reg_write(0x7819,2);}
void mg2_usb_enable(mg2_u16 e){reg_write(0x7a30,e?1:0);} mg2_u16 mg2_usb_status(void){return reg_read(0x7a3a);} void mg2_usb_ack(mg2_u16 m){reg_write(0x7a3a,m);}
mg2_u16 mg2_sd2_read(mg2_u16 o){return o<=10?reg_read((mg2_u16)(0x79e0+o)):0;} void mg2_sd2_write(mg2_u16 o,mg2_u16 v){if(o<=10)reg_write((mg2_u16)(0x79e0+o),v);}

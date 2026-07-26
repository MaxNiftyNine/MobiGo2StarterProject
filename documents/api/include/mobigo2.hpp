#ifndef MOBIGO2_API_HPP
#define MOBIGO2_API_HPP

#include "mobigo2.h"

namespace mobigo2 {

struct Address {
    mg2_u16 low;
    mg2_u16 high;
    constexpr Address(mg2_u16 lo, mg2_u16 hi) : low(lo), high(hi & 0x3f) {}
};

struct Color {
    static mg2_u16 rgb565(mg2_u16 r, mg2_u16 g, mg2_u16 b) { return mg2_rgb565(r,g,b); }
    static mg2_u16 rgb555(mg2_u16 r, mg2_u16 g, mg2_u16 b) { return mg2_rgb555(r,g,b); }
};

class Framebuffer {
    Address address_;
public:
    explicit constexpr Framebuffer(Address address) : address_(address) {}
    void begin() const { mg2_video_framebuffer_init(address_.low,address_.high); }
    void target() const { mg2_draw_target(address_.low,address_.high); }
    void clear(mg2_u16 color) const { target(); mg2_draw_fill(color); }
    void pixel(mg2_s16 x, mg2_s16 y, mg2_u16 color) const { target();mg2_draw_pixel(x,y,color); }
    mg2_u16 pixel(mg2_s16 x, mg2_s16 y) const { target();return mg2_draw_read_pixel(x,y); }
    void rect(mg2_u16 x,mg2_u16 y,mg2_u16 w,mg2_u16 h,mg2_u16 color) const
    { target();mg2_draw_rect(x,y,w,h,color); }
};

class Gpio {
    mg2_gpio_port port_;
public:
    explicit constexpr Gpio(mg2_gpio_port port) : port_(port) {}
    mg2_u16 read() const { return mg2_gpio_read(port_); }
    mg2_u16 latch() const { return mg2_gpio_latch(port_); }
    void write(mg2_u16 value) const { mg2_gpio_write(port_,value); }
    void output(mg2_u16 mask,bool normal=true) const { mg2_gpio_set_output(port_,mask,normal?1:0); }
    void input(mg2_u16 mask) const { mg2_gpio_set_input(port_,mask); }
};

inline void initialize() { mg2_init(); }
inline mg2_u16 battery() { return mg2_battery_read(); }
inline bool touching() { return mg2_touch_contact()!=0; }

} // namespace mobigo2
#endif

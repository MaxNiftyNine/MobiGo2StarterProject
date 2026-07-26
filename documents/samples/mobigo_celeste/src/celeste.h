#ifndef CELESTE_H_
#define CELESTE_H_

typedef int Celeste_P8_bool_t;

extern void Celeste_P8_set_rndseed(unsigned long seed);
extern void Celeste_P8_hard_reset(void);
extern void Celeste_P8_init(void);
extern void Celeste_P8_update(void);
extern void Celeste_P8_draw(void);

#endif

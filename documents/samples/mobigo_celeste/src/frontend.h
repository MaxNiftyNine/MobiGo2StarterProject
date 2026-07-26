#ifndef CELESTE_MOBIGO_FRONTEND_H
#define CELESTE_MOBIGO_FRONTEND_H

void mg_music(int track, int fade, int mask);
void mg_spr(int sprite, int x, int y, int cols, int rows, int flipx, int flipy);
int mg_btn(int button);
void mg_sfx(int id);
void mg_pal(int source, int destination);
void mg_pal_reset(void);
void mg_circfill(int x, int y, int radius, int color);
void mg_rectfill(int x0, int y0, int x1, int y1, int color);
void mg_print(const char *text, int x, int y, int color);
void mg_line(int x0, int y0, int x1, int y1, int color);
int mg_mget(int x, int y);
int mg_fget(int tile, int flag);
void mg_camera(int x, int y);
void mg_map(int mx, int my, int tx, int ty, int mw, int mh, int mask);

#endif

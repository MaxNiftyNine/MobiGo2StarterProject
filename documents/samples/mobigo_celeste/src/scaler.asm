// Hand-tuned u'nSP RGB565 row expander.
//
// The C compiler models pointers as 32-bit far pointers and spills them for
// nearly every pixel store. All render scratch and the RGB table are in
// segment zero, so this routine keeps the source, destination, and packed
// pixels in registers and uses one 16-bit loop counter.
//
// void expand_row_fast(int source_y, unsigned short row_address);

.code
.public _expand_row_fast

_expand_row_fast: .proc
     push BP to [SP]
     SP = SP - 1
     BP = SP + 1

     R4 = [BP + 4]
     R1 = R4 lsl 4
     R1 = R1 lsl 1
     R1 = R1 + 20480
     R2 = [BP + 5]
     R2 = R2 + 40
     R4 = 16
     [BP + 0] = R4
     DS = 0

L_expand_group:
     R3 = [R1]
     R1 = R1 + 1

     R4 = R3 & 15
     R4 = R4 + 24800
     R4 = [R4]
     [R2] = R4
     R2 = R2 + 1
     [R2] = R4
     R2 = R2 + 1
     R3 = R3 lsr 4

     R4 = R3 & 15
     R4 = R4 + 24800
     R4 = [R4]
     [R2] = R4
     R2 = R2 + 1
     [R2] = R4
     R2 = R2 + 1
     R3 = R3 lsr 4

     R4 = R3 & 15
     R4 = R4 + 24800
     R4 = [R4]
     [R2] = R4
     R2 = R2 + 1
     [R2] = R4
     R2 = R2 + 1
     R3 = R3 lsr 4

     R4 = R3 & 15
     R4 = R4 + 24800
     R4 = [R4]
     [R2] = R4
     R2 = R2 + 1
     [R2] = R4
     R2 = R2 + 1

     R3 = [R1]
     R1 = R1 + 1

     R4 = R3 & 15
     R4 = R4 + 24800
     R4 = [R4]
     [R2] = R4
     R2 = R2 + 1
     [R2] = R4
     R2 = R2 + 1
     R3 = R3 lsr 4

     R4 = R3 & 15
     R4 = R4 + 24800
     R4 = [R4]
     [R2] = R4
     R2 = R2 + 1
     [R2] = R4
     R2 = R2 + 1
     R3 = R3 lsr 4

     R4 = R3 & 15
     R4 = R4 + 24800
     R4 = [R4]
     [R2] = R4
     R2 = R2 + 1
     [R2] = R4
     R2 = R2 + 1
     R3 = R3 lsr 4

     R4 = R3 & 15
     R4 = R4 + 24800
     R4 = [R4]
     [R2] = R4
     R2 = R2 + 1

     R4 = [BP + 0]
     R4 = R4 - 1
     [BP + 0] = R4
     cmp R4, 0
     je L_expand_done
     goto L_expand_group

L_expand_done:
     SP = SP + 1
     pop BP, PC from [SP]
.endp

	.globl _mg2_asm_store_far
	.globl _mg2_asm_load_far

_mg2_asm_store_far:
	PUSH BP, BP, (SP)
	ADD BP, SP, 1
	LD R1, (BP+3)
	LD R2, (BP+4)
	LD R3, (BP+5)
	.2byte 0xf02b
	.2byte 0xd2e2
	LD R3, 0
	.2byte 0xf02b
	POP BP, BP, (SP)
	RETF

_mg2_asm_load_far:
	PUSH BP, BP, (SP)
	ADD BP, SP, 1
	LD R2, (BP+3)
	LD R3, (BP+4)
	.2byte 0xf02b
	.2byte 0x92e2
	LD R3, 0
	.2byte 0xf02b
	POP BP, BP, (SP)
	RETF

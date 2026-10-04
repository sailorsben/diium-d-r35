
build/launcher-clock/vrtemu.original:     file format elf32-littlearm


Disassembly of section .init:

Disassembly of section .plt:

Disassembly of section .text:

000a2f0c <joystick_input>:
   a2f0c:	e52de004 	push	{lr}		@ (str lr, [sp, #-4]!)
   a2f10:	e3500003 	cmp	r0, #3
   a2f14:	e59fe0a0 	ldr	lr, [pc, #160]	@ a2fbc <joystick_input+0xb0>
   a2f18:	e24dd00c 	sub	sp, sp, #12
   a2f1c:	83a00000 	movhi	r0, #0
   a2f20:	e08fe00e 	add	lr, pc, lr
   a2f24:	8a00000c 	bhi	a2f5c <joystick_input+0x50>
   a2f28:	e59fc090 	ldr	ip, [pc, #144]	@ a2fc0 <joystick_input+0xb4>
   a2f2c:	e3510005 	cmp	r1, #5
   a2f30:	03520000 	cmpeq	r2, #0
   a2f34:	e79e200c 	ldr	r2, [lr, ip]
   a2f38:	e7922100 	ldr	r2, [r2, r0, lsl #2]
   a2f3c:	0a000008 	beq	a2f64 <joystick_input+0x58>
   a2f40:	e59f107c 	ldr	r1, [pc, #124]	@ a2fc4 <joystick_input+0xb8>
   a2f44:	e0833200 	add	r3, r3, r0, lsl #4
   a2f48:	e79e1001 	ldr	r1, [lr, r1]
   a2f4c:	e7913103 	ldr	r3, [r1, r3, lsl #2]
   a2f50:	e1120003 	tst	r2, r3
   a2f54:	13a00001 	movne	r0, #1
   a2f58:	03a00000 	moveq	r0, #0
   a2f5c:	e28dd00c 	add	sp, sp, #12
   a2f60:	e49df004 	pop	{pc}		@ (ldr pc, [sp], #4)
   a2f64:	e3a01081 	mov	r1, #129	@ 0x81
   a2f68:	e3120010 	tst	r2, #16
   a2f6c:	e58d1000 	str	r1, [sp]
   a2f70:	13081001 	movwne	r1, #32769	@ 0x8001
   a2f74:	134f1fff 	movtne	r1, #65535	@ 0xffff
   a2f78:	e3120040 	tst	r2, #64	@ 0x40
   a2f7c:	e58d1004 	str	r1, [sp, #4]
   a2f80:	13071fff 	movwne	r1, #32767	@ 0x7fff
   a2f84:	158d1004 	strne	r1, [sp, #4]
   a2f88:	e3120080 	tst	r2, #128	@ 0x80
   a2f8c:	13081001 	movwne	r1, #32769	@ 0x8001
   a2f90:	e2033001 	and	r3, r3, #1
   a2f94:	134f1fff 	movtne	r1, #65535	@ 0xffff
   a2f98:	158d1000 	strne	r1, [sp]
   a2f9c:	e3120020 	tst	r2, #32
   a2fa0:	13072fff 	movwne	r2, #32767	@ 0x7fff
   a2fa4:	158d2000 	strne	r2, [sp]
   a2fa8:	e28d2008 	add	r2, sp, #8
   a2fac:	e0823103 	add	r3, r2, r3, lsl #2
   a2fb0:	e5130008 	ldr	r0, [r3, #-8]
   a2fb4:	e28dd00c 	add	sp, sp, #12
   a2fb8:	e49df004 	pop	{pc}		@ (ldr pc, [sp], #4)
   a2fbc:	000f60d8 	.word	0x000f60d8
   a2fc0:	00000474 	.word	0x00000474
   a2fc4:	000002b0 	.word	0x000002b0

Disassembly of section .fini:

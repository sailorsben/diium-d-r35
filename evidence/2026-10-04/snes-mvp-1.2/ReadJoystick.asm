
build/launcher-clock/vrtemu.original:     file format elf32-littlearm


Disassembly of section .init:

Disassembly of section .plt:

Disassembly of section .text:

0001599c <ReadJoystick>:
   1599c:	e92d41f0 	push	{r4, r5, r6, r7, r8, lr}
   159a0:	e3a00c02 	mov	r0, #512	@ 0x200
   159a4:	e59f821c 	ldr	r8, [pc, #540]	@ 15bc8 <ReadJoystick+0x22c>
   159a8:	ebffff86 	bl	157c8 <gpio_read_io>
   159ac:	e1a03000 	mov	r3, r0
   159b0:	e3000201 	movw	r0, #513	@ 0x201
   159b4:	e08f8008 	add	r8, pc, r8
   159b8:	e3530000 	cmp	r3, #0
   159bc:	03a04010 	moveq	r4, #16
   159c0:	13a04000 	movne	r4, #0
   159c4:	ebffff7f 	bl	157c8 <gpio_read_io>
   159c8:	e3500000 	cmp	r0, #0
   159cc:	e3000202 	movw	r0, #514	@ 0x202
   159d0:	03844040 	orreq	r4, r4, #64	@ 0x40
   159d4:	ebffff7b 	bl	157c8 <gpio_read_io>
   159d8:	e3500000 	cmp	r0, #0
   159dc:	e3000203 	movw	r0, #515	@ 0x203
   159e0:	03844080 	orreq	r4, r4, #128	@ 0x80
   159e4:	ebffff77 	bl	157c8 <gpio_read_io>
   159e8:	e3500000 	cmp	r0, #0
   159ec:	e3a00f81 	mov	r0, #516	@ 0x204
   159f0:	03844020 	orreq	r4, r4, #32
   159f4:	ebffff73 	bl	157c8 <gpio_read_io>
   159f8:	e3500000 	cmp	r0, #0
   159fc:	e3000205 	movw	r0, #517	@ 0x205
   15a00:	03844a02 	orreq	r4, r4, #8192	@ 0x2000
   15a04:	ebffff6f 	bl	157c8 <gpio_read_io>
   15a08:	e3500000 	cmp	r0, #0
   15a0c:	e300030a 	movw	r0, #778	@ 0x30a
   15a10:	03844901 	orreq	r4, r4, #16384	@ 0x4000
   15a14:	ebffff6b 	bl	157c8 <gpio_read_io>
   15a18:	e3500000 	cmp	r0, #0
   15a1c:	e3a00f82 	mov	r0, #520	@ 0x208
   15a20:	03844b01 	orreq	r4, r4, #1024	@ 0x400
   15a24:	ebffff67 	bl	157c8 <gpio_read_io>
   15a28:	e3500000 	cmp	r0, #0
   15a2c:	e3a00fc3 	mov	r0, #780	@ 0x30c
   15a30:	03844b02 	orreq	r4, r4, #2048	@ 0x800
   15a34:	ebffff63 	bl	157c8 <gpio_read_io>
   15a38:	e3500000 	cmp	r0, #0
   15a3c:	e300030f 	movw	r0, #783	@ 0x30f
   15a40:	03844008 	orreq	r4, r4, #8
   15a44:	ebffff5f 	bl	157c8 <gpio_read_io>
   15a48:	e3500000 	cmp	r0, #0
   15a4c:	e300030b 	movw	r0, #779	@ 0x30b
   15a50:	03844001 	orreq	r4, r4, #1
   15a54:	ebffff5b 	bl	157c8 <gpio_read_io>
   15a58:	e3500000 	cmp	r0, #0
   15a5c:	e300030d 	movw	r0, #781	@ 0x30d
   15a60:	03844902 	orreq	r4, r4, #32768	@ 0x8000
   15a64:	ebffff57 	bl	157c8 <gpio_read_io>
   15a68:	e3500000 	cmp	r0, #0
   15a6c:	e3000206 	movw	r0, #518	@ 0x206
   15a70:	03844a01 	orreq	r4, r4, #4096	@ 0x1000
   15a74:	ebffff53 	bl	157c8 <gpio_read_io>
   15a78:	e3500000 	cmp	r0, #0
   15a7c:	e3000207 	movw	r0, #519	@ 0x207
   15a80:	03844009 	orreq	r4, r4, #9
   15a84:	ebffff4f 	bl	157c8 <gpio_read_io>
   15a88:	e3500000 	cmp	r0, #0
   15a8c:	e300030e 	movw	r0, #782	@ 0x30e
   15a90:	03844c01 	orreq	r4, r4, #256	@ 0x100
   15a94:	ebffff4b 	bl	157c8 <gpio_read_io>
   15a98:	e3500000 	cmp	r0, #0
   15a9c:	e3a00000 	mov	r0, #0
   15aa0:	03844c02 	orreq	r4, r4, #512	@ 0x200
   15aa4:	ebfffe34 	bl	1537c <ReadUSBJoy>
   15aa8:	e1a03000 	mov	r3, r0
   15aac:	e3a00001 	mov	r0, #1
   15ab0:	e1844003 	orr	r4, r4, r3
   15ab4:	ebfffe30 	bl	1537c <ReadUSBJoy>
   15ab8:	e1a07000 	mov	r7, r0
   15abc:	e3a00002 	mov	r0, #2
   15ac0:	ebfffe2d 	bl	1537c <ReadUSBJoy>
   15ac4:	e1a06000 	mov	r6, r0
   15ac8:	e3a00003 	mov	r0, #3
   15acc:	ebfffe2a 	bl	1537c <ReadUSBJoy>
   15ad0:	e1a05000 	mov	r5, r0
   15ad4:	e3000209 	movw	r0, #521	@ 0x209
   15ad8:	ebffff3a 	bl	157c8 <gpio_read_io>
   15adc:	e3500000 	cmp	r0, #0
   15ae0:	e300020a 	movw	r0, #522	@ 0x20a
   15ae4:	13c44202 	bicne	r4, r4, #536870912	@ 0x20000000
   15ae8:	03844202 	orreq	r4, r4, #536870912	@ 0x20000000
   15aec:	ebffff35 	bl	157c8 <gpio_read_io>
   15af0:	e59f30d4 	ldr	r3, [pc, #212]	@ 15bcc <ReadJoystick+0x230>
   15af4:	e3500000 	cmp	r0, #0
   15af8:	13c44201 	bicne	r4, r4, #268435456	@ 0x10000000
   15afc:	03844201 	orreq	r4, r4, #268435456	@ 0x10000000
   15b00:	e7983003 	ldr	r3, [r8, r3]
   15b04:	e5933000 	ldr	r3, [r3]
   15b08:	e3530000 	cmp	r3, #0
   15b0c:	0a000027 	beq	15bb0 <ReadJoystick+0x214>
   15b10:	e3c430f0 	bic	r3, r4, #240	@ 0xf0
   15b14:	e3140010 	tst	r4, #16
   15b18:	13833080 	orrne	r3, r3, #128	@ 0x80
   15b1c:	e3140040 	tst	r4, #64	@ 0x40
   15b20:	13833020 	orrne	r3, r3, #32
   15b24:	e3140080 	tst	r4, #128	@ 0x80
   15b28:	13833040 	orrne	r3, r3, #64	@ 0x40
   15b2c:	e3140020 	tst	r4, #32
   15b30:	13834010 	orrne	r4, r3, #16
   15b34:	01a04003 	moveq	r4, r3
   15b38:	e3c730f0 	bic	r3, r7, #240	@ 0xf0
   15b3c:	e3170010 	tst	r7, #16
   15b40:	13833080 	orrne	r3, r3, #128	@ 0x80
   15b44:	e3170040 	tst	r7, #64	@ 0x40
   15b48:	13833020 	orrne	r3, r3, #32
   15b4c:	e3170080 	tst	r7, #128	@ 0x80
   15b50:	13833040 	orrne	r3, r3, #64	@ 0x40
   15b54:	e3170020 	tst	r7, #32
   15b58:	13837010 	orrne	r7, r3, #16
   15b5c:	01a07003 	moveq	r7, r3
   15b60:	e3c630f0 	bic	r3, r6, #240	@ 0xf0
   15b64:	e3160010 	tst	r6, #16
   15b68:	13833080 	orrne	r3, r3, #128	@ 0x80
   15b6c:	e3160040 	tst	r6, #64	@ 0x40
   15b70:	13833020 	orrne	r3, r3, #32
   15b74:	e3160080 	tst	r6, #128	@ 0x80
   15b78:	13833040 	orrne	r3, r3, #64	@ 0x40
   15b7c:	e3160020 	tst	r6, #32
   15b80:	13836010 	orrne	r6, r3, #16
   15b84:	01a06003 	moveq	r6, r3
   15b88:	e3c530f0 	bic	r3, r5, #240	@ 0xf0
   15b8c:	e3150010 	tst	r5, #16
   15b90:	13833080 	orrne	r3, r3, #128	@ 0x80
   15b94:	e3150040 	tst	r5, #64	@ 0x40
   15b98:	13833020 	orrne	r3, r3, #32
   15b9c:	e3150080 	tst	r5, #128	@ 0x80
   15ba0:	13833040 	orrne	r3, r3, #64	@ 0x40
   15ba4:	e3150020 	tst	r5, #32
   15ba8:	13835010 	orrne	r5, r3, #16
   15bac:	01a05003 	moveq	r5, r3
   15bb0:	e59f3018 	ldr	r3, [pc, #24]	@ 15bd0 <ReadJoystick+0x234>
   15bb4:	e7983003 	ldr	r3, [r8, r3]
   15bb8:	e8830090 	stm	r3, {r4, r7}
   15bbc:	e5836008 	str	r6, [r3, #8]
   15bc0:	e583500c 	str	r5, [r3, #12]
   15bc4:	e8bd81f0 	pop	{r4, r5, r6, r7, r8, pc}
   15bc8:	00183644 	.word	0x00183644
   15bcc:	000001e0 	.word	0x000001e0
   15bd0:	00000244 	.word	0x00000244

Disassembly of section .fini:

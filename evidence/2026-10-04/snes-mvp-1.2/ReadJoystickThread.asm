
build/launcher-clock/vrtemu.original:     file format elf32-littlearm


Disassembly of section .init:

Disassembly of section .plt:

Disassembly of section .text:

00015e50 <ReadJoystickThread>:
   15e50:	e92d4ff0 	push	{r4, r5, r6, r7, r8, r9, sl, fp, lr}
   15e54:	e3011002 	movw	r1, #4098	@ 0x1002
   15e58:	e59f0294 	ldr	r0, [pc, #660]	@ 160f4 <ReadJoystickThread+0x2a4>
   15e5c:	e24dd014 	sub	sp, sp, #20
   15e60:	e59f4290 	ldr	r4, [pc, #656]	@ 160f8 <ReadJoystickThread+0x2a8>
   15e64:	e3401010 	movt	r1, #16
   15e68:	e08f4004 	add	r4, pc, r4
   15e6c:	e08f0000 	add	r0, pc, r0
   15e70:	e59f9284 	ldr	r9, [pc, #644]	@ 160fc <ReadJoystickThread+0x2ac>
   15e74:	ebffefc9 	bl	11da0 <open@plt>
   15e78:	e59fe280 	ldr	lr, [pc, #640]	@ 16100 <ReadJoystickThread+0x2b0>
   15e7c:	e1a03004 	mov	r3, r4
   15e80:	e59f727c 	ldr	r7, [pc, #636]	@ 16104 <ReadJoystickThread+0x2b4>
   15e84:	e793e00e 	ldr	lr, [r3, lr]
   15e88:	e59f6278 	ldr	r6, [pc, #632]	@ 16108 <ReadJoystickThread+0x2b8>
   15e8c:	e59f8278 	ldr	r8, [pc, #632]	@ 1610c <ReadJoystickThread+0x2bc>
   15e90:	e59f5278 	ldr	r5, [pc, #632]	@ 16110 <ReadJoystickThread+0x2c0>
   15e94:	e59f4278 	ldr	r4, [pc, #632]	@ 16114 <ReadJoystickThread+0x2c4>
   15e98:	e59fc278 	ldr	ip, [pc, #632]	@ 16118 <ReadJoystickThread+0x2c8>
   15e9c:	e793a009 	ldr	sl, [r3, r9]
   15ea0:	e793b007 	ldr	fp, [r3, r7]
   15ea4:	e7936006 	ldr	r6, [r3, r6]
   15ea8:	e7938008 	ldr	r8, [r3, r8]
   15eac:	e7935005 	ldr	r5, [r3, r5]
   15eb0:	e7934004 	ldr	r4, [r3, r4]
   15eb4:	e59f0260 	ldr	r0, [pc, #608]	@ 1611c <ReadJoystickThread+0x2cc>
   15eb8:	e58de00c 	str	lr, [sp, #12]
   15ebc:	e793c00c 	ldr	ip, [r3, ip]
   15ec0:	e59f1258 	ldr	r1, [pc, #600]	@ 16120 <ReadJoystickThread+0x2d0>
   15ec4:	e58dc004 	str	ip, [sp, #4]
   15ec8:	e59f2254 	ldr	r2, [pc, #596]	@ 16124 <ReadJoystickThread+0x2d4>
   15ecc:	e7930000 	ldr	r0, [r3, r0]
   15ed0:	e58d0008 	str	r0, [sp, #8]
   15ed4:	e7937001 	ldr	r7, [r3, r1]
   15ed8:	e7939002 	ldr	r9, [r3, r2]
   15edc:	ea000031 	b	15fa8 <ReadJoystickThread+0x158>
   15ee0:	e59bc000 	ldr	ip, [fp]
   15ee4:	e5842004 	str	r2, [r4, #4]
   15ee8:	e3a02000 	mov	r2, #0
   15eec:	e5843000 	str	r3, [r4]
   15ef0:	e35c0000 	cmp	ip, #0
   15ef4:	e5841008 	str	r1, [r4, #8]
   15ef8:	e584000c 	str	r0, [r4, #12]
   15efc:	e58a2000 	str	r2, [sl]
   15f00:	0a000054 	beq	16058 <ReadJoystickThread+0x208>
   15f04:	e3130201 	tst	r3, #268435456	@ 0x10000000
   15f08:	0a000014 	beq	15f60 <ReadJoystickThread+0x110>
   15f0c:	e5970000 	ldr	r0, [r7]
   15f10:	e3500000 	cmp	r0, #0
   15f14:	0a00000c 	beq	15f4c <ReadJoystickThread+0xfc>
   15f18:	e2400001 	sub	r0, r0, #1
   15f1c:	e3500009 	cmp	r0, #9
   15f20:	d5870000 	strle	r0, [r7]
   15f24:	c3a03009 	movgt	r3, #9
   15f28:	c5873000 	strgt	r3, [r7]
   15f2c:	c1a00003 	movgt	r0, r3
   15f30:	e59d3004 	ldr	r3, [sp, #4]
   15f34:	e5830000 	str	r0, [r3]
   15f38:	ebfff193 	bl	1258c <SetSoundVol>
   15f3c:	e5970000 	ldr	r0, [r7]
   15f40:	e3a03001 	mov	r3, #1
   15f44:	e5883000 	str	r3, [r8]
   15f48:	ebfff1bb 	bl	1263c <SPISaveVOL>
   15f4c:	e3a00001 	mov	r0, #1
   15f50:	e5860000 	str	r0, [r6]
   15f54:	e5880000 	str	r0, [r8]
   15f58:	eb020255 	bl	968b4 <mui_Setflash>
   15f5c:	e5953000 	ldr	r3, [r5]
   15f60:	e3130202 	tst	r3, #536870912	@ 0x20000000
   15f64:	0a000008 	beq	15f8c <ReadJoystickThread+0x13c>
   15f68:	e5970000 	ldr	r0, [r7]
   15f6c:	e3500008 	cmp	r0, #8
   15f70:	c3a03009 	movgt	r3, #9
   15f74:	c5873000 	strgt	r3, [r7]
   15f78:	da000044 	ble	16090 <ReadJoystickThread+0x240>
   15f7c:	e3a00001 	mov	r0, #1
   15f80:	e5860000 	str	r0, [r6]
   15f84:	e5880000 	str	r0, [r8]
   15f88:	eb020249 	bl	968b4 <mui_Setflash>
   15f8c:	ebffff79 	bl	15d78 <processvblank>
   15f90:	e5993000 	ldr	r3, [r9]
   15f94:	e3530000 	cmp	r3, #0
   15f98:	0a000000 	beq	15fa0 <ReadJoystickThread+0x150>
   15f9c:	ebfff80c 	bl	13fd4 <xintiao>
   15fa0:	e3030a98 	movw	r0, #15000	@ 0x3a98
   15fa4:	ebffefd7 	bl	11f08 <usleep@plt>
   15fa8:	ebfffe7b 	bl	1599c <ReadJoystick>
   15fac:	e5963000 	ldr	r3, [r6]
   15fb0:	e3530000 	cmp	r3, #0
   15fb4:	0a000003 	beq	15fc8 <ReadJoystickThread+0x178>
   15fb8:	e2833001 	add	r3, r3, #1
   15fbc:	e353003c 	cmp	r3, #60	@ 0x3c
   15fc0:	d5863000 	strle	r3, [r6]
   15fc4:	ca00003b 	bgt	160b8 <ReadJoystickThread+0x268>
   15fc8:	e5941000 	ldr	r1, [r4]
   15fcc:	e5953000 	ldr	r3, [r5]
   15fd0:	e5952004 	ldr	r2, [r5, #4]
   15fd4:	e1510003 	cmp	r1, r3
   15fd8:	e595000c 	ldr	r0, [r5, #12]
   15fdc:	e5951008 	ldr	r1, [r5, #8]
   15fe0:	1affffbe 	bne	15ee0 <ReadJoystickThread+0x90>
   15fe4:	e594c004 	ldr	ip, [r4, #4]
   15fe8:	e15c0002 	cmp	ip, r2
   15fec:	1affffbb 	bne	15ee0 <ReadJoystickThread+0x90>
   15ff0:	e594c008 	ldr	ip, [r4, #8]
   15ff4:	e15c0001 	cmp	ip, r1
   15ff8:	1affffb8 	bne	15ee0 <ReadJoystickThread+0x90>
   15ffc:	e594c00c 	ldr	ip, [r4, #12]
   16000:	e15c0000 	cmp	ip, r0
   16004:	1affffb5 	bne	15ee0 <ReadJoystickThread+0x90>
   16008:	e59a3000 	ldr	r3, [sl]
   1600c:	e3032a98 	movw	r2, #15000	@ 0x3a98
   16010:	e2833001 	add	r3, r3, #1
   16014:	e1530002 	cmp	r3, r2
   16018:	e58a3000 	str	r3, [sl]
   1601c:	daffffda 	ble	15f8c <ReadJoystickThread+0x13c>
   16020:	e59b3000 	ldr	r3, [fp]
   16024:	e3530000 	cmp	r3, #0
   16028:	0affffd7 	beq	15f8c <ReadJoystickThread+0x13c>
   1602c:	e3a00000 	mov	r0, #0
   16030:	ebffff73 	bl	15e04 <LCM_LED>
   16034:	e3a00000 	mov	r0, #0
   16038:	ebfffb4d 	bl	14d74 <SetLEDVol>
   1603c:	e59d3008 	ldr	r3, [sp, #8]
   16040:	e5933000 	ldr	r3, [r3]
   16044:	e3530000 	cmp	r3, #0
   16048:	1a000025 	bne	160e4 <ReadJoystickThread+0x294>
   1604c:	e3a00000 	mov	r0, #0
   16050:	ebfff14d 	bl	1258c <SetSoundVol>
   16054:	eaffffcc 	b	15f8c <ReadJoystickThread+0x13c>
   16058:	e3a00001 	mov	r0, #1
   1605c:	ebffff68 	bl	15e04 <LCM_LED>
   16060:	e59d300c 	ldr	r3, [sp, #12]
   16064:	e5930000 	ldr	r0, [r3]
   16068:	ebfffb41 	bl	14d74 <SetLEDVol>
   1606c:	e59d3004 	ldr	r3, [sp, #4]
   16070:	e5930000 	ldr	r0, [r3]
   16074:	ebfff144 	bl	1258c <SetSoundVol>
   16078:	e59d3008 	ldr	r3, [sp, #8]
   1607c:	e5933000 	ldr	r3, [r3]
   16080:	e3530000 	cmp	r3, #0
   16084:	1a000012 	bne	160d4 <ReadJoystickThread+0x284>
   16088:	e5953000 	ldr	r3, [r5]
   1608c:	eaffff9c 	b	15f04 <ReadJoystickThread+0xb4>
   16090:	e59d3004 	ldr	r3, [sp, #4]
   16094:	e2800001 	add	r0, r0, #1
   16098:	e5870000 	str	r0, [r7]
   1609c:	e5830000 	str	r0, [r3]
   160a0:	ebfff139 	bl	1258c <SetSoundVol>
   160a4:	e5970000 	ldr	r0, [r7]
   160a8:	e3a03001 	mov	r3, #1
   160ac:	e5883000 	str	r3, [r8]
   160b0:	ebfff161 	bl	1263c <SPISaveVOL>
   160b4:	eaffffb0 	b	15f7c <ReadJoystickThread+0x12c>
   160b8:	e3a02000 	mov	r2, #0
   160bc:	e3a03002 	mov	r3, #2
   160c0:	e5862000 	str	r2, [r6]
   160c4:	e3a00001 	mov	r0, #1
   160c8:	e5883000 	str	r3, [r8]
   160cc:	eb0201f8 	bl	968b4 <mui_Setflash>
   160d0:	eaffffae 	b	15f90 <ReadJoystickThread+0x140>
   160d4:	e3a01001 	mov	r1, #1
   160d8:	e300040b 	movw	r0, #1035	@ 0x40b
   160dc:	ebfffde6 	bl	1587c <gpio_write_io>
   160e0:	eaffffe8 	b	16088 <ReadJoystickThread+0x238>
   160e4:	e3a01000 	mov	r1, #0
   160e8:	e300040b 	movw	r0, #1035	@ 0x40b
   160ec:	ebfffde2 	bl	1587c <gpio_write_io>
   160f0:	eaffffd5 	b	1604c <ReadJoystickThread+0x1fc>
   160f4:	0014ffa8 	.word	0x0014ffa8
   160f8:	00183190 	.word	0x00183190
   160fc:	000001e4 	.word	0x000001e4
   16100:	0000040c 	.word	0x0000040c
   16104:	00000498 	.word	0x00000498
   16108:	000002c0 	.word	0x000002c0
   1610c:	00000510 	.word	0x00000510
   16110:	00000244 	.word	0x00000244
   16114:	00000454 	.word	0x00000454
   16118:	0000035c 	.word	0x0000035c
   1611c:	000003f4 	.word	0x000003f4
   16120:	0000023c 	.word	0x0000023c
   16124:	000004c0 	.word	0x000004c0

Disassembly of section .fini:

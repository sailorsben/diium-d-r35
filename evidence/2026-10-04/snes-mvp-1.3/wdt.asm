
device-evidence/snes-mvp-return-20261004T222804Z/snes-mvp/platform-wdt:     file format elf32-littlearm


Disassembly of section .init:

00010344 <_init>:
   10344:	e92d4008 	push	{r3, lr}
   10348:	eb00005d 	bl	104c4 <call_weak_fn>
   1034c:	e8bd8008 	pop	{r3, pc}

Disassembly of section .plt:

00010350 <.plt>:
   10350:	e52de004 	push	{lr}		@ (str lr, [sp, #-4]!)
   10354:	e59fe004 	ldr	lr, [pc, #4]	@ 10360 <.plt+0x10>
   10358:	e08fe00e 	add	lr, pc, lr
   1035c:	e5bef008 	ldr	pc, [lr, #8]!
   10360:	00010ca0 	.word	0x00010ca0

00010364 <ioctl@plt>:
   10364:	e28fc600 	add	ip, pc, #0, 12
   10368:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   1036c:	e5bcfca0 	ldr	pc, [ip, #3232]!	@ 0xca0

00010370 <usleep@plt>:
   10370:	e28fc600 	add	ip, pc, #0, 12
   10374:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   10378:	e5bcfc98 	ldr	pc, [ip, #3224]!	@ 0xc98

0001037c <puts@plt>:
   1037c:	e28fc600 	add	ip, pc, #0, 12
   10380:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   10384:	e5bcfc90 	ldr	pc, [ip, #3216]!	@ 0xc90

00010388 <__libc_start_main@plt>:
   10388:	e28fc600 	add	ip, pc, #0, 12
   1038c:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   10390:	e5bcfc88 	ldr	pc, [ip, #3208]!	@ 0xc88

00010394 <__gmon_start__@plt>:
   10394:	e28fc600 	add	ip, pc, #0, 12
   10398:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   1039c:	e5bcfc80 	ldr	pc, [ip, #3200]!	@ 0xc80

000103a0 <open@plt>:
   103a0:	e28fc600 	add	ip, pc, #0, 12
   103a4:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   103a8:	e5bcfc78 	ldr	pc, [ip, #3192]!	@ 0xc78

000103ac <abort@plt>:
   103ac:	e28fc600 	add	ip, pc, #0, 12
   103b0:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   103b4:	e5bcfc70 	ldr	pc, [ip, #3184]!	@ 0xc70

Disassembly of section .text:

000103b8 <main>:
   103b8:	e59f00bc 	ldr	r0, [pc, #188]	@ 1047c <main+0xc4>
   103bc:	e92d40f0 	push	{r4, r5, r6, r7, lr}
   103c0:	e3a05000 	mov	r5, #0
   103c4:	e08f0000 	add	r0, pc, r0
   103c8:	e24dd00c 	sub	sp, sp, #12
   103cc:	e1a01005 	mov	r1, r5
   103d0:	e58d5004 	str	r5, [sp, #4]
   103d4:	ebfffff1 	bl	103a0 <open@plt>
   103d8:	e2504000 	subs	r4, r0, #0
   103dc:	ba000020 	blt	10464 <main+0xac>
   103e0:	e3051706 	movw	r1, #22278	@ 0x5706
   103e4:	e1a02005 	mov	r2, r5
   103e8:	e3441004 	movt	r1, #16388	@ 0x4004
   103ec:	e30a6120 	movw	r6, #41248	@ 0xa120
   103f0:	e3406007 	movt	r6, #7
   103f4:	ebffffda 	bl	10364 <ioctl@plt>
   103f8:	e3051704 	movw	r1, #22276	@ 0x5704
   103fc:	e3a02001 	mov	r2, #1
   10400:	e3441004 	movt	r1, #16388	@ 0x4004
   10404:	e1a00004 	mov	r0, r4
   10408:	e3055705 	movw	r5, #22277	@ 0x5705
   1040c:	ebffffd4 	bl	10364 <ioctl@plt>
   10410:	e3485004 	movt	r5, #32772	@ 0x8004
   10414:	e3051701 	movw	r1, #22273	@ 0x5701
   10418:	e3441004 	movt	r1, #16388	@ 0x4004
   1041c:	e3a02001 	mov	r2, #1
   10420:	e1a00004 	mov	r0, r4
   10424:	e28d7004 	add	r7, sp, #4
   10428:	ebffffcd 	bl	10364 <ioctl@plt>
   1042c:	e59f004c 	ldr	r0, [pc, #76]	@ 10480 <main+0xc8>
   10430:	e08f0000 	add	r0, pc, r0
   10434:	ebffffd0 	bl	1037c <puts@plt>
   10438:	e1a00006 	mov	r0, r6
   1043c:	ebffffcb 	bl	10370 <usleep@plt>
   10440:	e1a02007 	mov	r2, r7
   10444:	e1a01005 	mov	r1, r5
   10448:	e1a00004 	mov	r0, r4
   1044c:	ebffffc4 	bl	10364 <ioctl@plt>
   10450:	e3a02000 	mov	r2, #0
   10454:	e3051702 	movw	r1, #22274	@ 0x5702
   10458:	e1a00004 	mov	r0, r4
   1045c:	ebffffc0 	bl	10364 <ioctl@plt>
   10460:	eafffff4 	b	10438 <main+0x80>
   10464:	e59f0018 	ldr	r0, [pc, #24]	@ 10484 <main+0xcc>
   10468:	e08f0000 	add	r0, pc, r0
   1046c:	ebffffc2 	bl	1037c <puts@plt>
   10470:	e1a00005 	mov	r0, r5
   10474:	e28dd00c 	add	sp, sp, #12
   10478:	e8bd80f0 	pop	{r4, r5, r6, r7, pc}
   1047c:	0000021c 	.word	0x0000021c
   10480:	000001d8 	.word	0x000001d8
   10484:	00000188 	.word	0x00000188

00010488 <_start>:
   10488:	e3a0b000 	mov	fp, #0
   1048c:	e3a0e000 	mov	lr, #0
   10490:	e49d1004 	pop	{r1}		@ (ldr r1, [sp], #4)
   10494:	e1a0200d 	mov	r2, sp
   10498:	e52d2004 	push	{r2}		@ (str r2, [sp, #-4]!)
   1049c:	e52d0004 	push	{r0}		@ (str r0, [sp, #-4]!)
   104a0:	e59fc010 	ldr	ip, [pc, #16]	@ 104b8 <_start+0x30>
   104a4:	e52dc004 	push	{ip}		@ (str ip, [sp, #-4]!)
   104a8:	e59f000c 	ldr	r0, [pc, #12]	@ 104bc <_start+0x34>
   104ac:	e59f300c 	ldr	r3, [pc, #12]	@ 104c0 <_start+0x38>
   104b0:	ebffffb4 	bl	10388 <__libc_start_main@plt>
   104b4:	ebffffbc 	bl	103ac <abort@plt>
   104b8:	000105d8 	.word	0x000105d8
   104bc:	000103b8 	.word	0x000103b8
   104c0:	00010578 	.word	0x00010578

000104c4 <call_weak_fn>:
   104c4:	e59f3014 	ldr	r3, [pc, #20]	@ 104e0 <call_weak_fn+0x1c>
   104c8:	e59f2014 	ldr	r2, [pc, #20]	@ 104e4 <call_weak_fn+0x20>
   104cc:	e08f3003 	add	r3, pc, r3
   104d0:	e7932002 	ldr	r2, [r3, r2]
   104d4:	e3520000 	cmp	r2, #0
   104d8:	012fff1e 	bxeq	lr
   104dc:	eaffffac 	b	10394 <__gmon_start__@plt>
   104e0:	00010b2c 	.word	0x00010b2c
   104e4:	00000028 	.word	0x00000028

000104e8 <deregister_tm_clones>:
   104e8:	e59f0018 	ldr	r0, [pc, #24]	@ 10508 <deregister_tm_clones+0x20>
   104ec:	e59f3018 	ldr	r3, [pc, #24]	@ 1050c <deregister_tm_clones+0x24>
   104f0:	e1530000 	cmp	r3, r0
   104f4:	012fff1e 	bxeq	lr
   104f8:	e59f3010 	ldr	r3, [pc, #16]	@ 10510 <deregister_tm_clones+0x28>
   104fc:	e3530000 	cmp	r3, #0
   10500:	012fff1e 	bxeq	lr
   10504:	e12fff13 	bx	r3
   10508:	00021034 	.word	0x00021034
   1050c:	00021034 	.word	0x00021034
   10510:	00000000 	.word	0x00000000

00010514 <register_tm_clones>:
   10514:	e59f0024 	ldr	r0, [pc, #36]	@ 10540 <register_tm_clones+0x2c>
   10518:	e59f1024 	ldr	r1, [pc, #36]	@ 10544 <register_tm_clones+0x30>
   1051c:	e0413000 	sub	r3, r1, r0
   10520:	e1a01fa3 	lsr	r1, r3, #31
   10524:	e0811143 	add	r1, r1, r3, asr #2
   10528:	e1b010c1 	asrs	r1, r1, #1
   1052c:	012fff1e 	bxeq	lr
   10530:	e59f3010 	ldr	r3, [pc, #16]	@ 10548 <register_tm_clones+0x34>
   10534:	e3530000 	cmp	r3, #0
   10538:	012fff1e 	bxeq	lr
   1053c:	e12fff13 	bx	r3
   10540:	00021034 	.word	0x00021034
   10544:	00021034 	.word	0x00021034
   10548:	00000000 	.word	0x00000000

0001054c <__do_global_dtors_aux>:
   1054c:	e92d4010 	push	{r4, lr}
   10550:	e59f4018 	ldr	r4, [pc, #24]	@ 10570 <__do_global_dtors_aux+0x24>
   10554:	e5d43000 	ldrb	r3, [r4]
   10558:	e3530000 	cmp	r3, #0
   1055c:	18bd8010 	popne	{r4, pc}
   10560:	ebffffe0 	bl	104e8 <deregister_tm_clones>
   10564:	e3a03001 	mov	r3, #1
   10568:	e5c43000 	strb	r3, [r4]
   1056c:	e8bd8010 	pop	{r4, pc}
   10570:	00021034 	.word	0x00021034

00010574 <frame_dummy>:
   10574:	eaffffe6 	b	10514 <register_tm_clones>

00010578 <__libc_csu_init>:
   10578:	e92d47f0 	push	{r4, r5, r6, r7, r8, r9, sl, lr}
   1057c:	e1a07000 	mov	r7, r0
   10580:	e59f6048 	ldr	r6, [pc, #72]	@ 105d0 <__libc_csu_init+0x58>
   10584:	e1a08001 	mov	r8, r1
   10588:	e1a09002 	mov	r9, r2
   1058c:	e59f5040 	ldr	r5, [pc, #64]	@ 105d4 <__libc_csu_init+0x5c>
   10590:	e08f6006 	add	r6, pc, r6
   10594:	ebffff6a 	bl	10344 <_init>
   10598:	e08f5005 	add	r5, pc, r5
   1059c:	e0466005 	sub	r6, r6, r5
   105a0:	e1b06146 	asrs	r6, r6, #2
   105a4:	08bd87f0 	popeq	{r4, r5, r6, r7, r8, r9, sl, pc}
   105a8:	e3a04000 	mov	r4, #0
   105ac:	e4953004 	ldr	r3, [r5], #4
   105b0:	e2844001 	add	r4, r4, #1
   105b4:	e1a02009 	mov	r2, r9
   105b8:	e1a01008 	mov	r1, r8
   105bc:	e1a00007 	mov	r0, r7
   105c0:	e12fff33 	blx	r3
   105c4:	e1560004 	cmp	r6, r4
   105c8:	1afffff7 	bne	105ac <__libc_csu_init+0x34>
   105cc:	e8bd87f0 	pop	{r4, r5, r6, r7, r8, r9, sl, pc}
   105d0:	00010974 	.word	0x00010974
   105d4:	00010968 	.word	0x00010968

000105d8 <__libc_csu_fini>:
   105d8:	e12fff1e 	bx	lr

Disassembly of section .fini:

000105dc <_fini>:
   105dc:	e92d4008 	push	{r3, lr}
   105e0:	e8bd8008 	pop	{r3, pc}

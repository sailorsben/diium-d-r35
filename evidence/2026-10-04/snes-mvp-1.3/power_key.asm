
device-evidence/snes-mvp-return-20261004T222804Z/snes-mvp/platform-power_key:     file format elf32-littlearm


Disassembly of section .init:

00010444 <_init>:
   10444:	e92d4008 	push	{r3, lr}
   10448:	eb00009f 	bl	106cc <call_weak_fn>
   1044c:	e8bd8008 	pop	{r3, pc}

Disassembly of section .plt:

00010450 <.plt>:
   10450:	e52de004 	push	{lr}		@ (str lr, [sp, #-4]!)
   10454:	e59fe004 	ldr	lr, [pc, #4]	@ 10460 <.plt+0x10>
   10458:	e08fe00e 	add	lr, pc, lr
   1045c:	e5bef008 	ldr	pc, [lr, #8]!
   10460:	00010ba0 	.word	0x00010ba0

00010464 <printf@plt>:
   10464:	e28fc600 	add	ip, pc, #0, 12
   10468:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   1046c:	e5bcfba0 	ldr	pc, [ip, #2976]!	@ 0xba0

00010470 <ioctl@plt>:
   10470:	e28fc600 	add	ip, pc, #0, 12
   10474:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   10478:	e5bcfb98 	ldr	pc, [ip, #2968]!	@ 0xb98

0001047c <usleep@plt>:
   1047c:	e28fc600 	add	ip, pc, #0, 12
   10480:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   10484:	e5bcfb90 	ldr	pc, [ip, #2960]!	@ 0xb90

00010488 <puts@plt>:
   10488:	e28fc600 	add	ip, pc, #0, 12
   1048c:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   10490:	e5bcfb88 	ldr	pc, [ip, #2952]!	@ 0xb88

00010494 <__libc_start_main@plt>:
   10494:	e28fc600 	add	ip, pc, #0, 12
   10498:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   1049c:	e5bcfb80 	ldr	pc, [ip, #2944]!	@ 0xb80

000104a0 <system@plt>:
   104a0:	e28fc600 	add	ip, pc, #0, 12
   104a4:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   104a8:	e5bcfb78 	ldr	pc, [ip, #2936]!	@ 0xb78

000104ac <__gmon_start__@plt>:
   104ac:	e28fc600 	add	ip, pc, #0, 12
   104b0:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   104b4:	e5bcfb70 	ldr	pc, [ip, #2928]!	@ 0xb70

000104b8 <open@plt>:
   104b8:	e28fc600 	add	ip, pc, #0, 12
   104bc:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   104c0:	e5bcfb68 	ldr	pc, [ip, #2920]!	@ 0xb68

000104c4 <mmap@plt>:
   104c4:	e28fc600 	add	ip, pc, #0, 12
   104c8:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   104cc:	e5bcfb60 	ldr	pc, [ip, #2912]!	@ 0xb60

000104d0 <getpagesize@plt>:
   104d0:	e28fc600 	add	ip, pc, #0, 12
   104d4:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   104d8:	e5bcfb58 	ldr	pc, [ip, #2904]!	@ 0xb58

000104dc <munmap@plt>:
   104dc:	e28fc600 	add	ip, pc, #0, 12
   104e0:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   104e4:	e5bcfb50 	ldr	pc, [ip, #2896]!	@ 0xb50

000104e8 <abort@plt>:
   104e8:	e28fc600 	add	ip, pc, #0, 12
   104ec:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   104f0:	e5bcfb48 	ldr	pc, [ip, #2888]!	@ 0xb48

000104f4 <close@plt>:
   104f4:	e28fc600 	add	ip, pc, #0, 12
   104f8:	e28cca10 	add	ip, ip, #16, 20	@ 0x10000
   104fc:	e5bcfb40 	ldr	pc, [ip, #2880]!	@ 0xb40

Disassembly of section .text:

00010500 <main>:
   10500:	e3a02001 	mov	r2, #1
   10504:	e3a01008 	mov	r1, #8
   10508:	e92d47f0 	push	{r4, r5, r6, r7, r8, r9, sl, lr}
   1050c:	e1a00002 	mov	r0, r2
   10510:	e59f9154 	ldr	r9, [pc, #340]	@ 1066c <main+0x16c>
   10514:	eb0000e5 	bl	108b0 <WGPIO>
   10518:	e3a02001 	mov	r2, #1
   1051c:	e3a0100b 	mov	r1, #11
   10520:	e08f9009 	add	r9, pc, r9
   10524:	e3a00004 	mov	r0, #4
   10528:	e3a08068 	mov	r8, #104	@ 0x68
   1052c:	eb0000df 	bl	108b0 <WGPIO>
   10530:	e59f0138 	ldr	r0, [pc, #312]	@ 10670 <main+0x170>
   10534:	e3011002 	movw	r1, #4098	@ 0x1002
   10538:	e3401010 	movt	r1, #16
   1053c:	e3a07d35 	mov	r7, #3392	@ 0xd40
   10540:	e08f0000 	add	r0, pc, r0
   10544:	e3a06000 	mov	r6, #0
   10548:	e34d8000 	movt	r8, #53248	@ 0xd000
   1054c:	ebffffd9 	bl	104b8 <open@plt>
   10550:	e3407003 	movt	r7, #3
   10554:	e3021018 	movw	r1, #8216	@ 0x2018
   10558:	e1a04000 	mov	r4, r0
   1055c:	eb0000aa 	bl	1080c <write_io_memory.constprop.0>
   10560:	e59f010c 	ldr	r0, [pc, #268]	@ 10674 <main+0x174>
   10564:	e08f0000 	add	r0, pc, r0
   10568:	ebffffc6 	bl	10488 <puts@plt>
   1056c:	e1a00004 	mov	r0, r4
   10570:	e30a159e 	movw	r1, #42398	@ 0xa59e
   10574:	eb0000a4 	bl	1080c <write_io_memory.constprop.0>
   10578:	e59f00f8 	ldr	r0, [pc, #248]	@ 10678 <main+0x178>
   1057c:	e08f0000 	add	r0, pc, r0
   10580:	ebffffc0 	bl	10488 <puts@plt>
   10584:	e1a00004 	mov	r0, r4
   10588:	e3a01007 	mov	r1, #7
   1058c:	eb00009e 	bl	1080c <write_io_memory.constprop.0>
   10590:	e59f00e4 	ldr	r0, [pc, #228]	@ 1067c <main+0x17c>
   10594:	e08f0000 	add	r0, pc, r0
   10598:	ebffffba 	bl	10488 <puts@plt>
   1059c:	ea000003 	b	105b0 <main+0xb0>
   105a0:	e356000a 	cmp	r6, #10
   105a4:	0a00000e 	beq	105e4 <main+0xe4>
   105a8:	e1a0600a 	mov	r6, sl
   105ac:	ebffffb2 	bl	1047c <usleep@plt>
   105b0:	e1a01008 	mov	r1, r8
   105b4:	e1a00004 	mov	r0, r4
   105b8:	e286a001 	add	sl, r6, #1
   105bc:	eb00006f 	bl	10780 <read_io_memory>
   105c0:	e1a05000 	mov	r5, r0
   105c4:	e1a00009 	mov	r0, r9
   105c8:	e205100f 	and	r1, r5, #15
   105cc:	ebffffa4 	bl	10464 <printf@plt>
   105d0:	e2155008 	ands	r5, r5, #8
   105d4:	e1a00007 	mov	r0, r7
   105d8:	1afffff0 	bne	105a0 <main+0xa0>
   105dc:	e1a0a005 	mov	sl, r5
   105e0:	eafffff0 	b	105a8 <main+0xa8>
   105e4:	e59f0094 	ldr	r0, [pc, #148]	@ 10680 <main+0x180>
   105e8:	e3a06064 	mov	r6, #100	@ 0x64
   105ec:	e59f7090 	ldr	r7, [pc, #144]	@ 10684 <main+0x184>
   105f0:	e3a05068 	mov	r5, #104	@ 0x68
   105f4:	e08f0000 	add	r0, pc, r0
   105f8:	e34d6000 	movt	r6, #53248	@ 0xd000
   105fc:	ebffffa1 	bl	10488 <puts@plt>
   10600:	e34d5000 	movt	r5, #53248	@ 0xd000
   10604:	e08f7007 	add	r7, pc, r7
   10608:	e1a01006 	mov	r1, r6
   1060c:	e1a00004 	mov	r0, r4
   10610:	eb00005a 	bl	10780 <read_io_memory>
   10614:	e1a01000 	mov	r1, r0
   10618:	e1a00007 	mov	r0, r7
   1061c:	ebffff90 	bl	10464 <printf@plt>
   10620:	e1a01005 	mov	r1, r5
   10624:	e1a00004 	mov	r0, r4
   10628:	eb000054 	bl	10780 <read_io_memory>
   1062c:	e1a01000 	mov	r1, r0
   10630:	e59f0050 	ldr	r0, [pc, #80]	@ 10688 <main+0x188>
   10634:	e08f0000 	add	r0, pc, r0
   10638:	ebffff89 	bl	10464 <printf@plt>
   1063c:	e3a02000 	mov	r2, #0
   10640:	e3a01008 	mov	r1, #8
   10644:	e3a00001 	mov	r0, #1
   10648:	eb000098 	bl	108b0 <WGPIO>
   1064c:	e3a02001 	mov	r2, #1
   10650:	e3a0100b 	mov	r1, #11
   10654:	e3a00004 	mov	r0, #4
   10658:	eb000094 	bl	108b0 <WGPIO>
   1065c:	e59f0028 	ldr	r0, [pc, #40]	@ 1068c <main+0x18c>
   10660:	e08f0000 	add	r0, pc, r0
   10664:	ebffff8d 	bl	104a0 <system@plt>
   10668:	eaffffe6 	b	10608 <main+0x108>
   1066c:	0000058c 	.word	0x0000058c
   10670:	00000524 	.word	0x00000524
   10674:	0000050c 	.word	0x0000050c
   10678:	00000508 	.word	0x00000508
   1067c:	00000504 	.word	0x00000504
   10680:	000004cc 	.word	0x000004cc
   10684:	000004c8 	.word	0x000004c8
   10688:	000004ac 	.word	0x000004ac
   1068c:	00000494 	.word	0x00000494

00010690 <_start>:
   10690:	e3a0b000 	mov	fp, #0
   10694:	e3a0e000 	mov	lr, #0
   10698:	e49d1004 	pop	{r1}		@ (ldr r1, [sp], #4)
   1069c:	e1a0200d 	mov	r2, sp
   106a0:	e52d2004 	push	{r2}		@ (str r2, [sp, #-4]!)
   106a4:	e52d0004 	push	{r0}		@ (str r0, [sp, #-4]!)
   106a8:	e59fc010 	ldr	ip, [pc, #16]	@ 106c0 <_start+0x30>
   106ac:	e52dc004 	push	{ip}		@ (str ip, [sp, #-4]!)
   106b0:	e59f000c 	ldr	r0, [pc, #12]	@ 106c4 <_start+0x34>
   106b4:	e59f300c 	ldr	r3, [pc, #12]	@ 106c8 <_start+0x38>
   106b8:	ebffff75 	bl	10494 <__libc_start_main@plt>
   106bc:	ebffff89 	bl	104e8 <abort@plt>
   106c0:	000109cc 	.word	0x000109cc
   106c4:	00010500 	.word	0x00010500
   106c8:	0001096c 	.word	0x0001096c

000106cc <call_weak_fn>:
   106cc:	e59f3014 	ldr	r3, [pc, #20]	@ 106e8 <call_weak_fn+0x1c>
   106d0:	e59f2014 	ldr	r2, [pc, #20]	@ 106ec <call_weak_fn+0x20>
   106d4:	e08f3003 	add	r3, pc, r3
   106d8:	e7932002 	ldr	r2, [r3, r2]
   106dc:	e3520000 	cmp	r2, #0
   106e0:	012fff1e 	bxeq	lr
   106e4:	eaffff70 	b	104ac <__gmon_start__@plt>
   106e8:	00010924 	.word	0x00010924
   106ec:	00000040 	.word	0x00000040

000106f0 <deregister_tm_clones>:
   106f0:	e59f0018 	ldr	r0, [pc, #24]	@ 10710 <deregister_tm_clones+0x20>
   106f4:	e59f3018 	ldr	r3, [pc, #24]	@ 10714 <deregister_tm_clones+0x24>
   106f8:	e1530000 	cmp	r3, r0
   106fc:	012fff1e 	bxeq	lr
   10700:	e59f3010 	ldr	r3, [pc, #16]	@ 10718 <deregister_tm_clones+0x28>
   10704:	e3530000 	cmp	r3, #0
   10708:	012fff1e 	bxeq	lr
   1070c:	e12fff13 	bx	r3
   10710:	0002104c 	.word	0x0002104c
   10714:	0002104c 	.word	0x0002104c
   10718:	00000000 	.word	0x00000000

0001071c <register_tm_clones>:
   1071c:	e59f0024 	ldr	r0, [pc, #36]	@ 10748 <register_tm_clones+0x2c>
   10720:	e59f1024 	ldr	r1, [pc, #36]	@ 1074c <register_tm_clones+0x30>
   10724:	e0413000 	sub	r3, r1, r0
   10728:	e1a01fa3 	lsr	r1, r3, #31
   1072c:	e0811143 	add	r1, r1, r3, asr #2
   10730:	e1b010c1 	asrs	r1, r1, #1
   10734:	012fff1e 	bxeq	lr
   10738:	e59f3010 	ldr	r3, [pc, #16]	@ 10750 <register_tm_clones+0x34>
   1073c:	e3530000 	cmp	r3, #0
   10740:	012fff1e 	bxeq	lr
   10744:	e12fff13 	bx	r3
   10748:	0002104c 	.word	0x0002104c
   1074c:	0002104c 	.word	0x0002104c
   10750:	00000000 	.word	0x00000000

00010754 <__do_global_dtors_aux>:
   10754:	e92d4010 	push	{r4, lr}
   10758:	e59f4018 	ldr	r4, [pc, #24]	@ 10778 <__do_global_dtors_aux+0x24>
   1075c:	e5d43000 	ldrb	r3, [r4]
   10760:	e3530000 	cmp	r3, #0
   10764:	18bd8010 	popne	{r4, pc}
   10768:	ebffffe0 	bl	106f0 <deregister_tm_clones>
   1076c:	e3a03001 	mov	r3, #1
   10770:	e5c43000 	strb	r3, [r4]
   10774:	e8bd8010 	pop	{r4, pc}
   10778:	0002104c 	.word	0x0002104c

0001077c <frame_dummy>:
   1077c:	eaffffe6 	b	1071c <register_tm_clones>

00010780 <read_io_memory>:
   10780:	e92d40f0 	push	{r4, r5, r6, r7, lr}
   10784:	e2504000 	subs	r4, r0, #0
   10788:	e24dd00c 	sub	sp, sp, #12
   1078c:	b3a07000 	movlt	r7, #0
   10790:	ba000014 	blt	107e8 <read_io_memory+0x68>
   10794:	e1a05001 	mov	r5, r1
   10798:	ebffff4c 	bl	104d0 <getpagesize@plt>
   1079c:	e58d4000 	str	r4, [sp]
   107a0:	e1a04000 	mov	r4, r0
   107a4:	e2600000 	rsb	r0, r0, #0
   107a8:	e3a03001 	mov	r3, #1
   107ac:	e0000005 	and	r0, r0, r5
   107b0:	e1a01004 	mov	r1, r4
   107b4:	e58d0004 	str	r0, [sp, #4]
   107b8:	e1a02003 	mov	r2, r3
   107bc:	e3a00000 	mov	r0, #0
   107c0:	ebffff3f 	bl	104c4 <mmap@plt>
   107c4:	e3700001 	cmn	r0, #1
   107c8:	e1a06000 	mov	r6, r0
   107cc:	0a000008 	beq	107f4 <read_io_memory+0x74>
   107d0:	e2441001 	sub	r1, r4, #1
   107d4:	e0055001 	and	r5, r5, r1
   107d8:	e7907005 	ldr	r7, [r0, r5]
   107dc:	e1a01004 	mov	r1, r4
   107e0:	e1a00006 	mov	r0, r6
   107e4:	ebffff3c 	bl	104dc <munmap@plt>
   107e8:	e1a00007 	mov	r0, r7
   107ec:	e28dd00c 	add	sp, sp, #12
   107f0:	e8bd80f0 	pop	{r4, r5, r6, r7, pc}
   107f4:	e59f000c 	ldr	r0, [pc, #12]	@ 10808 <read_io_memory+0x88>
   107f8:	e1a01005 	mov	r1, r5
   107fc:	e08f0000 	add	r0, pc, r0
   10800:	ebffff17 	bl	10464 <printf@plt>
   10804:	eafffff4 	b	107dc <read_io_memory+0x5c>
   10808:	000001d8 	.word	0x000001d8

0001080c <write_io_memory.constprop.0>:
   1080c:	e92d40f0 	push	{r4, r5, r6, r7, lr}
   10810:	e2505000 	subs	r5, r0, #0
   10814:	e24dd00c 	sub	sp, sp, #12
   10818:	ba000018 	blt	10880 <write_io_memory.constprop.0+0x74>
   1081c:	e1a06001 	mov	r6, r1
   10820:	e3a070ec 	mov	r7, #236	@ 0xec
   10824:	e34d7000 	movt	r7, #53248	@ 0xd000
   10828:	ebffff28 	bl	104d0 <getpagesize@plt>
   1082c:	e58d5000 	str	r5, [sp]
   10830:	e1a04000 	mov	r4, r0
   10834:	e2600000 	rsb	r0, r0, #0
   10838:	e1a01004 	mov	r1, r4
   1083c:	e0000007 	and	r0, r0, r7
   10840:	e3a03001 	mov	r3, #1
   10844:	e58d0004 	str	r0, [sp, #4]
   10848:	e3a02003 	mov	r2, #3
   1084c:	e3a00000 	mov	r0, #0
   10850:	ebffff1b 	bl	104c4 <mmap@plt>
   10854:	e3700001 	cmn	r0, #1
   10858:	e1a05000 	mov	r5, r0
   1085c:	0a00000c 	beq	10894 <write_io_memory.constprop.0+0x88>
   10860:	e2443001 	sub	r3, r4, #1
   10864:	e0077003 	and	r7, r7, r3
   10868:	e7806007 	str	r6, [r0, r7]
   1086c:	e1a01004 	mov	r1, r4
   10870:	e1a00005 	mov	r0, r5
   10874:	e28dd00c 	add	sp, sp, #12
   10878:	e8bd40f0 	pop	{r4, r5, r6, r7, lr}
   1087c:	eaffff16 	b	104dc <munmap@plt>
   10880:	e59f0020 	ldr	r0, [pc, #32]	@ 108a8 <write_io_memory.constprop.0+0x9c>
   10884:	e08f0000 	add	r0, pc, r0
   10888:	e28dd00c 	add	sp, sp, #12
   1088c:	e8bd40f0 	pop	{r4, r5, r6, r7, lr}
   10890:	eafffefc 	b	10488 <puts@plt>
   10894:	e59f0010 	ldr	r0, [pc, #16]	@ 108ac <write_io_memory.constprop.0+0xa0>
   10898:	e1a01007 	mov	r1, r7
   1089c:	e08f0000 	add	r0, pc, r0
   108a0:	ebfffeef 	bl	10464 <printf@plt>
   108a4:	eafffff0 	b	1086c <write_io_memory.constprop.0+0x60>
   108a8:	00000160 	.word	0x00000160
   108ac:	00000138 	.word	0x00000138

000108b0 <WGPIO>:
   108b0:	e92d40f0 	push	{r4, r5, r6, r7, lr}
   108b4:	e1a06000 	mov	r6, r0
   108b8:	e59f009c 	ldr	r0, [pc, #156]	@ 1095c <WGPIO+0xac>
   108bc:	e24dd014 	sub	sp, sp, #20
   108c0:	e1a05002 	mov	r5, r2
   108c4:	e3a03001 	mov	r3, #1
   108c8:	e1812406 	orr	r2, r1, r6, lsl #8
   108cc:	e1a07001 	mov	r7, r1
   108d0:	e08f0000 	add	r0, pc, r0
   108d4:	e3a01002 	mov	r1, #2
   108d8:	e98d002c 	stmib	sp, {r2, r3, r5}
   108dc:	ebfffef5 	bl	104b8 <open@plt>
   108e0:	e2504000 	subs	r4, r0, #0
   108e4:	ba000017 	blt	10948 <WGPIO+0x98>
   108e8:	e3a01c47 	mov	r1, #18176	@ 0x4700
   108ec:	e28d2004 	add	r2, sp, #4
   108f0:	e344100c 	movt	r1, #16396	@ 0x400c
   108f4:	ebfffedd 	bl	10470 <ioctl@plt>
   108f8:	e1a01000 	mov	r1, r0
   108fc:	e1a00004 	mov	r0, r4
   10900:	e1a04001 	mov	r4, r1
   10904:	ebfffefa 	bl	104f4 <close@plt>
   10908:	e3540000 	cmp	r4, #0
   1090c:	1a000007 	bne	10930 <WGPIO+0x80>
   10910:	e59f0048 	ldr	r0, [pc, #72]	@ 10960 <WGPIO+0xb0>
   10914:	e1a03007 	mov	r3, r7
   10918:	e1a02006 	mov	r2, r6
   1091c:	e1a01005 	mov	r1, r5
   10920:	e08f0000 	add	r0, pc, r0
   10924:	ebfffece 	bl	10464 <printf@plt>
   10928:	e28dd014 	add	sp, sp, #20
   1092c:	e8bd80f0 	pop	{r4, r5, r6, r7, pc}
   10930:	e59f002c 	ldr	r0, [pc, #44]	@ 10964 <WGPIO+0xb4>
   10934:	e1a01004 	mov	r1, r4
   10938:	e08f0000 	add	r0, pc, r0
   1093c:	ebfffec8 	bl	10464 <printf@plt>
   10940:	e28dd014 	add	sp, sp, #20
   10944:	e8bd80f0 	pop	{r4, r5, r6, r7, pc}
   10948:	e59f0018 	ldr	r0, [pc, #24]	@ 10968 <WGPIO+0xb8>
   1094c:	e08f0000 	add	r0, pc, r0
   10950:	ebfffecc 	bl	10488 <puts@plt>
   10954:	e28dd014 	add	sp, sp, #20
   10958:	e8bd80f0 	pop	{r4, r5, r6, r7, pc}
   1095c:	00000128 	.word	0x00000128
   10960:	00000120 	.word	0x00000120
   10964:	000000e8 	.word	0x000000e8
   10968:	000000b8 	.word	0x000000b8

0001096c <__libc_csu_init>:
   1096c:	e92d47f0 	push	{r4, r5, r6, r7, r8, r9, sl, lr}
   10970:	e1a07000 	mov	r7, r0
   10974:	e59f6048 	ldr	r6, [pc, #72]	@ 109c4 <__libc_csu_init+0x58>
   10978:	e1a08001 	mov	r8, r1
   1097c:	e1a09002 	mov	r9, r2
   10980:	e59f5040 	ldr	r5, [pc, #64]	@ 109c8 <__libc_csu_init+0x5c>
   10984:	e08f6006 	add	r6, pc, r6
   10988:	ebfffead 	bl	10444 <_init>
   1098c:	e08f5005 	add	r5, pc, r5
   10990:	e0466005 	sub	r6, r6, r5
   10994:	e1b06146 	asrs	r6, r6, #2
   10998:	08bd87f0 	popeq	{r4, r5, r6, r7, r8, r9, sl, pc}
   1099c:	e3a04000 	mov	r4, #0
   109a0:	e4953004 	ldr	r3, [r5], #4
   109a4:	e2844001 	add	r4, r4, #1
   109a8:	e1a02009 	mov	r2, r9
   109ac:	e1a01008 	mov	r1, r8
   109b0:	e1a00007 	mov	r0, r7
   109b4:	e12fff33 	blx	r3
   109b8:	e1560004 	cmp	r6, r4
   109bc:	1afffff7 	bne	109a0 <__libc_csu_init+0x34>
   109c0:	e8bd87f0 	pop	{r4, r5, r6, r7, r8, r9, sl, pc}
   109c4:	00010580 	.word	0x00010580
   109c8:	00010574 	.word	0x00010574

000109cc <__libc_csu_fini>:
   109cc:	e12fff1e 	bx	lr

Disassembly of section .fini:

000109d0 <_fini>:
   109d0:	e92d4008 	push	{r3, lr}
   109d4:	e8bd8008 	pop	{r3, pc}

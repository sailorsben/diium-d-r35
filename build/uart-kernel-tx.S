/* Direct, in-place correction of the exact vendor UART TX ISR body.
 * Entered in the original ISR frame: r4=port, r5=entry status.
 * RX code, IRQ registration, locking and original epilogue remain unchanged.
 */
.syntax unified
.arm
.section .text.tx,"ax",%progbits
.global corrected_tx
corrected_tx:
 mov r6,r5
 ldr r0,[r4,#4]
 bl 0xc0117364
 ldrb r2,[r4,#0x108]
 and r2,r2,#2
 /* Both hardware bit14 and software bit1 must be enabled. */
 tst r0,r2,lsl #13
 beq 0xc011780c
 ldrb r1,[r4,#0x58]
 cmp r1,#0
 beq ordinary
 tst r6,#0x20
 bne 0xc011780c
 b 0xc01179cc
ordinary:
 ldr r5,[r4,#0x64]
 ldrd r2,r3,[r5,#0xb8]
 cmp r2,r3
 beq corrected_stop
 ldr r2,[r5,#0x4c]
 cmp r2,#0
 ldrbne r2,[r2,#0x124]
 tstne r2,#1
 bne corrected_stop
 ldr r2,[r4,#0xa8]
 cmp r2,#0
 bne corrected_stop
 tst r6,#0x20
 bne 0xc011780c
 ldr r2,[r5,#0xb4]
 ldrb r1,[r2,r3]
 ldr r0,[r4,#4]
 bl 0xc01172fc
 ldr r3,[r5,#0xbc]
 add r3,r3,#1
 ubfx r3,r3,#0,#12
 str r3,[r5,#0xbc]
 ldr r2,[r4,#0x7c]
 add r2,r2,#1
 str r2,[r4,#0x7c]
 ldrd r2,r3,[r5,#0xb8]
 sub r6,r2,r3
 tst r6,#0xf00
 mov r0,r4
 bleq 0xc0335f58
 cmp r6,#0
 beq corrected_stop
 b 0xc011780c
.section .text.stop,"ax",%progbits
.global corrected_stop
corrected_stop:
 mov r0,r4
 bl 0xc011755c
 b 0xc011780c

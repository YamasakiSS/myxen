/*
 * util.h: Useful utility functions.
 *
 * Leendert van Doorn, leendert@watson.ibm.com
 * Copyright (c) 2005, International Business Machines Corporation.
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms and conditions of the GNU General Public License,
 * version 2, as published by the Free Software Foundation.
 *
 * This program is distributed in the hope it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along with
 * this program; if not, write to the Free Software Foundation, Inc., 59 Temple
 * Place - Suite 330, Boston, MA 02111-1307 USA.
 */
#ifndef __UTIL_H__
#define __UTIL_H__

#include <stdarg.h>
#include <vm86.h>


#define	LINUX_E820_MAP_NR	((unsigned char *)0x901E8)
#define	LINUX_E820_MAP		((struct e820entry *)0x902D0)

#define	E820_RAM	1
#define	E820_RESERVED	2
#define	E820_ACPI	3
#define	E820_NVS	4
#define	E820_IO		16
#define	E820_SHARED	17

struct e820entry {
	unsigned long long	addr;
	unsigned long long	size;
	unsigned long		type;
} __attribute__((packed));


#define	offsetof(type, member)	((unsigned) &((type *)0)->member)

struct vmx_assist_context;

extern void hexdump(unsigned char *, int);
extern void dump_regs(struct regs *);
extern void dump_vmx_context(struct vmx_assist_context *);
extern void print_e820_map(struct e820entry *, int);
extern void dump_dtr(unsigned long, unsigned long);
extern void *memcpy(void *, const void *, unsigned);
extern void *memset(void *, int, unsigned);
extern int printf(const char *fmt, ...);
extern int vprintf(const char *fmt, va_list ap);
extern void panic(const char *format, ...);
extern void halt(void);

#endif /* __UTIL_H__ */

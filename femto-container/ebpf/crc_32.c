// /* This scale factor will be changed to equalise the runtime of the
//    benchmarks. */
#define LOCAL_SCALE_FACTOR 170

// /**********************************************************************\
//   |* Demonstration program to compute the 32-bit CRC used as the frame  *|
//   |* check sequence in ADCCP (ANSI X3.66, also known as FIPS PUB 71     *|
//   |* and FED-STD-1003, the U.S. versions of CCITT's X.25 link-level     *|
//   |* protocol).  The 32-bit FCS was added via the Federal Register,     *|
//   |* 1 June 1982, p.23798.  I presume but don't know for certain that   *|
//   |* this polynomial is or will be included in CCITT V.41, which        *|
//   |* defines the 16-bit CRC (often called CRC-CCITT) polynomial.  FIPS  *|
//   |* PUB 78 says that the 32-bit FCS reduces otherwise undetected       *|
//   |* errors by a factor of 10^-5 over 16-bit FCS.                       *|
//   \**********************************************************************/

// /* Some basic types.  */
typedef unsigned char BYTE;
typedef unsigned long DWORD;
typedef unsigned short WORD;

#include <stdint.h>

#define UPDC32(tab,octet,crc) (tab[((crc)^((BYTE)octet)) & 0xff] ^ ((crc) >> 8))

// /* Need an unsigned type capable of holding 32 bits; */

typedef DWORD UNS_32_BITS;

// /* Copyright (C) 1986 Gary S. Brown.  You may use this program, or
//    code or tables extracted from it, as desired without restriction.*/

// /* First, the polynomial itself and its table of feedback terms.  The  */
// /* polynomial is                                                       */
// /* X^32+X^26+X^23+X^22+X^16+X^12+X^11+X^10+X^8+X^7+X^5+X^4+X^2+X^1+X^0 */
// /* Note that we take it "backwards" and put the highest-order term in  */
// /* the lowest-order bit.  The X^32 term is "implied"; the LSB is the   */
// /* X^31 term, etc.  The X^0 term (usually shown as "+1") results in    */
// /* the MSB being 1.                                                    */

// /* Note that the usual hardware shift register implementation, which   */
// /* is what we're using (we're merely optimizing it by doing eight-bit  */
// /* chunks at a time) shifts bits into the lowest-order term.  In our   */
// /* implementation, that means shifting towards the right.  Why do we   */
// /* do it this way?  Because the calculated CRC must be transmitted in  */
// /* order from highest-order term to lowest-order term.  UARTs transmit */
// /* characters in order from LSB to MSB.  By storing the CRC this way,  */
// /* we hand it to the UART in the order low-byte to high-byte; the UART */
// /* sends each low-bit to hight-bit; and the result is transmission bit */
// /* by bit from highest- to lowest-order term without requiring any bit */
// /* shuffling on our part.  Reception works similarly.                  */

// /* The feedback terms table consists of 256, 32-bit entries.  Notes:   */
// /*                                                                     */
// /*  1. The table can be generated at runtime if desired; code to do so */
// /*     is shown later.  It might not be obvious, but the feedback      */
// /*     terms simply represent the results of eight shift/xor opera-    */
// /*     tions for all combinations of data and CRC register values.     */
// /*                                                                     */
// /*  2. The CRC accumulation logic is the same for all CRC polynomials, */
// /*     be they sixteen or thirty-two bits wide.  You simply choose the */
// /*     appropriate table.  Alternatively, because the table can be     */
// /*     generated at runtime, you can start by generating the table for */
// /*     the polynomial in question and use exactly the same "updcrc",   */
// /*     if your application needn't simultaneously handle two CRC       */
// /*     polynomials.  (Note, however, that XMODEM is strange.)          */
// /*                                                                     */
// /*  3. For 16-bit CRCs, the table entries need be only 16 bits wide;   */
// /*     of course, 32-bit entries work OK if the high 16 bits are zero. */
// /*                                                                     */
// /*  4. The values must be right-shifted by eight bits by the "updcrc"  */
// /*     logic; the shift must be unsigned (bring in zeroes).  On some   */
// /*     hardware you could probably optimize the shift in assembler by  */
// /*     using byte-swap instructions.                                   */

// /* The BEEBS version of this code uses its own version of rand, to
//    avoid library/architecture variation. */


static unsigned long int seed __attribute__((section(".data"))) = 0;

int inline rand_beebs (void)
{
  seed = (seed * 1103515245UL + 12345UL) & ((1UL << 31) - 1UL);
  return (int) (seed >> 16);
}

void inline srand_beebs (unsigned int new_seed)
{
  seed = (long int) new_seed;
}

DWORD inline crc32pseudo (UNS_32_BITS *tab)
{
  int i;
  register DWORD oldcrc32;

  oldcrc32 = 0xFFFFFFFF;

  for (i = 0; i < 1024; ++i)
    {
      oldcrc32 = UPDC32(tab, rand_beebs(), oldcrc32);
    }

  return ~oldcrc32;
}

int benchmark (UNS_32_BITS *tab)
{
  unsigned int lsf = LOCAL_SCALE_FACTOR;
  unsigned int gsf = GLOBAL_SCALE_FACTOR;
  int i;
  DWORD r;

  for (unsigned int lsf_cnt = 0; lsf_cnt < lsf; lsf_cnt++)
    for (unsigned int gsf_cnt = 0; gsf_cnt < gsf; gsf_cnt++) {
        srand_beebs(0);
        r = crc32pseudo(tab);
      
      }

  return (int) (r % 32768) == 11433;

  // srand_beebs(0);

  // volatile DWORD init_crc_32 = 0x7FFFFFFF;
  // init_crc_32 = (init_crc_32 << 1) + 1;

  // register DWORD oldcrc32 = 0xFFFFFFFF;
  // DWORD tab_value = 0;
  // int rand = 0;
  // DWORD shifted = 0;
  // for (i = 0; i < 4; i++) {
  //   rand = rand_beebs();
  //   tab_value = tab[((oldcrc32)^((BYTE)rand)) & 0xff];
  //   shifted = oldcrc32 >> 8;

  //   oldcrc32 = UPDC32(tab, rand, oldcrc32);
  // }

  // return shifted;
}
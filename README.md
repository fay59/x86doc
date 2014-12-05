x86doc
======

I needed a parsable copy of Intel's x86 instruction set documentation for a
personal project, so I downloaded volumes 2A and 2B of the *Intel® 64 and IA-32
Architectures Software Developer's Manual* (which can be found [here][1] and
[here][2], respectively), and used a online PDF-to-HTML tool to transform them
to HTML files. Unfortunately, the result was beyond terrible and absolutely
unusable.

They say that you're never better served than by yourself, so I took the matter
into my own, [pdfminer][3]-gloved hands to extract HTML pages straight from the
documentation PDF themselves.

*This branch is experimental.* Right now, it parses 417 of the 480 instructions
documented in Volume 2A and Volume 2B. Complex pages usually (but not always)
render better with this branch than the `master` branch, but not all pages
render. Be sure to check out the `master` branch if you want something
immediately usable.

The `master` documentation set can be found on [this page][4].

As of now, these are the 37 instructions that do not parse at all. Most fail
because of one of these reasons:

* the page contains a frameless figure and the script freaks out;
* the page contains footnotes and the script freaks out;
* some table lines are abnormally thick;
* some tables seem to be all right but the script still freaks out.

232/245
211/235
433/480

The list is:

* **CPUID**—CPU Identification *(unsure, really long)*
* **CVTDQ2PD**—Convert Packed Dword Integers to Packed Double-Precision FP Values *(frameless figure)*
* **CVTPD2PS**—Convert Packed Double-Precision FP Values to Packed Single-Precision FP Values *(frameless figure)*
* **CVTPS2PD**—Convert Packed Single-Precision FP Values to Packed Double-Precision FP Values *(frameless figure)*
* **FADD/FADDP/FIADD**—Add *(abnormally thick table lines)*
* **FDIV/FDIVP/FIDIV**—Divide *(abnormally thick table lines)*
* **FDIVR/FDIVRP/FIDIVR**—Reverse Divide *(abnormally thick table lines)*
* **FXSAVE**—Save x87 FPU, MMX Technology, and SSE State *(unsure)*
* **HADDPD**—Packed Double-FP Horizontal Add *(frameless figure)*
* **HADDPS**—Packed Single-FP Horizontal Add *(frameless figure)*
* **HSUBPD**—Packed Double-FP Horizontal Subtract *(frameless figure)*
* **HSUBPS**—Packed Single-FP Horizontal Subtract *(frameless figure)*
* **MPSADBW**—Compute Multiple Packed Sums of Absolute Difference *(unsure)*
* **PALIGNR**—Packed Align Right *(frameless figure)*
* **PDEP**—Parallel Bits Deposit *(frameless figure)*
* **PEXT**—Parallel Bits Extract *(frameless figure)*
* **PMADDWD**—Multiply and Add Packed Integers *(unsure)*
* **PMULHUW**—Multiply Packed Unsigned Integers and Store High Result *(unsure)*
* **PMULLW**—Multiply Packed Signed Integers and Store Low Result *(unsure)*
* **PSADBW**—Compute Sum of Absolute Differences *(unsure)*
* **PSHUFD**—Shuffle Packed Doublewords *(frameless figure)*
* **PSLLW/PSLLD/PSLLQ**—Shift Packed Data Left Logical *(unsure)*
* **PSRAW/PSRAD**—Shift Packed Data Right Arithmetic *(unsure)*
* **PSRLW/PSRLD/PSRLQ**—Shift Packed Data Right Logical *(unsure)*
* **ROUNDPD**—Round Packed Double Precision Floating-Point Values *(unsure)*
* **SHUFPD**—Shuffle Packed Double-Precision Floating-Point Values *(unsure)*
* **SHUFPS**—Shuffle Packed Single-Precision Floating-Point Values *(unsure)*
* **UNPCKHPD**—Unpack and Interleave High Packed Double-Precision Floating-Point Values *(unsure)*
* **UNPCKHPS**—Unpack and Interleave High Packed Single-Precision Floating-Point Values *(unsure)*
* **UNPCKLPD**—Unpack and Interleave Low Packed Double-Precision Floating-Point Values *(unsure)*
* **UNPCKLPS**—Unpack and Interleave Low Packed Single-Precision Floating-Point Values *(unsure)*
* **VBROADCAST**—Broadcast Floating-Point Data *(unsure)*
* **VCVTPS2PH**—Convert Single-Precision FP value to 16-bit FP value *(unsure)*
* **VPBROADCAST**—Broadcast Integer Data *(frameless figures)*
* **VPERM2I128**—Permute Integer Values *(frameless figures)*
* **VPERMILPD**—Permute Double-Precision Floating-Point Values *(frameless figures)*
* **VPERMILPS**—Permute Single-Precision Floating-Point Values *(frameless figures)*
* **VPERM2F128**—Permute Floating-Point Values 

I'm working on that.

  [1]: http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf
  [2]: http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2b-manual.pdf
  [3]: http://www.unixuser.org/~euske/python/pdfminer/
  [4]: http://www.felixcloutier.com/x86/
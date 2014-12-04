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

*This branch is experimental.* Right now, it parses about 415 of the 470ish
instructions documented in Volume 2A and Volume 2B. Complex pages usually (but
not always) render better with this branch than the `master` branch, but not all
pages render. Be sure to check out the `master` branch if you want something
immediately usable.

The `master` documentation set can be found on [this page][4].

As of now, these are the 46 instructions that do not parse at all:

* **ADDSUBPD**—Packed Double-FP Add/Subtract 
* **ADDSUBPS**—Packed Single-FP Add/Subtract 
* **CMPPD**—Compare Packed Double-Precision Floating-Point Values
* **CPUID**—CPU Identification 
* **CVTDQ2PD**—Convert Packed Dword Integers to Packed Double-Precision FP Values 
* **CVTPD2PS**—Convert Packed Double-Precision FP Values to Packed Single-Precision FP Values 
* **CVTPS2PD**—Convert Packed Single-Precision FP Values to Packed Double-Precision FP Values 
* **FADD/FADDP/FIADD**—Add 
* **FDIV/FDIVP/FIDIV**—Divide 
* **FDIVR/FDIVRP/FIDIVR**—Reverse Divide 
* **FIST/FISTP**—Store Integer 
* **FXSAVE**—Save x87 FPU, MMX Technology, and SSE State 
* **HADDPD**—Packed Double-FP Horizontal Add 
* **HADDPS**—Packed Single-FP Horizontal Add 
* **HSUBPD**—Packed Double-FP Horizontal Subtract 
* **HSUBPS**—Packed Single-FP Horizontal Subtract 
* **MOVDDUP**—Move One Double-FP and Duplicate 
* **MOVSHDUP**—Move Packed Single-FP High and Duplicate 
* **MOVSLDUP**—Move Packed Single-FP Low and Duplicate 
* **MPSADBW**—Compute Multiple Packed Sums of Absolute Difference 
* **PALIGNR**—Packed Align Right 
* **PDEP**—Parallel Bits Deposit 
* **PEXT**—Parallel Bits Extract 
* **PMADDWD**—Multiply and Add Packed Integers 
* **PMULHUW**—Multiply Packed Unsigned Integers and Store High Result 
* **PMULLW**—Multiply Packed Signed Integers and Store Low Result 
* **POPF/POPFD/POPFQ**—Pop Stack into EFLAGS Register 
* **PSADBW**—Compute Sum of Absolute Differences 
* **PSHUFD**—Shuffle Packed Doublewords 
* **PSLLW/PSLLD/PSLLQ**—Shift Packed Data Left Logical 
* **PSRAW/PSRAD**—Shift Packed Data Right Arithmetic 
* **PSRLW/PSRLD/PSRLQ**—Shift Packed Data Right Logical 
* **ROUNDPD**—Round Packed Double Precision Floating-Point Values 
* **SHUFPD**—Shuffle Packed Double-Precision Floating-Point Values 
* **SHUFPS**—Shuffle Packed Single-Precision Floating-Point Values 
* **UNPCKHPD**—Unpack and Interleave High Packed Double-Precision Floating-Point Values 
* **UNPCKHPS**—Unpack and Interleave High Packed Single-Precision Floating-Point Values 
* **UNPCKLPD**—Unpack and Interleave Low Packed Double-Precision Floating-Point Values 
* **UNPCKLPS**—Unpack and Interleave Low Packed Single-Precision Floating-Point Values 
* **VBROADCAST**—Broadcast Floating-Point Data 
* **VCVTPS2PH**—Convert Single-Precision FP value to 16-bit FP value 
* **VPBROADCAST**—Broadcast Integer Data 
* **VPERM2I128**—Permute Integer Values 
* **VPERMILPD**—Permute Double-Precision Floating-Point Values 
* **VPERMILPS**—Permute Single-Precision Floating-Point Values 
* **VPERM2F128**—Permute Floating-Point Values 

Most fail because of one of these reasons:

* the page contains a framed figure and the script freaks out;
* the page contains a frameless figure and the script freaks out;
* the page contains framed and frameless figures and the script freaks out;
* some table lines are abnormally thick;
* some tables seem to be all right but the script still freaks out.

I'm working on that.

  [1]: http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf
  [2]: http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2b-manual.pdf
  [3]: http://www.unixuser.org/~euske/python/pdfminer/
  [4]: http://www.felixcloutier.com/x86/
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

As of now, these are the 50 instructions that do not parse at all:

* **CMPPD**—Compare Packed Double-Precision Floating-Point Values
* **CPUID**—CPU Identification 
* **CVTDQ2PD**—Convert Packed Dword Integers to Packed Double-Precision FP Values 
* **CVTPD2DQ**—Convert Packed Double-Precision FP Values to Packed Dword Integers 
* **CVTPD2PS**—Convert Packed Double-Precision FP Values to Packed Single-Precision FP Values 
* **CVTPS2PD**—Convert Packed Single-Precision FP Values to Packed Double-Precision FP Values 
* **CVTSD2SI**—Convert Scalar Double-Precision FP Value to Integer 
* **CVTSI2SD**—Convert Dword Integer to Scalar Double-Precision FP Value 
* **CVTSI2SS**—Convert Dword Integer to Scalar Single-Precision FP Value 
* **CVTSS2SI**—Convert Scalar Single-Precision FP Value to Dword Integer 
* **CVTTPD2DQ**—Convert with Truncation Packed Double-Precision FP Values to Packed Dword 
* **CVTTSD2SI**—Convert with Truncation Scalar Double-Precision FP Value to Signed Integer 
* **CVTTSS2SI**—Convert with Truncation Scalar Single-Precision FP Value to Dword Integer 
* **FADD/FADDP/FIADD**—Add 
* **FDIV/FDIVP/FIDIV**—Divide 
* **FDIVR/FDIVRP/FIDIVR**—Reverse Divide 
* **FIST/FISTP**—Store Integer 
* **FXSAVE**—Save x87 FPU, MMX Technology, and SSE State 
* **HADDPD**—Packed Double-FP Horizontal Add 
* **HADDPS**—Packed Single-FP Horizontal Add 
* **HSUBPD**—Packed Double-FP Horizontal Subtract 
* **HSUBPS**—Packed Single-FP Horizontal Subtract 
* **INVPCID**—Invalidate Process-Context Identifier 
* **MOVDDUP**—Move One Double-FP and Duplicate 
* **MOVSHDUP**—Move Packed Single-FP High and Duplicate 
* **MOVSLDUP**—Move Packed Single-FP Low and Duplicate 
* **MPSADBW**—Compute Multiple Packed Sums of Absolute Difference 
* **PACKSSWB/PACKSSDW**—Pack with Signed Saturation 
* **PALIGNR**—Packed Align Right 
* **PCLMULQDQ**—Carry-Less Multiplication Quadword 
* **PDEP**—Parallel Bits Deposit 
* **PEXT**—Parallel Bits Extract 
* **PHADDW/PHADDD**—Packed Horizontal Add 
* **PMADDWD**—Multiply and Add Packed Integers 
* **PMULHUW**—Multiply Packed Unsigned Integers and Store High Result 
* **PMULLW**—Multiply Packed Signed Integers and Store Low Result 
* **POPF/POPFD/POPFQ**—Pop Stack into EFLAGS Register 
* **PSADBW**—Compute Sum of Absolute Differences 
* **PSHUFD**—Shuffle Packed Doublewords 
* **PSLLW/PSLLD/PSLLQ**—Shift Packed Data Left Logical 
* **PSRAW/PSRAD**—Shift Packed Data Right Arithmetic 
* **PSRLW/PSRLD/PSRLQ**—Shift Packed Data Right Logical 
* **PUNPCKHBW/PUNPCKHWD/PUNPCKHDQ/PUNPCKHQDQ**— Unpack High Data 
* **PUNPCKLBW/PUNPCKLWD/PUNPCKLDQ/PUNPCKLQDQ**—Unpack Low Data 
* **ROUNDPD**—Round Packed Double Precision Floating-Point Values 
* **SARX/SHLX/SHRX**—Shift Without Affecting Flags 
* **SHUFPD**—Shuffle Packed Double-Precision Floating-Point Values 
* **SHUFPS**—Shuffle Packed Single-Precision Floating-Point Values 
* **UNPCKHPD**—Unpack and Interleave High Packed Double-Precision Floating-Point Values 
* **UNPCKHPS**—Unpack and Interleave High Packed Single-Precision Floating-Point Values 
* **UNPCKLPD**—Unpack and Interleave Low Packed Double-Precision Floating-Point Values 
* **UNPCKLPS**—Unpack and Interleave Low Packed Single-Precision Floating-Point Values 
* **VBROADCAST**—Broadcast Floating-Point Data 
* **VCVTPH2PS**—Convert 16-bit FP Values to Single-Precision FP Values 
* **VCVTPS2PH**—Convert Single-Precision FP value to 16-bit FP value 
* **VPBROADCAST**—Broadcast Integer Data 
* **VPERM2I128**—Permute Integer Values 
* **VPERMILPD**—Permute Double-Precision Floating-Point Values 
* **VPERMILPS**—Permute Single-Precision Floating-Point Values 
* **VPERM2F128**—Permute Floating-Point Values 
* **XACQUIRE/XRELEASE**—Hardware Lock Elision Prefix Hints 

Most fail because of one of these reasons:

* the page contains a framed figure and the script freaks out;
* the page contains a frameless figure and the script freaks out;
* the page contains framed and frameless figures and the script freaks out;
* something's amiss with how rectangles are merged;
* some table lines are abnormally thick;
* some tables seem to be all right but the script still freaks out.

I'm working on that.

  [1]: http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf
  [2]: http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2b-manual.pdf
  [3]: http://www.unixuser.org/~euske/python/pdfminer/
  [4]: http://www.felixcloutier.com/x86/
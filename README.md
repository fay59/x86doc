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

As of now, these are the 13 instructions that do not parse at all. Most of them
fail because they contain a frameless figure. The list is:

* **CVTDQ2PD**—Convert Packed Dword Integers to Packed Double-Precision FP Values
* **CVTPS2PD**—Convert Packed Single-Precision FP Values to Packed Double-Precision FP Values
* **HADDPD**—Packed Double-FP Horizontal Add
* **HADDPS**—Packed Single-FP Horizontal Add
* **HSUBPD**—Packed Double-FP Horizontal Subtract
* **HSUBPS**—Packed Single-FP Horizontal Subtract
* **PDEP**—Parallel Bits Deposit
* **PEXT**—Parallel Bits Extract
* **PSADBW**—Compute Sum of Absolute Differences
* **VBROADCAST**—Broadcast Floating-Point Data
* **VPBROADCAST**—Broadcast Integer Data
* **VPERM2I128**—Permute Integer Values
* **VPERMILPD**—Permute Double-Precision Floating-Point Values
* **VPERM2F128**—Permute Floating-Point Values

I'm working on that.

  [1]: http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf
  [2]: http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2b-manual.pdf
  [3]: http://www.unixuser.org/~euske/python/pdfminer/
  [4]: http://www.felixcloutier.com/x86/
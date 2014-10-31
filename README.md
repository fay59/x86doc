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

*This branch is experimental.* Right now, it doesn't produce any useful output.
However, it is expected to eventually do, and that output will be of much better
quality than the crappy converter/BeautifulSoup combo. Be sure to check out the
`master` branch if you want the final result.

The current documentation set can be found on [this page][4].

  [1]: http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf
  [2]: http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2b-manual.pdf
  [3]: http://www.unixuser.org/~euske/python/pdfminer/
  [4]: http://www.felixcloutier.com/x86/
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

This is still not perfect, but it's already much better than the other solution
(and it doesn't involve an ugly third-party).

How To Run
----------

1. Install [`pdfminer`][3];
2. Get yourself a copy of the [Volume A][1] and [Volume B][2] PDFs.
3. `pdfminer` doesn't understand how these are encrypted, so print them to PDF,
	both starting only from the first instruction in the document (not the whole
	document);
4. Run `python extract.py vol2a.pdf vol2b.pdf`;
5. Go grab a coffee;
6. Enjoy your documentation set.

The set is also available online at [felixcloutier.com/x86][4].

  [1]: http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf
  [2]: http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2b-manual.pdf
  [3]: http://www.unixuser.org/~euske/python/pdfminer/
  [4]: http://www.felixcloutier.com/x86/
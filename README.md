x86doc
======

I needed a parsable copy of Intel's x86 instruction set documentation for a
personal project, so I downloaded volumes 2A and 2B of the *Intel® 64 and IA-32
Architectures Software Developer's Manual* (which can be found [here][1] and
[here][2], respectively), and used a online PDF-to-HTML tool to transform them
to HTML files.

The result was beyond terrible.

To fix that, I made a Python script with BeautifulSoup to extract in bulk the
documentation for each instruction and write it to cleaner HTML files. There are
still some issues, especially with lists:

* Nested lists are broken
* Lists sometimes appear as tables (and when it does, all hell breaks lose as
	far as layout is concerned);
* Figures simply can't be translated correctly.

Even then, this is significantly more useful, so I'm publishing it in case
anyone needs it. Most of what's missing will probably have to be dealt with
manually.

  [1]: http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf
  [2]: http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2b-manual.pdf
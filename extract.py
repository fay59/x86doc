#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
from x86manual import x86ManParser

def main(argv):
	for arg in argv[1:]:
		fd = open(arg)
		parser = PDFParser(fd)
		document = PDFDocument(parser)
		if not document.is_extractable:
			print "Document not extractable."
			return 1
	
		params = LAParams(char_margin=1)
		resMan = PDFResourceManager(caching=True)
		device = PDFPageAggregator(resMan, laparams=params)
		interpreter = PDFPageInterpreter(resMan, device)
		parser = x86ManParser("html", params)
	
		i = 1
		for page in PDFPage.get_pages(fd, set(), caching=True, check_extractable=True):
			print "Processing page %i" % i
			interpreter.process_page(page)
			page = device.get_result()
			parser.process_page(page)
			i += 1
		parser.flush()
		fd.close()
	
		print "Conversion result: %i/%i" % (parser.success, parser.success + parser.fail)

if __name__ == "__main__":
	result = main(sys.argv)
	sys.exit(result)
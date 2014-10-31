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
	fd = open(argv[1])
	parser = PDFParser(fd)
	document = PDFDocument(parser)
	if not document.is_extractable:
		print "Document not extractable."
		return 1
	
	params = LAParams()
	resMan = PDFResourceManager(caching=True)
	device = PDFPageAggregator(resMan, laparams=params)
	interpreter = PDFPageInterpreter(resMan, device)
	parser = x86ManParser("html", params)
	for page in PDFPage.get_pages(fd, set(), caching=True, check_extractable=True):
		interpreter.process_page(page)
		page = device.get_result()
		parser.process_page(page)
	parser.flush()
	fd.close()

if __name__ == "__main__":
	result = main(sys.argv)
	sys.exit(result)
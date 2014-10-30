#!/usr/bin/env python
from pdfminer.layout import *
import pdftable
import sys
import math

class AttributedText(object):
	def __init__(self, text, font, size):
		self.text = text
		self.font = font
		self.size = size
		pass

class AttributedParagraph(object):
	def __init(self):
		self.nodes = []
	
	def push(self, char, font, size):
		if len(self.nodes) > 0:
			last = self.nodes[-1]
			if last.font == font and last.size == size:
				last.text += char
				return
		
		self.nodes.append(AttributedText(text, font, size))

class x86ManParser(object):
	def __init__(self, outputDir, laParams):
		self.outputDir = outputDir
		self.laParams = laParams
	
	def process_item(self, item, n=0):
		print "%s%s" % (" " * n, item)
		if isinstance(item, LTContainer):
			for obj in item:
				self.process_item(obj, n+1)
	
	def process_page(self, page):
		for item in page:
			self.process_item(item)
		sys.exit(0)

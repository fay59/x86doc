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

class CharCollection(object):
	def __init__(self, rect, iterable):
		self.rect = rect
		self.chars = [c for c in iterable]

class x86ManParser(object):
	def __init__(self, outputDir, laParams):
		self.outputDir = outputDir
		self.laParams = laParams
		self.pageHeight = 800 # evil hardcoded value
		self.yBase = 0
		
		self.ltRects = []
		self.textLines = []
		self.thisPageLtRects = []
		self.thisPageTextLines = []
	
	def flush(self):
		tables = []
		while len(self.ltRects) > 0:
			table = pdftable.cluster_rects(self.ltRects)
			tables.append(table)
		
		print tables
		print self.textLines
		print
		
		self.ltRects = []
		self.textLines = []
	
	def begin_page(self):
		pass
	
	def end_page(self):
		if len(self.thisPageTextLines) > 0:
			firstChar = self.thisPageTextLines[0].chars[0]
			if firstChar.fontname.endswith("NeoSansIntel") and firstChar.matrix[0] >= 12:
				self.flush()
		self.ltRects += self.thisPageLtRects
		self.textLines += self.thisPageTextLines
	
	def process_text_line(self, line):
		# ignore header and footer
		if line.bbox[1] < 740 and line.bbox[1] > 50:
			rect = self.__fix_bbox(line.bbox)
			self.thisPageTextLines.append(CharCollection(rect, line))
	
	def process_rect(self, rect):
		self.thisPageLtRects.append(self.__fix_bbox(rect.bbox))
	
	def process_item(self, item, n=0):
		if isinstance(item, LTTextLineHorizontal):
			self.process_text_line(item)
		elif isinstance(item, LTRect):
			self.process_rect(item)
		elif isinstance(item, LTContainer):
			for obj in item:
				self.process_item(obj, n+1)
	
	def process_page(self, page):
		self.begin_page()
		for item in page:
			self.process_item(item)
		self.end_page()
	
	def __fix_bbox(self, bbox):
		x1 = bbox[0]
		y1 = self.yBase + self.pageHeight - bbox[1]
		x2 = bbox[2]
		y2 = self.yBase + self.pageHeight - bbox[3]
		return pdftable.Rect(x1, y1, x2, y2)

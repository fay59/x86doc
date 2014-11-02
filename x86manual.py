#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from pdfminer.layout import *
import pdftable
import sys
import math

def escape_html(a):
	return a.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

def sort_topdown_ltr(a, b):
	aa = a.bounds()
	bb = b.bounds()
	if aa.y1() < bb.y1(): return -1
	if aa.y1() > bb.y1(): return 1
	if aa.x1() < bb.x1(): return -1
	if aa.x1() > bb.x1(): return 1
	return 0

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

class FakeChar(object):
	def __init__(self, t):
		self.text = t
	
	def get_text(self):
		return self.text

class CharCollection(object):
	def __init__(self, rect, iterable):
		self.rect = rect
		self.chars = [c for c in iterable]
		while len(self.chars[-1].get_text().strip()) == 0:
			self.chars.pop()
	
	def bounds(self): return self.rect
	
	def append(self, line):
		self.rect = self.rect.union(line.rect)
		self.chars += line.chars
		while len(self.chars[-1].get_text().strip()) == 0:
			self.chars.pop()
	
	def append_char(self, c):
		aChar = self.chars[0]
		self.chars.append(FakeChar(c))
	
	def font_name(self):
		return self.chars[0].fontname
	
	def font_size(self):
		return self.chars[0].matrix[0]
	
	def __str__(self):
		uni = u"".join([c.get_text() for c in self.chars])
		if uni[-1] != "-" and uni[-1] != "/":
			uni += " "
		return uni
	
	def __repr__(self):
		return u"<%r text=%r>" % (self.rect, unicode(self))

class x86ManParser(object):
	def __init__(self, outputDir, laParams):
		self.outputDir = outputDir
		self.laParams = laParams
		self.yBase = 0
		
		self.ltRects = []
		self.textLines = []
		self.thisPageLtRects = []
		self.thisPageTextLines = []
	
	def flush(self):
		tables = []
		while len(self.ltRects) > 0:
			cluster = pdftable.cluster_rects(self.ltRects)
			if len(cluster) >= 4:
				tables.append(pdftable.Table(cluster))
		
		# fill tables
		lines = self.textLines
		for table in tables:
			orphans = []
			bounds = table.bounds()
			for line in lines:
				if bounds.intersects(line.rect, 0):
					table.get_at_pixel(line.rect.xmid(), line.rect.ymid()).append(line)
				else:
					orphans.append(line)
			lines = orphans
		
		for i in xrange(0, len(tables)):
			table = tables[i]
			if table.rows() == 1 and table.columns() == 1:
				if len(table.get_at_pixel(0, 0)) != 0:
					tables[i] = table.separate_from_contents(CharCollection.bounds)
		
		displayable = self.__merge_text(orphans) + tables
		displayable.sort(cmp=sort_topdown_ltr)
		self.__output_file(displayable)
		
		self.ltRects = []
		self.textLines = []
	
	def begin_page(self, page):
		self.yBase += page.bbox[3] - page.bbox[1]
	
	def end_page(self, page):
		if len(self.thisPageTextLines) > 0:
			firstLine = self.thisPageTextLines[0]
			if firstLine.font_name().endswith("NeoSansIntel") and firstLine.font_size() >= 12:
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
		self.begin_page(page)
		for item in page:
			self.process_item(item)
		self.end_page(page)
	
	def __fix_bbox(self, bbox):
		x1 = bbox[0]
		y1 = self.yBase - bbox[1]
		x2 = bbox[2]
		y2 = self.yBase - bbox[3]
		return pdftable.Rect(x1, y2, x2, y1)
	
	def __merge_text(self, lines):
		def sort_text(a, b):
			if a.rect.x1() < b.rect.x1():
				return -1
			if a.rect.x1() == b.rect.x1():
				if a.rect.y1() < b.rect.y1():
					return -1
				if a.rect.y1() == b.rect.y1():
					return 1
				return 0
			return 1
		
		if len(lines) == 0: return
		
		lines.sort(cmp=sort_text)
		merged = [lines[0]]
		for line in lines[1:]:
			last = merged[-1]
			same_x = pdftable.pretty_much_equal(line.rect.x1(), last.rect.x1())
			same_font = last.font_name() == line.font_name()
			same_size = last.font_size() == line.font_size()
			decent_descent = line.rect.y1() - last.rect.y2() < 5
			if same_x and same_font and same_size and decent_descent:
				lastChar = last.chars[-1].get_text()[-1]
				if not (lastChar == "-" or lastChar == "/"):
					last.append_char(" ")
				last.append(line)
			else:
				merged.append(line)
		return merged
	
	def __output_file(self, displayable):
		title = [p.strip() for p in unicode(displayable[0]).split(u"—")][0]
		path = "%s/%s.html" % (self.outputDir, title.replace("/", ":"))
		with open(path, "w") as fd:
			fd.write(self.__output_page(displayable).encode("UTF-8"))
	
	def __output_page(self, displayable):
		title = unicode(displayable[0])
		result = [""]
		def write_line(line): result[0] += line + "\n"
		write_line("<!DOCTYPE hmtl>")
		write_line("<html>")
		write_line("<head>")
		write_line('<meta charset="UTF-8">')
		write_line("<title>%s</title>" % escape_html(title))
		write_line("</head>")
		write_line("<body>")
		for element in displayable:
			result[0] += self.__output_html(element)
		write_line("</body>")
		write_line("</html>")
		return result[0]
	
	def __output_html(self, element):
		result = ""
		if isinstance(element, list):
			return "".join([unicode(e) for e in element])
		if isinstance(element, CharCollection):
			# TODO fonts and stuff
			result = unicode(element)
		elif isinstance(element, pdftable.Table):
			result += "<table>\n"
			for row in xrange(0, element.rows()):
				result += "<tr>\n"
				for col in xrange(0, element.columns()):
					result += "<td>"
					sub = element.get_at(col, row)
					result += self.__output_html(sub)
					result += "</td>\n"
				result += "</tr>\n"
			result += "</table>\n"
		return result

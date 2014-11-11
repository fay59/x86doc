#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from pdfminer.layout import *
import pdftable
import sys
import math
import bisect

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

def __fix_table(contents, bounds, rows, columns):
	rects = [pdftable.Rect(col, bounds.y1(), col, bounds.y2()) for col in columns]
	rects += [pdftable.Rect(bounds.x1(), row, bounds.x2(), row) for row in rows]
	table = pdftable.Table(rects)
	for item in contents:
		bounds = item.bounds()
		table.get_at_pixel(bounds.xmid(), bounds.ymid()).append(item)
	return table

def center_aligned_table(table):
	assert table.rows() == 1 and table.columns() == 1
	bounds = table.bounds()
	contents = table.get_at(0, 0)[:]
	contents.sort(cmp=sort_topdown_ltr)
	columns = [bounds.x1()]
	y0 = contents[0].bounds().y1()
	for i in xrange(0, len(contents) - 1):
		item = contents[i]
		next_item = contents[i+1]
		if not pdftable.pretty_much_equal(y0, next_item.bounds().y1()): break
		columns.append((item.bounds().x2() + next_item.bounds().x1()) / 2)
	columns.append(bounds.x2())
	
	ys = set()
	for item in contents:
		hundreds = round(item.bounds.ymid() * 100)
		ys.add(hundreds.add)
	
	rows = [bounds.y1()]
	ys = list(ys)
	ys.sort()
	i = 1
	while i != len(ys):
		if not pdftable.pretty_much_equal(ys[i], ys[i-1]):
			rows.append((ys[i] + ys[i-1]) / 2)
	rows.append(bounds.y2())
	
	return __fix_table(contents, bounds, rows, columns)

def left_aligned_table(source):
	assert source.rows() == 1 and source.columns() == 1
	bounds = source.bounds()
	contents = source.get_at(0, 0)[:]
	contents.sort(cmp=sort_topdown_ltr)
	
	table = []
	row = []
	columns = []
	last_y = contents[0].bounds().y1()
	for item in contents:
		item_bounds = item.bounds()
		if not pdftable.pretty_much_equal(item_bounds.y1(), last_y):
			break
		columns.append(item_bounds.x1())
	
	last_y = contents[0].bounds().y1()
	row = [[]] * len(columns)
	for item in contents:
		item_bounds = item.bounds()
		if not pdftable.pretty_much_equal(item_bounds.y1(), last_y):
			if any((len(c) == 0 for c in row)):
				for i in xrange(0, len(columns)):
					table[-1][i] += row[i]
			else: table.append(row)
			row = [[]] * len(columns)
			last_y = item_bounds.y1()
		
		for i in xrange(0, len(columns)):
			if pdftable.pretty_much_equal(item_bounds.x1(), columns[i]):
				col_index = i
				break
		else: raise Exception("No matching column!")
		
		row[col_index] = [item]
	
	if any((len(c) == 0 for c in row)):
		for i in xrange(0, len(columns)):
			table[-1][i] += row[i]
	else: table.append(row)
	
	return pdftable.ImplicitTable(bounds, table)

class FakeChar(object):
	def __init__(self, t):
		self.text = t
	
	def get_text(self):
		return self.text

class CharCollection(object):
	def __init__(self, rect, iterable):
		self.rect = rect
		self.chars = [c for c in iterable]
		while len(self.chars) > 0 and len(self.chars[-1].get_text().strip()) == 0:
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
		return self.chars[0].fontname[7:] if len(self.chars) != 0 else ""
	
	def font_size(self):
		return self.chars[0].matrix[0] if len(self.chars) != 0 else 0
	
	def __str__(self):
		uni = u"".join([c.get_text() for c in self.chars])
		if len(uni) > 0 and uni[-1] != "-" and uni[-1] != "/":
			uni += " "
		return uni
	
	def __repr__(self):
		return u"<%r text=%r>" % (self.rect, unicode(self))

class x86ManParser(object):
	def __init__(self, outputDir, laParams):
		self.outputDir = outputDir
		self.laParams = laParams
		self.yBase = 0
		self.success = 0
		self.fail = 0
		
		self.ltRects = []
		self.textLines = []
		self.thisPageLtRects = []
		self.thisPageTextLines = []
		self.__title_stack = []
	
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
		
		displayable = self.__merge_text(orphans) + tables
		displayable.sort(cmp=sort_topdown_ltr)
		
		self.__output_file(displayable)
	
	def begin_page(self, page):
		self.thisPageLtRects = []
		self.thisPageTextLines = []
		self.yBase += page.bbox[3] - page.bbox[1]
	
	def end_page(self, page):
		if len(self.thisPageTextLines) > 0:
			firstLine = self.thisPageTextLines[0]
			if firstLine.font_name() == "NeoSansIntelMedium" and firstLine.font_size() >= 12:
				if len(self.ltRects) > 0 or len(self.textLines) > 0:
					try:
						self.flush()
						self.success += 1
					except:
						print "*** couldn't flush to disk"
						self.fail += 1
		
					self.ltRects = []
					self.textLines = []
		
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
			if pdftable.pretty_much_equal(a.rect.x1(), b.rect.x1()):
				if a.rect.y1() < b.rect.y1():
					return -1
				if a.rect.y1() == b.rect.y1():
					return 1
				return 0
			if a.rect.x1() < b.rect.x1():
				return -1
			return 1
		
		if len(lines) == 0: return
		
		lines.sort(cmp=sort_text)
		merged = [lines[0]]
		for line in lines[1:]:
			last = merged[-1]
			same_x = pdftable.pretty_much_equal(line.rect.x1(), last.rect.x1())
			same_font = last.font_name() == line.font_name()
			same_size = last.font_size() == line.font_size()
			decent_descent = line.rect.y1() - last.rect.y2() < 2.5
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
		print "Writing to %s" % path
		file_data = self.__output_page(displayable).encode("UTF-8")
		with open(path, "w") as fd:
			fd.write(file_data)
	
	def __output_page(self, displayable):
		title = unicode(displayable[0])
		result = [""]
		def write_line(line): result[0] += line + "\n"
		write_line("<!DOCTYPE hmtl>")
		write_line("<html>")
		write_line("<head>")
		write_line('<meta charset="UTF-8">')
		write_line('<link rel="stylesheet" type="text/css" href="style.css">')
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
			result = self.__output_text(element)
		elif isinstance(element, pdftable.Table):
			print_index = -1
			if element.rows() == 1 and element.columns() == 1:				
				if len(self.__title_stack) == 1:
					# instruction table
					element = left_aligned_table(element)
				elif len(self.__title_stack) == 2 and self.__title_stack[1].lower() == "instruction operand encoding":
					element = center_aligned_table(element)
			
			result += "<table>\n"
			for row in xrange(0, element.rows()):
				result += "<tr>\n"
				for col in xrange(0, element.columns()):
					index = element.data_index(col, row)
					if index <= print_index: continue
					index = print_index
					
					size = element.cell_size(col, row)
					colspan = (' colspan="%i"' % size[0]) if size[0] > 1 else ""
					rowspan = (' rowspan="%i"' % size[1]) if size[1] > 1 else ""
					result += "<td%s%s>" % (colspan, rowspan)
					children = self.__merge_text(element.get_at(col, row))
					if children != None:
						if len(children) == 1:
							result += self.__output_html(children[0])
						else:
							for child in children:
								result += "<p>%s</p>\n" % self.__output_html(child)
					result += "</td>\n"
				result += "</tr>\n"
			result += "</table>\n"
		return result
	
	def __output_text(self, element):
		bold = False
		italic = False
		superscript = False
		
		stack_index = None
		tag = u"p"
		if element.font_name() == "NeoSansIntelMedium":
			if element.font_size() >= 12:
				tag = "h1"
				stack_index = 0
			elif element.font_size() >= 9.9:
				if element.bounds().x1() < 50:
					tag = "h2"
					stack_index = 1
				else:
					tag = "h3"
					stack_index = 2
			else:
				bold = True
		
		self.__title_stack = self.__title_stack[:stack_index]
		self.__title_stack.append(unicode(element))
		
		result = "<%s>" % tag
		if bold: result += "<strong>"
		if italic: result += "<em>"
		if superscript: result += "<sup>"
		
		# TODO style transitions
		result += unicode(element).strip()
		
		if superscript: result += "</sup>"
		if italic: result += "</em>"
		if bold: result += "</strong>"
		result += "</%s>" % tag
		return result

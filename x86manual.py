#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from pdfminer.layout import *
import pdftable
from htmltext import *
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

class TableDataSet(pdftable.TableBase):
	def __init__(self, data):
		self.__data = data
		self.__bounds = data[0].bounds()
		for r in self.__data:
			self.__bounds = self.__bounds.union(r.bounds())
	
	def rows(self): return 1
	def columns(self): return 1
	def bounds(self): return self.__bounds
	def get_at(self, x, y):
		assert x == 0 and y == 0
		return self.__data[:]

def center_aligned_table(source):
	assert source.rows() == 1 and source.columns() == 1
	bounds = source.bounds()
	contents = source.get_at(0, 0)[:]
	contents.sort(cmp=sort_topdown_ltr)
	column_centers = []
	last_y = contents[0].bounds().y1()
	for item in contents:
		if not pdftable.pretty_much_equal(last_y, item.bounds().y1()): break
		column_centers.append(item.bounds().xmid())
	
	table = []
	row = [[]] * len(column_centers)
	for item in contents:
		item_bounds = item.bounds()
		if not pdftable.pretty_much_equal(item_bounds.y1(), last_y):
			if any((len(c) == 0 for c in row)):
				for i in xrange(0, len(column_centers)):
					table[-1][i] += row[i]
			else: table.append(row)
			row = [[]] * len(column_centers)
			last_y = item_bounds.y1()
		
		col_index = None
		min_dist = float("inf")
		for i in xrange(0, len(column_centers)):
			distance = abs(item_bounds.xmid() - column_centers[i])
			if distance < min_dist:
				min_dist = distance
				col_index = i
		
		row[col_index] = [item]
	
	if any((len(c) == 0 for c in row)):
		for i in xrange(0, len(column_centers)):
			table[-1][i] += row[i]
	else: table.append(row)
	
	return pdftable.ImplicitTable(bounds, table)

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
		else:
			print columns
			raise Exception("No matching column!")
		
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
	def __init__(self, iterable, rect):
		self.chars = [c for c in iterable]
		while len(self.chars) > 0 and len(self.chars[-1].get_text().strip()) == 0:
			self.chars.pop()
		
		# actual, complete bounds (modified by caller)
		self.rect = rect
		# bounds excluding abnormally-placed characters (exponents, symbols)
		self.approx_rect = self.__approximative_bounds()
	
	def bounds(self): return self.approx_rect
	
	def __approximative_bounds(self):
		if len(self.chars) == 0: return self.rect
		size = self.font_size()
		approx = None
		for c in self.chars:
			if hasattr(c, "matrix") and c.matrix[0] == size:
				rect = pdftable.Rect(c.x0, c.y1, c.x1, c.y0)
				if approx == None: approx = rect
				elif approx.y1() == rect.y1(): approx = approx.union(rect)
		return approx
	
	def append(self, line):
		self.rect = self.rect.union(line.rect)
		self.approx_rect = self.approx_rect.union(line.approx_rect)
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
		self.__is_code = False
	
	def flush(self):
		tables = []
		while len(self.ltRects) > 0:
			cluster = pdftable.cluster_rects(self.ltRects)
			if len(cluster) >= 4:
				tables.append(pdftable.Table(cluster))
		
		assert len(tables) > 0
		# explicit tables
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
		
		# exception tables
		lines.sort(cmp=sort_topdown_ltr)
		orphans = []
		table_data = []
		is_exc_section = False
		for line in lines:
			if line.font_name() == "NeoSansIntelMedium":
				orphans.append(line)
				is_exc_section = unicode(line).strip().lower()[-10:] == "exceptions"
				if len(table_data) > 0:
					tables.append(TableDataSet(table_data))
					table_data = []
				continue
			
			if is_exc_section:
				if line.bounds().x1() < 50 and line.chars[0].get_text() != '#':
					orphans.append(line)
					if len(table_data) > 0:
						tables.append(TableDataSet(table_data))
						table_data = []
				else:
					table_data.append(line)
			else:
				orphans.append(line)
		
		if len(table_data) > 0:
			tables.append(TableDataSet(table_data))
		
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
					# convenience: if we're debugging, let an exception crash
					# the script
					if __debug__:
						self.flush()
						self.success += 1
					else:
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
			coll = CharCollection(line, self.__fix_bbox(line.bbox))
			coll.approx_rect = self.__fix_rect(coll.approx_rect)
			self.thisPageTextLines.append(coll)
	
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
	
	def __fix_rect(self, r):
		return pdftable.Rect(r.x1(), self.yBase - r.y1(), r.x2(), self.yBase - r.y2())
	
	def __fix_bbox(self, bbox):
		return self.__fix_rect(pdftable.Rect(bbox[0], bbox[3], bbox[2], bbox[1]))
	
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
		
		lines.sort(cmp=sort_topdown_ltr)
		merged = [lines[0]]
		for line in lines[1:]:
			last = merged[-1]
			same_x = pdftable.pretty_much_equal(line.rect.x1(), last.rect.x1())
			same_size = last.font_size() == line.font_size()
			decent_descent = line.approx_rect.y1() - last.approx_rect.y2() < 1.2
			if same_x and same_size and decent_descent:
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
		text = HtmlText()
		text.append(OpenTag("html"))
		text.append(OpenTag("head"))
		text.append(OpenTag("meta", attributes={"charset": "UTF-8"}, self_closes=True))
		text.append(OpenTag("link", attributes={"rel": "stylesheet", "type": "text/css", "href": "style.css"}, self_closes=True))
		text.append(OpenTag("title"))
		text.append(title)
		text.append(CloseTag("title"))
		text.append(CloseTag("head"))
		text.append(OpenTag("body"))
		
		for element in displayable:
			text.append(self.__output_html(element))
		
		return "<!DOCTYPE html>" + text.to_html()
	
	def __output_html(self, element):
		if isinstance(element, list):
			result = HtmlText()
			for e in element:
				result.append(unicode(e))
			return result
		
		if isinstance(element, CharCollection):
			result = self.__output_text(element)
			if result.tokens[0].tag[0] == "h":
				level = int(result.tokens[0].tag[1]) - 1
				self.__title_stack = self.__title_stack[0:level]
				self.__title_stack.append(u"".join(result.tokens[1:-1]).strip().lower())
			return result
		
		if isinstance(element, pdftable.TableBase):
			result = HtmlText()
			print_index = -1
			attributes = {}
			if element.rows() == 1 and element.columns() == 1:
				if len(self.__title_stack) == 1:
					# instruction table
					element = left_aligned_table(element)
				else:
					heading = self.__title_stack[-1]
					if heading == "instruction operand encoding":
						# operands encoding
						element = center_aligned_table(element)
					elif heading[-10:] == "exceptions":
						# exception table
						element = left_aligned_table(element)
						attributes["class"] = "exception-table"
			
			result.append(OpenTag("table", attributes=attributes))
			for row in xrange(0, element.rows()):
				result.append(OpenTag("tr"))
				for col in xrange(0, element.columns()):
					index = element.data_index(col, row)
					if index <= print_index: continue
					index = print_index
					
					cell_tag = "td"
					contents = HtmlText()
					children = self.__merge_text(element.get_at(col, row))
					if children != None:
						if len(children) == 1:
							contents = self.__output_text(children[0])
							if contents.tokens[0].tag != "p":
								contents.tokens = contents.tokens[1:-1]
								cell_tag = "th"
							else:
								tok = contents.tokens[1]
								if hasattr(tok, "tag") and tok.tag == "strong":
									contents.tokens = contents.tokens[2:-2]
									cell_tag = "th"
								else:
									contents.tokens = contents.tokens[1:-1]
						else:
							for child in children:
								contents.append(self.__output_html(child))
					
					attributes = {}
					size = element.cell_size(col, row)
					if size[0] > 1: attributes["colspan"] = size[0]
					if size[1] > 1: attributes["rowspan"] = size[1]
					result.append(OpenTag(cell_tag, attributes=attributes))
					result.append(contents)
					result.append(CloseTag(cell_tag))
				result.append(CloseTag("tr"))
			result.append(CloseTag("table"))
			return result
		
		assert False
		return HtmlText()
	
	def __output_text(self, element):
		if len(element.chars) == 0: return ""
		
		style = [element.chars[0].fontname, element.chars[0].matrix[0:4]]
		text = HtmlText()
		# what kind of text block is this?
		open = OpenTag("p")
		strong = False
		if element.font_name() == "NeoSansIntelMedium":
			if element.font_size() >= 12: open.tag = "h1"
			elif element.font_size() >= 9.9:
				if element.bounds().x1() < 50: open.tag = "h2"
				else: open.tag = "h3"
			else:
				strong = True
		elif element.font_name() == "NeoSansIntel" and self.__title_stack[-1] == "operation":
			open = OpenTag("pre", True)
			indent = int((element.bounds().x1() - 45) / 3.375)
			element.chars = [FakeChar(' ')] * indent + element.chars
		
		text.append(open)
		if strong: text.append(OpenTag("strong"))
		if style[0].find("Italic") != -1: text.append(OpenTag("em"))
		
		for char in element.chars:
			if hasattr(char, "fontname") and hasattr(char, "matrix"):
				this_style = [char.fontname, char.matrix[0:4]]
				if this_style != style and this_style[0].find("Symbol") == -1:
					this_italic = this_style[0].find("Italic") != -1
					if this_italic != (style[0].find("Italic") != -1):
						if this_italic: text.append(OpenTag("em"))
						else: text.append(CloseTag("em"))
					
					# Intel inconsistently switches between Arial and Verdana
					# and uses different font sizes
					if this_style[0].find("Arial") == -1 and style[0].find("Arial") == -1:
						if this_style[1][0] < style[1][0]:
							text.append(OpenTag("sup"))
						elif style[1][0] < this_style[1][0]:
							text.append(CloseTag("sup"))
					style = this_style
					
			text.append(char.get_text())
		text.autoclose()
		return text
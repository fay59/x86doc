# -*- coding: UTF-8 -*-
import re
import bs4
import sys
from StringIO import StringIO

# not my most efficient class
class AttributedString(object):
	bold = 1
	italic = 2
	underlined = 4
	subscript = 8
	superscript = 16
	
	@staticmethod
	def non(attribute):
		if attribute <= AttributedString.superscript:
			return attribute << 5
		else:
			return attribute >> 5
	
	def __init__(self, string="", attributes=None):
		self.value = string
		self.attributes = [0] * len(string) if attributes == None else attributes[:]
		assert len(self.value) == len(self.attributes)
	
	def add_attribute(self, begin, end, attribute):
		for i in xrange(begin, end):
			if self.attributes[i] & AttributedString.non(attribute) == 0:
				self.attributes[i] |= attribute
	
	def append(self, that):
		self.value += that.value
		self.attributes += that.attributes
	
	def split(self, position):
		left = AttributedString(self.value[:position], self.attributes[:position])
		right = AttributedString(self.value[position:], self.attributes[position:])
		return (left, right)
	
	def lstrip(self):
		stripped = self.value.lstrip()
		attributes = self.attributes[-len(stripped):]
		return AttributedString(stripped, attributes)
	
	def rstrip(self):
		stripped = self.value.rstrip()
		attributes = self.attributes[:len(stripped)]
		return AttributedString(stripped, attributes)
	
	def strip(self):
		return self.lstrip().rstrip()
	
	def __build_open_close_map(self):
		events = {}
		prev_attributes = 0
		tags = ['strong', 'em', 'u', 'sub', 'sup']
		for i in xrange(0, len(self.attributes)):
			attribute_bitmap = self.attributes[i] & 31
			difference = attribute_bitmap ^ prev_attributes
			opening = difference & attribute_bitmap
			closing = difference & prev_attributes
			j = 0
			while opening != 0:
				if opening & 1:
					tag = tags[j]
					if i not in events: events[i] = []
					events[i].append(tag)
				opening >>= 1
				j += 1
			
			j = 0
			while closing != 0:
				if closing & 1:
					tag = tags[j]
					if i not in events: events[i] = []
					events[i].append("/" + tag)
				closing >>= 1
				j += 1
			
			prev_attributes = attribute_bitmap
		
		j = 0
		i += 1
		closing = prev_attributes
		while closing != 0:
			if closing & 1:
				tag = tags[j]
				if i not in events: events[i] = []
				events[i].append("/" + tag)
			closing >>= 1
			j += 1
		return events
	
	def html(self):
		events = self.__build_open_close_map()
		event_keys = events.keys()
		event_keys.sort()
		
		html = ""
		tag_stack = []
		string_index = 0
		reopen_stack = []
		for key in event_keys:
			while len(reopen_stack) != 0:
				reopen = reopen_stack.pop()
				html += "<%s>" % reopen
				tag_stack.append(reopen)
		
			html += self.value[string_index:key]
			string_index = key
			tags = events[key]
			tags.sort()
		
			for tag in tags:
				if tag[0] == '/': # close
					tag = tag[1:]
					if tag in reopen_stack:
						del reopen_stack[reopen_stack.index(tag)]
					else:
						tag_to_close = tag_stack.pop()
						while tag_to_close != tag:
							html += "</%s>" % tag_to_close
							reopen_stack.append(tag_to_close)
							tag_to_close = tag_stack.pop()
					
						html += "</%s>" % tag
				else:
					html += "<%s>" % tag
					tag_stack.append(tag)

		html += self.value[string_index:]
		return html
	
	def __str__(self): return self.html()

class TextCell(object):
	def __init__(self, page, x, y, style, contents, x_approx = False):
		self.page = page
		self.style = style
		self.x = x
		self.x_approx = x_approx
		self.y = y
		self.contents = contents
	
	def __repr__(self):
		return ("%i: %s" % (self.x, self.contents.html())).encode("UTF-8")

class UglyDocument(object):
	def __init__(self, soup):
		self.__soup = soup
		self.__css = {}
		for tag, klass, style in re.findall(r"([a-z]+)\.([a-z0-9_]+){([^}]+)}", soup.style.text):
			if tag not in self.__css:
				self.__css[tag] = {}
			
			props = {}
			for prop in style.split(";"):
				key, value = self.__css_property(prop)
				props[key] = value
			self.__css[tag][klass] = props
	
	def __css_property(self, property):
		(key, value) = (v.strip() for v in property.split(":"))
		if key == "color":
			match = re.match(r"rgb\(([0-9]+),([0-9]+),([0-9]+)\)", value)
			return (key, [int(match.group(i)) for i in xrange(1, 4)])
		elif value.find(",") != -1:
			return (key, [v.strip() for v in value.split(",")])
		elif value[-2:] == "px":
			return (key, float(value[:-2]))
		else:
			return (key, value)
	
	def __tag_style(self, tag):
		tag_key = tag.name
		style = {}
		
		if tag_key in self.__css:
			classes = self.__css[tag_key]
			for klass in tag["class"]:
				for key in classes[klass]:
					style[key] = classes[klass][key]
		
		if tag.has_attr("style"):
			for prop in tag["style"].split(";"):
				key, value = self.__css_property(prop)
				style[key] = value
		
		return style
	
	def __all_divs(self):
		i = 0
		for page_div in soup.body.children:
			if not isinstance(page_div, bs4.Tag) or page_div.name != "div":
				continue
		
			children = page_div.findChildren("div")[:-3]
			slice_first = 1
			if len(children[0].text.strip()) == 0:
				slice_first += 1
			
			for child in children[slice_first:]:
				yield child
			yield "page-break"
	
	def __attributed_string(self, tag):
		new_string = AttributedString("")
		for child in tag.children:
			if isinstance(child, bs4.Tag):
				new_string.append(self.__attributed_string(child))
			else:
				assert isinstance(child, bs4.NavigableString)
				safe = unicode(child)
				for find, replace in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;")):
					safe = safe.replace(find, replace)
				new_string.append(AttributedString(safe))
		
		length = len(new_string.value)
		style = self.__tag_style(tag)
		
		if tag.name == "sup":
			new_string.add_attribute(0, length, AttributedString.superscript)
		elif tag.name == "sub":
			new_string.add_attribute(0, length, AttributedString.subscript)
		
		if "font-weight" in style:
			weight = style["font-weight"]
			if weight == "bold":
				new_string.add_attribute(0, length, AttributedString.bold)
			elif weight == "normal":
				new_string.add_attribute(0, length, AttributedString.non(AttributedString.bold))
				
		if "font-style" in style:
			style = style["font-style"]
			if style == "italic":
				new_string.add_attribute(0, length, AttributedString.italic)
			elif style == "normal":
				new_string.add_attribute(0, length, AttributedString.non(AttributedString.italic))
		
		return new_string
	
	def all_cells(self):
		bold = 1
		italic = 2
		underline = 4
		sub = 8
		sup = 16
		page = 0
		
		for div in self.__all_divs():
			if div == "page-break":
				page += 1
				continue
			
			style = self.__tag_style(div)
			x = style["left"]
			y = style["top"]
			
			text = self.__attributed_string(div)
			text_parts = []
			match = re.search(" {2,}", text.value)
			while match != None:
				left, right = text.split(match.end())
				text_parts.append(left)
				text = right
				match = re.search(" {2,}", text.value)
			text_parts.append(text)
			
			x_approx = False
			for part in text_parts:
				yield TextCell(page, x, y, style, part.strip(), x_approx)
				x += len(part.value) * style["font-size"] / 2 # approximation
				x_approx = True
	
	def all_rows(self):
		row = []
		last_y = 0
		last_page = 0
		for cell in self.all_cells():
			if cell.page != last_page or (abs(last_y - cell.y) > 3 and len(row) != 0):
				row.sort(lambda a, b: cmp(a.x - b.x, 0))
				yield row
				row = []
				last_page = cell.page
			row.append(cell)
			last_y = cell.y
		yield row

class DocumentWriter(object):
	def __init__(self):
		self.title = ""
		self.__output_mode = None # could be one of None, "p", "list", "code", "table"
		self.__output_mode_data = {}
		self.__output = StringIO()
		self.__spaced_chars = set([c for c in ".,;:)"])
	
	def write(self, row):
		if self.__output_mode == "p":
			if self.__break_p(row):
				text = self.__output_mode_data["contents"] 
				if self.__output_mode_data["color"] == [0,0,0]:
					css_class = ' class="%s"' % self.__output_mode_data["class"] if "class" in self.__output_mode_data else ""
					self.__output.write("<p%s>%s</p>\n" % (css_class, text.html()))
				else:
					text = text.value
					lowered = text.lower()
					if lowered != "notes:":
						if self.__output_mode_data["size"] > 12:
							self.title = text
							tag = "h1"
						elif re.search("^Table [0-9]+-[0-9]+\.", text):
							tag = "h3"
						else:
							tag = "h2"
						id = re.sub("[^a-z0-9]+", "-", lowered)
						self.__output.write('<%s id="%s">%s</%s>\n' % (tag, id, text, tag))
				
				self.__output_mode = None
				return self.write(row)
			
			for cell in row:
				self.__output_mode_data["contents"] = self.__append(self.__output_mode_data["contents"], cell.contents)
			self.__output_mode_data["top"] = row[-1].y
			return True
			
		elif self.__output_mode == "code":
			cell = row[0]
			if self.__is_title(cell):
				self.__output.write("</pre>\n")
				self.__output_mode = None
				return self.write(row)
				
			distance = cell.x - self.__output_mode_data["left"]
			self.__output.write(" " * int(round(distance / 6.75)))
			self.__output.write(cell.contents.html().replace(u"", u"←") + "\n")
			return True
			
		elif self.__output_mode == "list":
			if self.__break_list(row):
				if len(self.__output_mode_data["contents"].value) != 0:
					self.__output.write("\t<li>%s</li>\n" % self.__output_mode_data["contents"].html())
				self.__output.write("</ul>\n")
				self.__output_mode = None
				return self.write(row)
			
			if row[0].contents.value == u"•" and len(self.__output_mode_data["contents"].value) != 0:
				self.__output.write("\t<li>%s</li>\n" % self.__output_mode_data["contents"].html())
				self.__output_mode_data["contents"] = AttributedString("")
			
			for cell in row:
				if cell.contents.value == u"•": continue
				self.__output_mode_data["contents"] = self.__append(self.__output_mode_data["contents"], cell.contents)
			return True
			
		elif self.__output_mode == "table":
			if self.__break_table(row):
				self.__write_table()
				self.__output_mode = None
				return self.write(row)
			
			last_column = -1
			columns = self.__output_mode_data["columns"]
			table_row = [None for i in columns]
			self.__output_mode_data["row_top"].append(row[0].y)
			
			for cell in row:
				for i in xrange(last_column + 1, len(columns)):
					if columns[i] > cell.x:
						last_column = i - 1
						break
				else:
					last_column = len(columns) - 1
				
				if cell.x_approx and table_row[last_column] != None and last_column != len(table_row) - 1:
					last_column += 1
				
				table_row[last_column] = cell.contents
			
			self.__output_mode_data["row_data"].append(table_row)
			return True
			
		else:
			assert self.__output_mode == None
			# figure out output mode
			length = len(row)
			if length == 0: return False
			elif length == 1 or re.match(r"Table [0-9]+-[0-9]+\.", row[0].contents.value):
				cell = row[0]
				self.__output_mode = "p"
				self.__output_mode_data = {
					"top": cell.y,
					"left": cell.x,
					"contents": AttributedString(""),
					"color": cell.style["color"],
					"size": cell.style["font-size"],
				}
				
				if self.__output_mode_data["color"] != [0,0,0]:
					if self.__output_mode_data["size"] > 12:
						if len(self.title) != 0:
							self.__output_mode = None
							self.__output_mode_data = {}
							return False
					
					lowered = cell.contents.value.lower()
					# hacks!
					if lowered == "notes:":
						self.__output_mode_data["color"] = [0,0,0]
						self.__output_mode_data["contents"] = AttributedString("Notes: ")
						self.__output_mode_data["class"] = "notes"
						return True
				
					if lowered == "operation":
						self.__output.write('<h2 id="operation">Operation</h2>\n')
						self.__output_mode = "code"
						self.__output.write("<pre>")
						return True
			else:
				if row[0].contents.value == u"•":
					self.__output.write("<ul>\n")
					self.__output_mode = "list"
					self.__output_mode_data = {"indent": row[1].x, "contents": AttributedString("")}
					return self.write(row)
				
				# pretty much a table if it's not a list
				self.__output_mode = "table"
				self.__output_mode_data = {
					"columns": [row[i].x - 2 if i == 0 else (row[i-1].x + row[i].x) / 2 for i in xrange(0, len(row))],
					"row_data": [],
					"row_top": []
				}
			
			return self.write(row)
	
	def __is_title(self, cell):
		return cell.style["color"] != [0,0,0]
	
	def __write_table(self):
		# first merge cells
		column_count = len(self.__output_mode_data["columns"])
		row_data = self.__output_mode_data["row_data"]
		row_tops = self.__output_mode_data["row_top"]
		i = 1
		
		while i < len(row_data):
			if None in row_data[i] or abs(row_tops[i] - row_tops[i-1]) < 12:
				for j in xrange(0, column_count):
					if row_data[i][j] != None:
						row_data[i-1][j] = self.__append(row_data[i-1][j], row_data[i][j])
				row_tops[i-1] = row_tops[i]
				del row_data[i]
				del row_tops[i]
			else:
				i += 1
		
		self.__output.write("<table>\n")
		for row in row_data: 
			self.__output.write("<tr>\n")
			for text in row:
				self.__output.write("\t<td>%s</td>\n" % text.html())
			self.__output.write("</tr>\n")
		self.__output.write("</table>\n")
	
	def __break_p(self, row):
		if len(row) != 1 and not re.match(r"Table [0-9]+-[0-9]+\.", row[0].contents.value): return True
		
		cell = row[0]
		if cell.style["color"] != self.__output_mode_data["color"]: return True
		if abs(cell.y - self.__output_mode_data["top"]) > 15: return True
		return False
	
	def __break_list(self, row):
		length = len(row)
		if length == 0: return True
		if row[0].contents.value != u"•" and row[0].x < self.__output_mode_data["indent"] - 5:
			return True
		return False
	
	def __break_table(self, row):
		length = len(row)
		if length == 0: return True
		if length == 1:
			if row[0].style["color"] != [0,0,0]: return True
			
			xdiff = abs(row[0].x - self.__output_mode_data["columns"][0])
			ydiff = abs(row[0].y - self.__output_mode_data["row_top"][-1])
			return xdiff < 2 or ydiff > 18
		return False
	
	def __append(self, a, b):
		if len(a.value) == 0: return b
		if a.value[-1].isalnum() or a.value[-1] in self.__spaced_chars:
			c = AttributedString(a.value, a.attributes)
			c.append(AttributedString(" "))
			c.append(b)
			return c
			
		if a.value[-1] == u"-":
			c = AttributedString(a.value[:-1], a.attributes[:-1])
			c.append(b)
			return c
		
		c = AttributedString(a.value, a.attributes)
		c.append(b)
		return c
	
	def save(self, name_func):
		self.write([])
		filename = self.title.split(u"—")[0].replace("/", ":").strip()
		path = "html/" + name_func(filename)
		print "Saving to", path
		with open(path, "wb") as fd:
			fd.write("<!DOCTYPE html>\n")
			fd.write("<html>\n")
			fd.write("<head>\n")
			fd.write('\t<meta charset="UTF-8"/>\n')
			fd.write('\t<link rel="stylesheet" type="text/css" href="style.css"/>\n')
			fd.write(("\t<title>%s</title>\n" % self.title).encode("UTF-8"))
			fd.write("</head>\n")
			fd.write("<body>\n")
			fd.write(self.__output.getvalue().encode("UTF-8"))
			fd.write("</body>\n</html>\n")

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "usage: %s file [file...]" % sys.argv[0]
	
	names = set()
	def namer(filename):
		i = 1
		result = filename + ".html"
		while result in names:
			result = "%s-%i.html" % (filename, i)
			i += 1
		names.add(result)
		return result
	
	for i in xrange(1, len(sys.argv)):
		soup = bs4.BeautifulSoup(open(sys.argv[i]))
		input = UglyDocument(soup)
		output = DocumentWriter()
		for row in input.all_rows():
			if not output.write(row):
				output.save(namer)
				output = DocumentWriter()
				output.write(row)

		output.save(namer)

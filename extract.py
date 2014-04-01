# -*- coding: UTF-8 -*-
import re
import bs4
import sys
from StringIO import StringIO

class BetterIter(object):
	def __init__(self, iter):
		self.__iter = iter
		self.__current = iter.next()
	
	def next(self):
		try:
			self.__current = self.__iter.next()
			return True
		except StopIteration:
			self.__current = None
			return False
	
	def current(self):
		return self.__current

class TextCell(object):
	def __init__(self, x, y, style, contents):
		self.style = style
		self.x = x
		self.y = y
		self.contents = contents
	
	def __repr__(self):
		return ("%i: %s" % (self.x, self.contents)).encode("UTF-8")

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
	
	def all_cells(self):
		for div in self.__all_divs():
			style = self.__tag_style(div)
			x = style["left"]
			y = style["top"]
			
			# TODO change <span> tags into <em>, <strong> somewhere around this place
			
			text = div.text.strip()
			text_parts = []
			last_offset = 0
			match = re.search(" {2,}", text)
			while match != None:
				text_parts.append(text[last_offset:match.end()])
				last_offset += match.end()
				match = re.search(" {2,}", text[last_offset:])
			text_parts.append(text[last_offset:])
			
			for part in text_parts:
				yield TextCell(x, y, style, part.strip())
				x += len(part) * style["font-size"] / 2 # approximation
	
	def all_rows(self):
		row = []
		last_y = 0
		for cell in self.all_cells():
			if abs(last_y - cell.y) > 3 and len(row) != 0:
				yield row
				row = []
			row.append(cell)
			last_y = cell.y
		yield row

class DocumentWriter(object):
	def __init__(self):
		self.title = ""
		self.__output_mode = None # could be one of None, "p", "list", "code", "table"
		self.__output_mode_data = {}
		self.__output = StringIO()
		self.__spaced_chars = set(['.', ',', ';', ':'])
	
	def write(self, row):
		if self.__output_mode == "p":
			if self.__break_p(row):
				text = self.__output_mode_data["contents"]
				if self.__output_mode_data["color"] == [0,0,0]:
					css_class = ' class="%s"' % self.__output_mode_data["class"] if "class" in self.__output_mode_data else ""
					self.__output.write("<p%s>%s</p>\n" % (css_class, text))
				else:
					lowered = text.lower()
					if lowered != "notes:":
						if self.__output_mode_data["size"] > 12:
							self.title = text
							tag = "h1"
						else:
							tag = "h2"
						id = re.sub("[^a-z0-9]", "-", lowered)
						self.__output.write('<%s id="%s">%s</%s>\n' % (tag, id, text, tag))
				
				self.__output_mode = None
				return self.write(row)
			
			cell = row[0]
			self.__output_mode_data["contents"] = self.__append(self.__output_mode_data["contents"], cell.contents)
			self.__output_mode_data["top"] = cell.y
			return True
			
		elif self.__output_mode == "code":
			cell = row[0]
			if self.__is_title(cell):
				self.__output.write("</pre>\n")
				self.__output_mode = None
				return self.write(row)
				
			distance = cell.x - self.__output_mode_data["left"]
			self.__output.write(" " * int(round(distance / 6.75)))
			self.__output.write(cell.contents.replace(u"", u"←") + "\n")
			return True
			
		elif self.__output_mode == "list":
			if self.__break_list(row):
				if len(self.__output_mode_data["contents"]) != 0:
					self.__output.write("\t<li>%s</li>\n" % self.__output_mode_data["contents"])
				self.__output.write("</ul>\n")
				self.__output_mode = None
				return self.write(row)
			
			if len(row) == 2 and len(self.__output_mode_data["contents"]) != 0:
				self.__output.write("\t<li>%s</li>\n" % self.__output_mode_data["contents"])
				self.__output_mode_data["contents"] = ""
			
			self.__output_mode_data["contents"] = self.__append(self.__output_mode_data["contents"], row[-1].contents)
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
				table_row[last_column] = cell.contents
			
			self.__output_mode_data["row_data"].append(table_row)
			return True
			
		else:
			assert self.__output_mode == None
			# figure out output mode
			length = len(row)
			if length == 0: return False
			elif length == 1:
				cell = row[0]
				self.__output_mode = "p"
				self.__output_mode_data = {
					"top": cell.y,
					"left": cell.x,
					"contents": "",
					"color": cell.style["color"],
					"size": cell.style["font-size"],
				}
				
				if self.__output_mode_data["color"] != [0,0,0]:
					if self.__output_mode_data["size"] > 12:
						if len(self.title) != 0:
							self.__output_mode = None
							self.__output_mode_data = {}
							return False
					
					lowered = cell.contents.lower()
					# hacks!
					if lowered == "notes:":
						self.__output_mode_data["color"] = [0,0,0]
						self.__output_mode_data["contents"] = "Notes: "
						self.__output_mode_data["class"] = "notes"
						return True
				
					if lowered == "operation":
						self.__output.write('<h2 id="operation">Operation</h2>\n')
						self.__output_mode = "code"
						self.__output.write("<pre>")
						return True
			else:
				if len(row) == 2 and row[0].contents == u"•":
					self.__output.write("<ul>\n")
					self.__output_mode = "list"
					self.__output_mode_data = {"left": row[0].x, "contents": ""}
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
				self.__output.write("\t<td>%s</td>\n" % text)
			self.__output.write("</tr>\n")
		self.__output.write("</table>\n")
	
	def __break_p(self, row):
		if len(row) != 1: return True
		
		cell = row[0]
		if cell.style["color"] != self.__output_mode_data["color"]: return True
		if abs(cell.y - self.__output_mode_data["top"]) > 15: return True
		return False
	
	def __break_list(self, row):
		length = len(row)
		if length == 0 or length > 2: return True
		if length == 1:
			if abs(row[0].x - self.__output_mode_data["left"]) < 3:
				return True
		elif row[0].contents != u"•": return True
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
		if len(a) == 0: return b
		if a[-1].isalpha() or a[-1] in self.__spaced_chars: return a + " " + b
		if a[-1] == u"-": return a[:-1] + b
		return a + b
	
	def save(self):
		self.write([])
		filename = self.title.split(u"—")[0].replace("/", ":").strip()
		path = "html/" + filename + ".html"
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
	
	for i in xrange(1, len(sys.argv)):
		soup = bs4.BeautifulSoup(open(sys.argv[i]))
		input = UglyDocument(soup)
		output = DocumentWriter()
		for row in input.all_rows():
			if not output.write(row):
				output.save()
				output = DocumentWriter()
				output.write(row)

		output.save()

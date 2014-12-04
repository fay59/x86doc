#!/usr/bin/env python
# -*- coding: UTF-8 -*-

class Rect(object):
	def __init__(self, x1, y1, x2, y2):
		self.__x1 = x1
		self.__x2 = x2
		self.__y1 = y1
		self.__y2 = y2
	
	def x1(self): return self.__x1
	def x2(self): return self.__x2
	def y1(self): return self.__y1
	def y2(self): return self.__y2
	def xmid(self): return (self.__x1 + self.__x2) / 2
	def ymid(self): return (self.__y1 + self.__y2) / 2
	
	def width(self): return abs(self.__x1 - self.__x2)
	def height(self): return abs(self.__y1 - self.__y2)
	
	def union(self, rect):
		return Rect(min(rect.x1(), self.x1()), min(rect.y1(), self.y1()), max(rect.x2(), self.x2()), max(rect.y2(), self.y2()))
	
	def vertical(self): return self.width() < self.height()
	def horizontal(self): return self.height() < self.width()
	
	def __repr__(self):
		orientation = "V" if self.vertical() else "H"
		return "Rect%s(%0.2f,%0.2f,%0.2f,%0.2f)" % (orientation, self.x1(), self.y1(), self.x2(), self.y2())
	
	def intersects(self, that, threshold = 2):
		if self.x1() - that.x2() - threshold > 0:
			return False
		if that.x1() - self.x2() - threshold > 0:
			return False
		if self.y1() - that.y2() - threshold > 0:
			return False
		if that.y1() - self.y2() - threshold > 0:
			return False
		return True
	
	def debug_html(self, color="black", cls="black"):
		fmt = '<div class="%s" style="position:absolute;left:%fpx;top:%fpx;width:%fpx;height:%fpx;border:1px %s solid;background-color:%s"></div>'
		return fmt % (cls, self.x1(), self.y1(), self.width(), self.height(), color, color)

def sort_rect_by_position(x, y, dimension):
	return lambda rect: y(rect) * dimension + x(rect)

def sort_rect(a, b):
	ydiff = a.y1() - b.y1()
	if abs(ydiff) > 0.7: return int(ydiff * 100)
	
	xdiff = a.x1() - b.x1()
	if abs(xdiff) > 0.7: return int(xdiff * 100)
	
	heightdiff = a.y2() - b.y2()
	return int(-heightdiff * 100)

def cluster_rects(lines):
	table_group = [lines.pop()]
	just_removed = table_group[:]
	while len(just_removed) > 0:
		removed = []
		for test_against in just_removed:
			i = 0
			while i < len(lines):
				if test_against.intersects(lines[i]):
					removed.append(lines.pop(i))
				else:
					i += 1
		table_group += removed
		just_removed = removed
	return table_group

# this is not particularly statistically sound, but I think that it works
def count_segments(list, expected_clusters):
	list.sort()
	expected_distance = (list[-1] - list[0]) / expected_clusters
	last_item = list[0]
	clusters = [1]
	for item in list[1:]:
		if item - last_item < expected_distance:
			clusters[-1] += 1
		else:
			clusters.append(1)
		last_item = item
	return clusters

def pretty_much_equal(a, b, threshold = 2):
	return abs(a - b) < threshold

class List(object):
	def __init__(self, items):
		assert len(items) > 0
		self.items = items
		self.rect = items[0].bounds()
		for i in items[1:]:
			self.rect = self.rect.union(i.bounds())
	
	def bounds(self): return self.rect
		

class TableBase(object):
	def get_at(self, x, y): raise Exception("Not implemented")
	def rows(self): raise Exception("Not implemented")
	def columns(self): raise Exception("Not implemented")
	def bounds(self): raise Exception("Not implemented")
	def cell_size(self, x, y): raise Exception("Not implemented")
	def data_index(self, x, y): raise Exception("Not implemented")

class ImplicitTable(TableBase):
	def __init__(self, bounds, table_data):
		self.__bounds = bounds
		self.__data = table_data
	
	def get_at_pixel(self, x, y):
		raise Exception("Not supported on implicit tables")
	
	def get_at(self, x, y):
		return self.__data[y][x]
	
	def rows(self): return len(self.__data)
	def columns(self): return len(self.__data[0])
	def bounds(self): return self.__bounds
	
	def cell_size(self, x, y):
		assert x >= 0 and x < self.columns()
		assert y >= 0 and y < self.rows()
		return (1, 1)
	
	def data_index(self, x, y): return y * self.columns() + x
	
	def debug_html(self):
		result = '<table border="1">'
		for row in self.__data:
			result += '<tr>'
			for cell in row:
				result += '<td>'
				for element in ell:
					result += unicode(element).replace("<", "&lt;").replace(">", "&gt;")
				result += '</td>'
			result += '</tr>'
		result += '</table>'
		return result

class Table(TableBase):
	def __init__(self, group):
		ver = []
		hor = []
		for line in group:
			(ver if line.vertical() else hor).append(line)
		
		assert len(ver) >= 2
		assert len(hor) >= 2
		
		self.__columns = self.__identify_dimension(ver, Rect.xmid)
		self.__rows = self.__identify_dimension(hor, Rect.ymid)
		self.__init_data_layout()
		
		if len(self.__columns) > 2:
			missingC = self.__identify_missing_col_lines(ver)
			missingC.sort(key=sort_rect_by_position(Rect.y1, Rect.xmid, self.__columns[-1]))
			for missing in missingC:
				rightColumn = self.__data_col_index(missing.xmid())
				assert rightColumn != 0 and rightColumn != len(self.__columns)
				leftColumn = rightColumn - 1
				beginIndex = self.__data_row_index(missing.y1())
				endIndex = self.__data_row_index(missing.y2())
				for i in xrange(beginIndex, endIndex):
					self.__data_layout[i][rightColumn] = self.__data_layout[i][leftColumn]
		
		if len(self.__rows) > 2:
			missingR = self.__identify_missing_row_lines(hor)
			missingR.sort(key=sort_rect_by_position(Rect.x1, Rect.ymid, self.__rows[-1]))
			for missing in missingR:
				topRow = self.__data_row_index(missing.ymid())
				assert topRow != 0 and topRow != len(self.__rows) - 1
				bottomRow = topRow - 1
				beginIndex = self.__data_col_index(missing.x1())
				endIndex = self.__data_col_index(missing.x2())
			
				# Do not merge into non-rectangular cells.
				if beginIndex > 0:
					prev = beginIndex - 1
					if self.__data_layout[topRow][prev] == self.__data_layout[topRow][beginIndex]:
						continue
			
				if endIndex < len(self.__rows) - 1:
					prev = endIndex - 1
					if self.__data_layout[topRow][prev] == self.__data_layout[topRow][endIndex]:
						continue
			
				for i in xrange(beginIndex, endIndex):
					self.__data_layout[bottomRow][i] = self.__data_layout[topRow][i]
		
		self.__init_data_storage()
	
	def get_at_pixel(self, x, y):
		row_index = self.__data_row_index(y)
		col_index = self.__data_col_index(x)
		return self.get_at(col_index, row_index)
	
	def get_at(self, x, y):
		row = self.__data_layout[y]
		data_index = row[x]
		return self.__data_storage[data_index]
	
	def rows(self): return len(self.__rows) - 1
	def columns(self): return len(self.__columns) - 1
	
	def bounds(self):
		return Rect(self.__columns[0], self.__rows[0], self.__columns[-1], self.__rows[-1])
	
	def cell_size(self, x, y):
		row_index = self.__data_row_index(y)
		col_index = self.__data_col_index(x)
		return self.__cell_size(col_index, row_index)
	
	def data_index(self, x, y):
		return self.__data_layout[y][x]
	
	def debug_html(self):
		result = '<table border="1">'
		print_index = -1
		for row_index in xrange(0, self.rows()):
			row = self.__data_layout[row_index]
			result += "<tr>"
			for cell_index in xrange(0, len(row)):
				cell = row[cell_index]
				if print_index >= cell: continue
				width, height = self.cell_size(cell_index, row_index)
				colspan = (' colspan="%i"' % width) if width != 1 else ""
				rowspan = (' rowspan="%i"' % height) if height != 1 else ""
				result += "<td%s%s>" % (colspan, rowspan)
				for element in self.get_at(cell_index, row_index):
					result += unicode(element).replace("<", "&lt;").replace(">", "&gt;")
				result += "</td>"
				print_index = cell
			result += "</tr>"
		result += "</table>"
		return result
	
	def __identify_dimension(self, lines, key):
		lines.sort(key=key)
		dim = []
		for line in lines:
			value = key(line)
			if len(dim) == 0 or value - dim[-1] > 1:
				dim.append(value)
		return dim
	
	def __identify_missing_col_lines(self, vertical):
		sort_key = sort_rect_by_position(Rect.y1, Rect.xmid, self.__rows[0] - self.__rows[-1])
		vertical.sort(key=sort_key)
		missing_lines = []
		def add_missing_line(x, y1, y2):
			missing_lines.append(Rect(x, y1, x, y2))
		
		topY = self.__rows[0]
		botY = self.__rows[-1]
		lastX = self.__columns[0]
		lastY = botY
		for line in vertical[1:]:
			if not pretty_much_equal(line.xmid(), lastX):
				if not pretty_much_equal(lastY, botY):
					add_missing_line(lastX, lastY, botY)
				lastY = topY
			
			if not pretty_much_equal(line.y1(), lastY):
				add_missing_line(line.xmid(), lastY, line.y1())
			lastY = line.y2()
			lastX = line.xmid()
		return missing_lines
	
	def __identify_missing_row_lines(self, horizontal):
		sort_key = sort_rect_by_position(Rect.x1, Rect.ymid, self.__columns[-1] - self.__columns[0])
		horizontal.sort(key=sort_key)
		missing_lines = []
		def add_missing_line(y, x1, x2):
			missing_lines.append(Rect(x1, y, x2, y))
		
		topX = self.__columns[0]
		botX = self.__columns[-1]
		lastX = botX
		lastY = self.__rows[0]
		for line in horizontal[1:]:
			if not pretty_much_equal(line.ymid(), lastY):
				if not pretty_much_equal(lastX, botX):
					add_missing_line(lastY, lastX, botX)
				lastX = topX
			
			if not pretty_much_equal(line.x1(), lastX):
				add_missing_line(line.ymid(), lastX, line.x1())
			lastY = line.ymid()
			lastX = line.x2()
		return missing_lines
	
	def __init_data_layout(self):
		self.__data_layout = []
		i = 0
		row_count = len(self.__rows) - 1
		col_count = len(self.__columns) - 1
		for _ in xrange(0, row_count):
			row = []
			for _ in xrange(0, col_count):
				row.append(i)
				i += 1
			self.__data_layout.append(row)
	
	def __init_data_storage(self):
		i = 0
		last_index = 0
		for row_index in xrange(0, len(self.__data_layout)):
			row = self.__data_layout[row_index]
			for cell_index in xrange(0, len(row)):
				if row[cell_index] > last_index:
					i += 1
					last_index = row[cell_index]
				row[cell_index] = i
		
		self.__data_storage = []
		for i in xrange(0, self.__data_layout[-1][-1] + 1):
			self.__data_storage.append([])
	
	def __data_row_index(self, y):
		return self.__dim_index(self.__rows, y)
	
	def __data_col_index(self, x):
		return self.__dim_index(self.__columns, x)
	
	def __dim_index(self, array, value):
		for i in xrange(1, len(array)):
			ref_value = array[i]
			if ref_value > value:
				return i - 1
		
		raise Exception("improbable (%g between %g and %g)" % (value, array[0], array[-1]))
	
	def __cell_size(self, column, row):
		value = self.__data_layout[row][column]
		width = 0
		x = column
		while x >= 0 and self.__data_layout[row][x] == value:
			width += 1
			x -= 1
		
		x = column + 1
		while x < len(self.__data_layout[row]) and self.__data_layout[row][x] == value:
			width += 1
			x += 1
		
		height = 0
		y = row
		while y >= 0 and self.__data_layout[y][column] == value:
			height += 1
			y -= 1
		
		y = row + 1
		while y < len(self.__data_layout) and self.__data_layout[y][column] == value:
			height += 1
			y += 1
		
		return (width, height)

def main():
	rects = [[45.120,39.720,494.340,53.640],
			[504.840,39.720,559.620,53.640],
			[46.380,354.960,104.520,370.980],
			[336.960,354.960,366.060,370.980],
			[278.880,339.000,336.960,354.960],
			[46.380,322.980,220.740,339.000],
			[46.380,306.960,220.740,322.980],
			[46.380,291.000,220.740,306.960],
			[46.380,274.980,220.740,291.000],
			[46.380,258.960,220.740,274.980],
			[46.380,243.000,220.740,258.960],
			[46.380,226.980,220.740,243.000],
			[46.380,210.960,220.740,226.980],
			[46.020,627.240,46.500,709.740],
			[557.460,627.240,557.940,709.740],
			[46.020,709.740,557.940,710.220],
			[46.020,626.760,557.940,627.240],
			[46.140,559.260,46.620,590.760],
			[557.340,559.260,557.820,590.760],
			[46.140,590.760,557.880,591.240],
			[46.140,558.780,557.880,559.260],
			[45.660,371.760,47.160,386.220],
			[46.140,355.260,46.620,370.260],
			[46.140,83.220,46.620,354.720],
			[104.280,370.260,104.760,387.720],
			[104.280,354.720,104.760,371.760],
			[162.420,338.760,162.900,387.720],
			[220.500,370.260,220.980,387.720],
			[220.500,210.720,220.980,339.240],
			[278.640,338.760,279.120,387.720],
			[336.720,370.260,337.200,387.720],
			[336.720,354.720,337.200,371.760],
			[336.720,338.760,337.200,355.260],
			[365.820,370.260,366.300,387.720],
			[365.820,354.720,366.300,371.760],
			[402.360,338.760,402.840,387.720],
			[460.440,354.720,460.920,387.720],
			[518.580,370.260,519.060,387.720],
			[518.100,82.740,519.600,371.760],
			[556.860,83.220,558.360,386.220],
			[45.660,386.220,558.300,387.720],
			[45.660,370.200,558.300,371.700],
			[46.140,354.720,337.260,355.200],
			[336.720,354.720,365.820,355.200],
			[366.300,354.720,558.300,355.200],
			[46.140,338.760,558.300,339.240],
			[46.140,322.740,558.300,323.220],
			[46.140,306.720,558.300,307.200],
			[46.140,290.760,558.300,291.240],
			[46.140,274.740,558.300,275.220],
			[46.140,258.720,558.300,259.200],
			[46.140,242.760,558.300,243.240],
			[46.140,226.740,558.300,227.220],
			[46.140,210.720,558.300,211.200],
			[46.140,194.760,558.300,195.240],
			[46.140,178.740,558.300,179.220],
			[46.140,162.720,558.300,163.200],
			[46.140,146.760,558.300,147.240],
			[46.140,130.740,558.300,131.220],
			[46.140,114.720,558.300,115.200],
			[46.140,98.760,558.300,99.240],
			[46.140,82.740,558.300,83.220],]

	lines = []
	figures = []
	tables = []
	for i in xrange(0, len(rects)):
		rect = Rect(*rects[i])
		(lines if (rect.width() < 9 or rect.height() < 9) else figures).append(rect)

	# group lines into tables
	while len(lines) > 0:
		table = cluster_rects(lines)
		tables.append(table)

	for table in tables:
		t = Table(table)
		print

if __name__ == "__main__":
	main()
#!/bin/env python
# -*- coding: UTF-8 -*-

# OpenTag and CloseTag are NOT HARDENED against HTML injection!
# Do not use them for input that you cannot perfectly predict.

import re

class OpenTag(object):
	def __init__(self, tag, coalesce=False, attributes={}):
		self.tag = tag
		self.coalesce = coalesce
		self.attributes = attributes
		self.closed_by = None
	
	def __attribute_string(self):
		if len(self.attributes) == 0:
			return ""
		result = ""
		for key in self.attributes:
			result += ' %s="%s"' % (key, self.attributes[key].replace('"', '&quot;'))
		return result
	
	def open(self):
		return "<%s%s>" % (self.tag, self.__attribute_string())
	
	def close(self):
		return "</%s>" % self.tag
	
	def __str__(self): return self.open()

class CloseTag(object):
	def __init__(self, tag):
		self.closes = None
		self.tag = tag
	
	def __str__(self):
		return "</%s>" % self.tag

class HtmlText(object):
	def __init__(self):
		self.__tokens = []
	
	def append(self, token):
		if self.__is_close(token):
			for prev in reversed(self.__tokens):
				if self.__is_open(prev) and prev.closed_by == None and prev.tag == token.tag:
					token.closes = prev
					prev.closed_by = token
					break
			else: raise Exception("No matching OpenTag found!")
		elif len(self.__tokens) > 0 and self.__is_open(token):
			for i in xrange(-1, -len(self.__tokens), -1):
				last = self.__tokens[i]
				is_close = self.__is_close(last)
				if not (is_close or self.__is_open(last)):
					break
				if is_close and last.tag == token.tag and last.coalesce and last.attributes == token.attributes:
					positive = len(self.__tokens) + i
					self.__tokens = self.__tokens[0:positive] + self.__tokens[positive+1:]
					return
		
		self.__tokens.append(token)
	
	def to_html(self):
		tag_stack = []
		result = u""
		for token in self.__tokens:
			if isinstance(token, OpenTag):
				tag_stack.append(token)
				result += token.open()
			elif isinstance(token, CloseTag):
				close_it = tag_stack.pop()
				reopen_it = []
				while close_it.tag != token.tag:
					result += close_it.close()
					reopen_it.append(close_it)
					close_it = tag_stack.pop()
				result += close_it.close()
				for tag in reversed(reopen_it):
					tag_stack.append(tag)
					result += tag.open()
			else:
				uni = unicode(token)
				for pair in [("&", "&amp;"), ("<", "&lt;"), (">", "&gt;")]:
					uni = uni.replace(pair[0], pair[1])
				result += uni
		
		while len(tag_stack) > 0:
			result += tag_stack.pop().close()
		return result
	
	def __is_open(self, token):
		return hasattr(token, "tag") and hasattr(token, "coalesce")
	
	def __is_close(self, token):
		return hasattr(token, "tag") and not hasattr(token, "coalesce")
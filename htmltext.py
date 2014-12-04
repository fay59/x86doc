#!/bin/env python
# -*- coding: UTF-8 -*-

# OpenTag and CloseTag are NOT HARDENED against HTML injection!
# Do not use them for input that you cannot perfectly predict.

import re

inline_tags__ = set(["em", "strong", "sup", "sub"])

class OpenTag(object):
	def __init__(self, tag, coalesce=False, attributes={}, self_closes = False):
		self.tag = tag
		self.coalesce = coalesce
		self.attributes = attributes
		self.closed_by = None
		self.self_closes = self_closes
	
	def __attribute_string(self):
		if len(self.attributes) == 0:
			return ""
		result = ""
		for key in self.attributes:
			result += ' %s="%s"' % (key, unicode(self.attributes[key]).replace("&", "&amp;").replace('"', '&quot;'))
		return result
	
	def open(self):
		return "<%s%s>" % (self.tag, self.__attribute_string())
	
	def close(self):
		return "</%s>" % self.tag
	
	def __str__(self): return self.open()
	def __repr__(self): return "<OpenTag %s %s>" % (self.tag, self.__attribute_string())

class CloseTag(object):
	def __init__(self, tag):
		self.closes = None
		self.tag = tag
	
	def __str__(self): return "</%s>" % self.tag
	def __repr__(self): return "<CloseTag %s>" % self.tag

class HtmlText(object):
	def __init__(self):
		self.tokens = []
	
	def autoclose(self):
		close_stack = []
		for t in self.tokens:
			if self.__is_open(t): close_stack.append(t)
			elif self.__is_close(t):
				if not (close_stack[-1].tag == t.tag):
					print close_stack
					print self.tokens
					raise Exception("autoclose mismatch")
				close_stack.pop()
		
		while len(close_stack) > 0:
			self.append(CloseTag(close_stack.pop().tag))
	
	def append(self, token):
		if self.__is_close(token):
			for prev in reversed(self.tokens):
				if self.__is_open(prev) and prev.closed_by == None and prev.tag == token.tag:
					token.closes = prev
					prev.closed_by = token
					break
			else:
				print self.tokens
				raise Exception("No matching OpenTag for %s found!" % token.tag)
		elif len(self.tokens) > 0 and self.__is_open(token):
			for i in xrange(-1, -len(self.tokens), -1):
				last = self.tokens[i]
				is_close = self.__is_close(last)
				if not (is_close or self.__is_open(last)):
					break
				if is_close and last.tag == token.tag and last.closes.coalesce and last.closes.attributes == token.attributes:
					positive = len(self.tokens) + i
					self.tokens = self.tokens[0:positive] + self.tokens[positive+1:]
					return
		elif hasattr(token, "tokens"):
			token.autoclose()
			tokens = token.tokens
			if len(tokens) > 0:
				if len(self.tokens) > 0:
					last = self.tokens[-1]
					is_close = self.__is_close(last)
					next = tokens[0]
					if is_close and self.__is_open(next):
						closed = last.closes
						if last.tag == next.tag and closed.coalesce and closed.attributes == next.attributes:
							self.tokens[-1].closed_by = tokens[-1]
							self.tokens[-1] = "\n"
							tokens = tokens[1:]
				
				self.tokens += tokens
			return
		
		self.tokens.append(token)
	
	def to_html(self):
		tag_stack = []
		result = u""
		for token in self.tokens:
			if isinstance(token, OpenTag):
				if not token.self_closes:
					tag_stack.append(token)
				if not token.tag in inline_tags__: result += "\n"
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
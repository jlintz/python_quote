#!/usr/bin/env python
"""
A basic setup of demonstrating how python_quote can be used within a webapp

"""
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import python_quote
import logging

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

logger = logging.getLogger("python_quote")
logger.setLevel(logging.DEBUG)
qc = python_quote.QuoteCache()

class Application(tornado.web.Application):
	def __init__(self):
		handlers = [
			(r"/", MainHandler),
			(r"/quote/([a-zA-Z]+)",QuoteHandler),
		    ]
		tornado.web.Application.__init__(self, handlers)

class MainHandler(tornado.web.RequestHandler):
	"""
		This will handle the default request or a GET request
		looking for the "quotes" query string

		Note: Probably pointless to use asynchronous as python_quote
		uses urllib which makes synchronous calls to yahoo finance.
	"""
	@tornado.web.asynchronous
	def get(self):

		options = self.get_argument("options","l1,a").encode("utf-8")
		options = list(options.split(","))
		logger.debug(options)
		
		if self.get_argument("quotes",None):
			quotes = self.get_argument("quotes").encode("utf-8")
			quotes = list(quotes.split(","))
			try:
				results = qc.get(quotes,options,True)
			except ValueError, ve:
				logger.info(ve)
				raise tornado.web.HTTPError(500,str(ve))

			self.write(results)
			self.finish()
		else:
			self.write("Oh hai")
			self.finish()

class QuoteHandler(tornado.web.RequestHandler):
	"""
		Handles URIs of /quote/ticker
		Single quotes only
	"""
	@tornado.web.asynchronous
	def get(self,quote):
		results = qc.get([quote],['l1','a'],True)
		self.write(results)
		self.finish()

def main():
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()  

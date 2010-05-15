#!/usr/bin/env python
"""
Modified the Hello World tornado "webapp"
"""
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import python_quote

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

class MainHandler(tornado.web.RequestHandler):
	"""
		This will handle the default request or a GET request
		looking for the "quotes" query string
	"""
	@tornado.web.asynchronous
	def get(self):
		qc = python_quote.QuoteCache()
		if self.get_argument("quotes",None):
			quotes = self.get_argument("quotes").encode( "utf-8" )
			quotes = list(quotes.split(","))
			results = qc.get(quotes,['l1','a'],True)
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
		qc = python_quote.QuoteCache()
		results = qc.get([quote],['l1','a'],True)
		self.write(results)
		self.finish()

def main():
	tornado.options.parse_command_line()
	application = tornado.web.Application([
        (r"/", MainHandler),
	(r"/quote/([a-zA-Z]+)",QuoteHandler),
    ])
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()  

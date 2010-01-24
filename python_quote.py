#!/usr/bin/env python
"""
Author: Justin Lintz < jlintz@gmail.com >

This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

About:
	A python module to pull quotes from Yahoo Finance and cache them using a
	memcached backend

TODO:
- use get_multi to reduce memcache lookups
- unit tests

FUTURE:
- prevent storms to yahoo finance
- persistence storage (redis backend?)

"""

import urllib2
import re
import logging
import sys


#need to test for memcache module and throw error if not found
try:
	import memcache
except ImportError:
	raise ImportError('python-memcache module is required for this module.')


class QuoteCache(object):
	#yahoo allows a max of 50 quote requests per GET
	MAX_QUOTES = 50

	def __init__(self, servers = ['localhost:11211'], logfile = './python_quote.log', EXPIRE_TIME = 600):
		self.servers = servers
		self.EXPIRE_TIME = EXPIRE_TIME
		self.cache = memcache.Client(servers)
		self.yahoo_url = "http://finance.yahoo.com/d/quotes.csv?s=%s&f=%s"
		self.valid_params = set(['a','a2','a5','b','b2','b3','b4','b6','c','c1','c3','c6','c8','d','d1',
		'd2','e','e1','e7','e8','e9','f6','g','h','j','k','g1','g3','g4','g5','g6','i','i5','j1','j3',
		'j4','j5','j6','k1','k2','k3','k4','k5','l','l1','l2','l3','m','m2','m3','m4','m5','m6','m7',
		'm8','n','n4','o','p','p1','p2','p5','p6','q','r','r1','r2','r5','r6','r7','s','s1','s7','t1',
		't6','t7','t8','v','v1','v7','w','w1','w4','x','y'])

		#change level to logging.DEBUG for debug msgs
		logging.basicConfig(filename=logfile,level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',)

	def get(self,quotes,params,refresh=False):
		""" 
		The main function for pulling quotes from Yahoo Finance.  First tries to pull
		from cache, if not, pulls quotes in groups of 50 for those not cached.

		@quotes: list of strings of stock symbols
		@params: list of yahoo parameters
		@refresh: bool that determines quotes should be forced to fetch from yahoo
		returns: a Dictionary of Dictionarys 
			{'STOCK': {'param' : 'value'}}

		"""

		if type(quotes) is not list:
			raise TypeError('quotes must be a list')

		if type(params) is not list:
			raise TypeError('params must be a list')

		#build a dictionary to return our results
		stock_results = {} 

		#build a list of uncached stocks
		if refresh:
			stock_miss = quotes
		else:
			stock_miss = []	

		#need to work with params as a string also
		params_str = ''.join(params)

		#check and make sure our params are valid
		invalid_params = set(params) - self.valid_params

		if invalid_params:
			raise ValueError('Invalid parameters found %s' % invalid_params)

		if not refresh:
			#iterate our quote list and check which values exist in memcache already	
			for stock in quotes:
				obj = self.cache.get(stock.upper() + params_str)
				if obj:
					logging.debug('Cache HIT %s' % stock)
					stock_results[stock.upper()] = obj
				else:
					logging.debug('Cache MISS %s' % stock)
					stock_miss.append(stock)

		#grab data for stocks we don't have cached
		#chunk our requests into 50 stocks at a time
		if stock_miss:
			for cnt in xrange(0,(len(stock_miss) / 50) + 1):	
				try:
					#make our list into a comma delimmited string
					quote_string = ','.join(stock_miss[cnt*50:(cnt+1)*50]) 

					#always include symbol param for use in our Dictionary
					url = self.yahoo_url % (quote_string,'s' + params_str)

					logging.debug('Fetching URL: %s' % url)
					ulquote = urllib2.urlopen(url) 
				except urllib2.error.URLError, e:
					sys.stderr.write("Error fetching quote from Yahoo" . e.reason)

				for csv_data in ulquote.readlines():
					#split up the csv data , chop off LF and CR
					stock_attrib = csv_data.strip().split(',') 
					#clean off quotes from symbol
					symbol = stock_attrib[0].replace('"','') 
					stock_dict = dict(zip(params,stock_attrib[1:]))
					
					if refresh:
						logging.debug('REFRESH forced %s' % symbol)

					logging.debug('SET %s (KEY: %s) to expire in %d' % (symbol,symbol+params_str,self.EXPIRE_TIME))
					logging.debug('ZIP %s' % stock_dict)

					self.cache.set(symbol + params_str,stock_dict,self.EXPIRE_TIME)
					stock_results[symbol.upper()] = stock_dict

		return stock_results

"""
called standalone
"""
def main():
	qc = QuoteCache()

	#test cache hit
	print qc.get(['KO'],['l1','a'])
	print qc.get(['KO'],['l1','a'])

	#invalid param 
	print qc.get(['KO'],['z'])

	#check chunking
	print qc.get(["UACA","UAXS","UBCD","UBCP","UBET","UBFO","UBIX","UBMT","UBOH",
	"UBSC","UBSCP","UBSH","UBSI","UCBC","UCBH","UCFC","UCOMA","UCTN","UEIC",
	"UFAB","UFBS","UFCS","UFHI","UFHIP","UFMG","UFPI","UFPT","UGLY","UHAL",
	"UHCO","UHCP","ULAB","ULBI","ULCM","ULGX","ULTE","ULTI","ULTK","UMBF",
	"UMPQ","UNAM","UNBJ","UNBO","UNCA","UNEWY","UNFI","UNIB","UNSRA","UNSRW",
	"UNTD","UNTY","UNWR","UOPX","UPCOY","UPCPO","UPCS","UPFC","URBN","URGI",
	"USAB","USAI","USAK","USAP","USBI","USDC","USEG","USEY","USEYW","USFC",
	"USHG","USHP","USHS","USIX","USLB","USLM","USNA","USOL","USOLW","USON",
	"USPH","USPI","USPL","USTR","USVI","UTBI","UTCI","UTCIW","UTEK","UTGI",
	"UTHR","UTIW","UTMD","UTOB","UTSI","UVEW","UVSL","UVSLW"],
	['l1'])

	#test force refresh
	print qc.get(['KO'],['l1','a'],True)

if __name__ == '__main__':
	main()	

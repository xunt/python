#!/usr/bin/env python
#coding=utf-8

import sys
import urllib
import re
import os
import socket

import sys
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
	reload(sys)
	sys.setdefaultencoding(default_encoding)

class crawl():
	def __init__(self):
		import time
		self.cur_date =time.strftime('%Y-%m-%d',time.localtime(time.time()))
		self.category = ['news', 'sports', 'tech', 'ent', 'edu', 'baby', 'games', 'green','travel']
		self.timeout=3
		self.swith_table = False	#True表示要表格，false不要
		
		os.system("mkdir -p news")
		self.web_coding="gb2312"	#web页面编码
			
	def get_urls(self,cate,num):
		socket.setdefaulttimeout(self.timeout)
		if num==3:
			print "faild!"
			return []
		try:
			content = urllib.urlopen("http://%s.sina.com.cn" %cate).read()
			rege="http://%s.sina.com.cn(?:/\w+)+/%s(?:/\w+)+.shtml" %( cate, self.cur_date )
			urls = re.findall(rege, content,re.S)
			urls = list(set(urls))
			return urls
		except socket.error:
			errno, errstr = sys.exc_info()[:2]
			if errno == socket.timeout:
				print "There was a timeout" 
			else:
				print "There was some other socket error"
			return self.get_urls(cate,num+1)
		except IOError:
			print "IOError"
			return self.get_urls(cate,num+1)
	
	def extract_title(self,content):
		re_key = "<h[0-9] id=\"artibodyTitle\"[^>]*>(.+?)</h[0-9]>"
		title = re.findall(re_key,content,re.S)
		if len(title) != 0:
			return title[0]
		else: return ""
	
	def extract_body(self,content):
		re_key = "<div[^>]*id=\"artibody\"[^>]*>(.+)</div>"
		body = re.findall(re_key,content,re.S)
		if len(body) != 0:
			#取"正文内容begin"之后的内容
			body = re.split("<!--\s*正文内容\s*begin\s*-->",body[0])
			if len(body)==2: body = body[1]
			else: body = body[0]
			
			#取"正文内容end"之前的内容
			body = re.split("<!--\s*正文内容\s*end\s*-->", body)[0]
			
			#取"微博推荐begin"之前的内容
			body = re.split("<!--\s*优质用户微博推荐\s*begin\s*-->",body)[0]
			
			#取"相关新闻"之前的内容 for games.sina.com.cn
			body = re.split("<!--\s*相关新闻\s*begin\s*-->", body)[0]
			body = body.split("相关新闻")[0]
			
			#取"分享功能"之前的内容
			body = re.split("<!--\s*分享功能\s*begin\s*-->",body)[0]
			
			#去分页前的文字
			body = body.split("上一页")[0]
			return body.strip()
		else: return ""
	
	def filter_tags(self,s):
		if self.swith_table==False:	#是否要表格，false不要
			re_table = re.compile("<table[^>]*>.+?</table>",re.S)	
			s = re_table.sub('',s)
		
		re_cdata=re.compile('//<!\[CDATA\[[^>]*//\]\]>',re.I|re.S) #CDATA
		s=re_cdata.sub('',s)
		
		re_script=re.compile('<script[^>]*>.+?</script>',re.I|re.S)#Script
		s=re_script.sub('',s)
		
		re_style=re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>',re.I|re.S)#style
		s=re_style.sub('',s)
		
		re_p=re.compile('<P\s*?/?>',re.I)#<p>
		s=re_p.sub('\n\n',s)
		
		re_h=re.compile('</?\w+[^>]*>',re.I|re.S)#HTML标签
		s=re_h.sub('',s) 
		
		re_comment=re.compile('<!--[^>]*-->',re.I|re.S)#HTML注释
		s=re_comment.sub('',s)
		
		re_nbsp=re.compile('&nbsp;')#HTML空格
		s=re_nbsp.sub('',s)
		
		re_video = re.compile("视频加载中，请稍候...(.+?)向后",re.S)	#视频
		s=re_video.sub('',s)
		re_video = re.compile("视频加载中，请稍候...(.+?)下一个",re.S)
		s=re_video.sub('',s)
		
		re_video = re.compile("<!--\s*标清图\s*begin\s*-->(.+?)<!--\s*标清图\s*end\s*-->",re.S)	#去图片内容
		s=re_video.sub('',s)
		
		re_M = re.compile("\r\n",re.S) #^M
		s=re_M.sub('',s)
		
		blank_line=re.compile('\n+',re.S)#多余空行
		s=blank_line.sub('',s)	
		
		return s
	
	
	def get_title_content(self,url,num):
		title,content = "",""
		if num==2: 
			print "faild!"
			return ("","")
		try:
			web_data = urllib.urlopen(url).read()
			web_data = web_data.decode(self.web_coding,"ignore").encode("utf8")
			title = self.extract_title(web_data)
			content = self.extract_body(web_data)
			content = self.filter_tags(content)
			return (title,content)
		except socket.error:
			errno, errstr = sys.exc_info()[:2]
			if errno == socket.timeout:
				print "There was a timeout" 
			else:
				print "There was some other socket error"
			return self.get_title_content(url,num+1)
		except IOError:
			print "IOError"
			return self.get_title_content(url,num+1)
	
	def gen_cate(self,cate):
		#get the urls
		urls = self.get_urls(cate,0)
		print "urls total:%d" %len(urls)
		
		if len(urls)>0:
			#generate file
			import codecs
			f = codecs.open("news/%s_%s.dat" %(cate, self.cur_date),"w","utf-8")
			for url in urls:
				print url
				title,content = self.get_title_content(url,0)
				if title!="" or content!="":
					f.write("url:\t" + url + "\ntitle:" + title + "\ncontent:" + content + "\n" + "-"*80 + "\n")
			f.close()
	
	def main(self):
		import datetime
		start = datetime.datetime.now()
		for cate in self.category:
			print "retrieve %s" %cate
			starttime = datetime.datetime.now()
			self.gen_cate(cate)
			endtime = datetime.datetime.now()
			print "%s Done:%d s\n" %(cate,(endtime - starttime).seconds)
		end = datetime.datetime.now()
		print "\ntotal:%d s" %(end - start).seconds

if __name__=='__main__':
	bob = crawl()
	bob.main()

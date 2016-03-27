# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse
import hashlib,time,re
from django.conf import settings
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from xml.etree import ElementTree
from wechat import message_res
import urllib2,json


#Store MsgId for all incoming message.
incomeMessageIds = set()
#Store (FromUserName,CreateTime) for all incoming message.
incomeMessageFromAndTime = set()
searchPattern = re.compile("^.*(查找|想买|买|搜索|查询|find|search|look for|query|seek)",re.IGNORECASE)

@csrf_exempt
def index(request):
	if request.method == 'GET':#auth
		return auth(request)
	if request.method == 'POST':#new message received
		return onUserMessage(request)
	
def onUserMessage(request):
	print "Incoming Msg:"+ request.body
	if not request.body:
		return HttpResponse(message_res.EMPTY_MESSAGE)
	tree = ElementTree.fromstring(request.body)
	if not isNewMessage(tree):
		return HttpResponse(message_res.REDUNDANT_MESSAGE)
	resp = None
	msgType = tree.find('MsgType')
	if msgType is not None and msgType.text =="event":
		resp =  doSubscriptionEvent(request,tree)
	elif msgType is not None and msgType.text =="text":
		resp =  doTextMessageEvent(request,tree)
	if resp:
		return resp
	else:
		return HttpResponse(message_res.UNSUPPORT_MESSAGE)

	
	
def doSubscriptionEvent(request,elementTree):
	event = elementTree.find("Event")
	if event is not None and event.text =="subscribe":
		msgType = "text"
		me = elementTree.find('ToUserName').text
		msgTo = elementTree.find('FromUserName').text
		content = message_res.USER_WELCOME
		createTime = int(time.time())
		context = {
			'toUser':msgTo,
			'fromUser':me,
			'createTime':createTime,
			'msgType':msgType,
			'content':content
		}
		return render(request, 'message.html', context)
	
	
	
def doTextMessageEvent(request,elementTree):
	#MsgType=text
	content = elementTree.find('Content').text
	content = content.encode('utf-8')
	m = searchPattern.search(content)
	if m:
		searchKeyword = searchPattern.sub("",content)
		resp = urllib2.urlopen(settings.SOLR_SVC %(urllib2.quote(searchKeyword),0,10))
		jsonStr = resp.read()
		itemJson = json.loads(jsonStr)
		itemTotal = itemJson['response']['numFound']
		mainTitle = "为你找到%s件\"%s\"相关的商品" %(itemTotal,searchKeyword)

		
		me = elementTree.find('ToUserName').text
		msgTo = elementTree.find('FromUserName').text
		createTime = int(time.time())
		context = {
			'toUser':msgTo,
			'fromUser':me,
			'createTime':createTime,
			'msgType':"news",
			'content':searchKeyword.strip(),
			'count':min(10,itemTotal),
			'items':[]
		}
		for i, doc in enumerate(itemJson['response']['docs']):
			if i==0:
				title = mainTitle
				pic = "http://108.61.126.123/static/images/360-2.png"
				url = "http://TODO-mysearchListPage.com"
			else:
				title = doc['name']
				if "pictureUrl" in doc:
					pic = doc['pictureUrl']
					if not pic.startswith("http://"):
						pic = "http://"+pic
				else:
					pic = "http://108.61.126.123/static/images/200.jpg"
				url = "http://TODO-itemDetailPage.com"
			context['items'].append({
				"title":title,
				"desc":"",
				"picUrl":pic,
				"url":url
				})

		return render(request, 'QueryResults.html', context)
	
	
	
def auth(request):
	print "AUTH"
	timestamp = request.GET.get('timestamp')
	nonce = request.GET.get('nonce')
	if timestamp and nonce and settings.WECHAT_TOKEN:
		params = [settings.WECHAT_TOKEN,timestamp,nonce]
		params.sort()
		sha1 = hashlib.sha1("".join(params)).hexdigest()
		signature = request.GET.get('signature')
		if sha1==signature:
			echoStr = request.GET.get('echostr')
			return HttpResponse(echoStr)
	return HttpResponse("FAIL")

def isNewMessage(elementTree):
	msgNode = elementTree.find('MsgId')
	if msgNode is not None:
		msgId = msgNode.text
		if msgId not in incomeMessageIds:
			incomeMessageIds.add(msgId)
			return True
		else:
			return False
	fromUserNode = elementTree.find('FromUserName')
	createTimeNode = elementTree.find('CreateTime')
	if fromUserNode is not None and createTimeNode is not None:
		fromUser = fromUserNode.text
		createTime = createTimeNode.text
		if (fromUser,createTime) not in incomeMessageFromAndTime:
			incomeMessageFromAndTime.add((fromUser,createTime))
			return True
		else:
			return False
	return False
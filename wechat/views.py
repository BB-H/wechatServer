from django.shortcuts import render
from django.http import HttpResponse
import hashlib

def auth(request):
	token = r"kDmr10bMVt3Yv6siPyPbctuRQ7SI9r2aHzO6wGLJWn4fmGhO_q_B3HoYI8Bxyv8wl1PkyvrXS9k_uD0vSI7NIyPK2XlCOvib3dZzyXCO4lLR39BxWYxZIeGtquVIPYIHWIAdAJALXP"
	timestamp = request.GET.get('timestamp')
	nonce = request.GET.get('nonce')
	
	params = [token,timestamp,nonce]
	params.sort()
	sha1 = hashlib.sha1("".join(params)).hexdigest()
	signature = request.GET.get('signature')
	
	if sha1==signature:
		echoStr = request.GET.get('echostr')
		return HttpResponse(echoStr)

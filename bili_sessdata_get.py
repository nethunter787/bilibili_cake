# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import urllib.request
import json
import time
import re

def urllib_useproxy(proxy=''):
    if proxy:
        proxy_support = urllib.request.ProxyHandler({
                'http'  : proxy,
                'https' : proxy,
                })
    else:
        proxy_support = urllib.request.ProxyHandler({
                })
    opener = urllib.request.build_opener(proxy_support)
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36'),
                         ]
    urllib.request.install_opener(opener)
    
urllib_useproxy()
qrurl      = 'http://passport.bilibili.com/qrcode/getLoginUrl'
checkurl   = 'http://passport.bilibili.com/qrcode/getLoginInfo'
qrurl_res  = urllib.request.urlopen(qrurl)
qrurl_json = json.loads(qrurl_res.read())
qroauthKey = qrurl_json['data']['oauthKey']
qrimg_url  = qrurl_json['data']['url']
# 有能力的同学自己使用Qrcode模块根据qrimg_url生成图片
print('打开网址【https://tool.oschina.net/qr】(Qr生成网站)\n将下面网址转换为二维码用bilibili手机客户端扫码:\n',qrimg_url,sep='') 
# 将form表单的元素进行编码，Post的提前准备操作
oauthKey_coded = urllib.parse.urlencode({'oauthKey':qroauthKey}).encode('utf-8')   #url编码
startCheckTime = time.time()
LastStatusData = None
while(True):
    endCheckTime = time.time()
    if(endCheckTime - startCheckTime) < 180.0: #如果超过180秒 停止检测
        loginInfoPostRes = urllib.request.urlopen(checkurl,oauthKey_coded)
        loginStatus_json = json.loads(loginInfoPostRes.read())
        if not loginStatus_json['status']: #如果未登录，则显示当前状态(已经扫码/未扫码)
            if LastStatusData == loginStatus_json['data']:
                # 显示正在查询
                print('.',end='')
            else:
                if loginStatus_json['data'] == -5:
                    print('\n已扫码,等待登录中',end='')
                if loginStatus_json['data'] == -4:
                    print('\n未扫码,等待扫码中',end='')
            # 延迟3秒 避免过度频繁查询
            LastStatusData = loginStatus_json['data']
            time.sleep(3)
        else: #登录成功，获取
            loginSESSDATA_raw = loginStatus_json['data']['url']
            break
    else:
        print('验证码失效超时,请重新登录')
        break

SESSDATA_Clue = re.compile(r'SESSDATA=(.*?)&bili_jct')
SESSDATA_Res  = re.findall(SESSDATA_Clue,loginSESSDATA_raw)[0]
print('\n登录成功，SESSDATA =',SESSDATA_Res)
    
# from urllib.request import urlretrieve
# import http.cookiejar 
# cookie = http.cookiejar.CookieJar()                                        #保存cookie，为登录后访问其它页面做准备  
# cjhdr  =  urllib.request.HTTPCookieProcessor(cookie)               
# opener = urllib.request.build_opener(cjhdr) 

# qrimg_path = 'C://Users/Administrator/Desktop'
# os.chdir(qrimg_path)
# urllib.request.urlretrieve(qrimg_url,'Bilibili_Login_QR_Code.jpg')


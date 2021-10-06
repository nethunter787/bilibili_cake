# -*- coding: utf-8 -*-
"""
I love FishC.com
                     -Sharpstar
"""

import os,sys
import qrcode
import urllib.request
import json
import time
import http.cookiejar
import re
import gzip
from io import BytesIO

def _progress(block_num, block_size, total_size):
    '''回调函数
       @block_num: 已经下载的数据块
       @block_size: 数据块的大小
       @total_size: 远程文件的大小
    '''
    sys.stdout.write('\r>> Downloading %.1f%%' % (
                     float(block_num * block_size) / float(total_size) * 100.0))
    sys.stdout.flush()

# 检测登录有效性 返回值：0 未登录 1 会员 2 大会员
def checklogin():
    check_url  = 'https://api.bilibili.com/x/web-interface/nav'     # 用户状态
    check_html = urllib.request.urlopen(check_url)
    check_json = json.loads(check_html.read())
    if check_json['data']['isLogin']:
        if check_json['data']['vipStatus']:
            return 2
        else:
            return 1
    else:
        return 0
    
# 二维码登录程序
def qrlogin():
    # 所用到的API网址
    qrurl      = 'http://passport.bilibili.com/qrcode/getLoginUrl'  # 登陆二维码
    checkurl   = 'http://passport.bilibili.com/qrcode/getLoginInfo' # 登陆状态
    # 获取二维码并显示
    qrurl_res  = urllib.request.urlopen(qrurl)
    qrurl_json = json.loads(qrurl_res.read())
    qroauthKey = qrurl_json['data']['oauthKey']
    qrimg_url  = qrurl_json['data']['url']
    qrcode.make(qrimg_url).show()
    # 扫码登陆 
    oauthKey_coded = urllib.parse.urlencode({'oauthKey':qroauthKey}).encode('utf-8')
    startCheckTime = time.time()
    LastStatusData = None
    while(True):
        endCheckTime = time.time()
        if(endCheckTime - startCheckTime) < 180.0: #限时180秒内完成扫码
            loginInfoPostRes = urllib.request.urlopen(checkurl,data=oauthKey_coded)
            loginStatus_json = json.loads(loginInfoPostRes.read()) # 当中包含SESSDATA
            if not loginStatus_json['status']: #如果未登录，则显示当前状态(已经扫码/未扫码)
                if LastStatusData == loginStatus_json['data']:
                    print('.',end='') # 显示正在查询
                else:
                    if loginStatus_json['data'] == -5:
                        print('\n已扫码,等待登录中',end='')
                    if loginStatus_json['data'] == -4:
                        print('\n未扫码,等待扫码中',end='')
                LastStatusData = loginStatus_json['data']
                time.sleep(3) # 延迟3秒 避免过度频繁查询
            else: 
                return True
        else:
            print('验证码失效超时,请重新登录')
            return False
        
# =============================================================================
# 预设
# =============================================================================
video_url   = 'https://www.bilibili.com/video/BV1rf4y1n78w' # 观测视频地址
video_url   = video_url.split('?')[0] #去除附带参数
sub_url     = 'https://t.bilibili.com/?tab=8'
proxy       = ''
UA          = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36'
# pag_api = 'https://api.bilibili.com/x/player/pagelist?bvid=BV1YP4y187cp'
# =============================================================================
# 登录,代理,Cookies
# =============================================================================
proxy_support = urllib.request.ProxyHandler({'http':proxy,'https':proxy}) if proxy else urllib.request.ProxyHandler({})
# 自动保存cookies
cookies_filename = 'bilibili_cookies.txt'
# cookiejar = http.cookiejar.CookieJar()  
cookiejar = http.cookiejar.MozillaCookieJar(cookies_filename) # 有save()
cookie_support = urllib.request.HTTPCookieProcessor(cookiejar)
# urllib钢铁侠安装各个组件
opener = urllib.request.build_opener(proxy_support,cookie_support)
opener.addheaders = [('User-Agent', UA),]
urllib.request.install_opener(opener) #使得所有urllib默认使用此opener
if not os.path.exists(cookies_filename):
    while(qrlogin() == False):None
    cookiejar.save() #保存cookie文件
else:
    cookiejar.load(cookies_filename)
    if not checklogin():# 登录信息过期.重新登录
        while(qrlogin() == False):None
        cookiejar.save() #保存cookie文件
# print('\nCookies:')
# for item in cookiejar:
#     print(item.name,'=',item.value)

# =============================================================================
# 视频信息获取
# =============================================================================
# # video_pages 内部元素
# #  {'cid': 394696432,
# #   'page': 8,
# #   'from': 'vupload',
# #   'part': '零距离 - 沙漠骆驼',
# #   'duration': 339,
# #   'vid': '',
# #   'weblink': '',
# #   'dimension': {'width': 1920, 'height': 1080, 'rotate': 0},
# #   'first_frame': 'http://i1.hdslb.com/bfs/storyff/n210822a21hlctgvi08o4e2hu9nrpvq3_firsti.jpg'}
# # videp_code 定义
# #    0：成功
# # -400：请求错误
# # -403：权限不足
# # -404：无视频
# # 62002：稿件不可见
# =============================================================================
# =============================================================================
video_html      = urllib.request.urlopen(video_url)
video_html_read = video_html.read()
buff = BytesIO(video_html_read)
f = gzip.GzipFile(fileobj=buff) # 读取内容需要gizp解码
video_html_read_extracted = f.read()
video_html_res = video_html_read_extracted.decode('utf-8')

downloadInfo_Clue = re.compile(r'__playinfo__=(.*?)</script><script>window')
downloadInfo_Res  = re.findall(downloadInfo_Clue,video_html_res)
downloadInfo_json = json.loads(downloadInfo_Res[0])
videoInfo_Clue    = re.compile(r'<script>window.__INITIAL_STATE__=(.*?);\(function\(\)')
videoInfo_Res     = re.findall(videoInfo_Clue,video_html_res)
videoInfo_json    = json.loads(videoInfo_Res[0])

# 获取视频基本信息
video_bvid     = videoInfo_json['bvid']                 # BV号
video_title    = videoInfo_json['videoData']['title']   # 标题
video_pubdate  = videoInfo_json['videoData']['pubdate'] # 发布日期(Unix时间戳)
video_cover    = videoInfo_json['videoData']['pic']     # 封面（URL）
video_pages    = videoInfo_json['videoData']['pages']   # 分P数信息（列表字典）
video_formats  = downloadInfo_json['data']['support_formats']     # 支持视频格式
video_code     = downloadInfo_json['code']
video_session  = downloadInfo_json['session']
video_download_url = downloadInfo_json['data']['dash']['video'][0]['baseUrl']
audio_download_url = downloadInfo_json['data']['dash']['audio'][0]['baseUrl']
# 发布者信息
video_up       = videoInfo_json['videoData']['owner']['name']      # UP主名字
video_up_uid   = videoInfo_json['videoData']['owner']['mid']       # UP主UID
video_up_face  = videoInfo_json['videoData']['owner']['face']      # UP主头像

# 视频质量衡量信息
video_view     = videoInfo_json['videoData']['stat']['view']       # 视频播放量
video_like     = videoInfo_json['videoData']['stat']['like']       # 视频点赞数
video_coin     = videoInfo_json['videoData']['stat']['coin']       # 视频硬币数
video_favorite = videoInfo_json['videoData']['stat']['favorite']   # 视频收藏数

print('标题        : %s'%video_title)
print('视频封面地址 : %s'%video_cover)
print('BV号        : %s'%video_bvid)
print('发布时间    :',time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(video_pubdate)))
print('支持视频格式 : ',end='')
for i in video_formats:
    print(i['new_description'],end=' ') 
print('\n共有%d个分P视频'%len(video_pages))
print('UP主     :%s 【UID:%d】'%(video_up,video_up_uid))
print('播放：%d,点赞：%d,硬币：%d,收藏：%d'%(video_view,video_like,video_coin,video_favorite))
bvid  = video_bvid
bvid_page = 0 # 选择集数
cid   = video_pages[bvid_page]['cid'] 
pname = video_pages[bvid_page]['part'] 
qn    = video_formats[0]['quality'] # 0位为最高清晰度
sess  = video_session
vdownapi = 'https://api.bilibili.com/x/player/playurl?cid=%d&bvid=%s&qn=%d&fnver=0&fnval=80&session=040fdbf639835a92741224fb9d3f51ed'%(cid,bvid,qn)
vdowninfo = urllib.request.urlopen(vdownapi)
vdowninfo_json = json.loads(vdowninfo.read())
vdownurl = vdowninfo_json['data']['dash']['video'][0]['baseUrl']
vdownurl_1 = vdowninfo_json['data']['dash']['video'][0]['base_url']
vdownurl_2 = vdowninfo_json['data']['dash']['video'][0]['backupUrl'][0]
adownurl = vdowninfo_json['data']['dash']['audio'][0]['baseUrl']

# vdownpath, _ = urllib.request.urlretrieve(vdownurl,'bvideo.m4s')
# adownpath, _ = urllib.request.urlretrieve(adownurl,'baudio.m4s')


# =============================================================================
# [{'quality': 112,
#   'format': 'hdflv2',
#   'new_description': '1080P 高码率',
#   'display_desc': '1080P',
#   'superscript': '高码率'},
#  {'quality': 80,
#   'format': 'flv',
#   'new_description': '1080P 高清',
#   'display_desc': '1080P',
#   'superscript': ''},
#  {'quality': 64,
#   'format': 'flv720',
#   'new_description': '720P 高清',
#   'display_desc': '720P',
#   'superscript': ''},
#  {'quality': 32,
#   'format': 'flv480',
#   'new_description': '480P 清晰',
#   'display_desc': '480P',
#   'superscript': ''},
#  {'quality': 16,
#   'format': 'mp4',
#   'new_description': '360P 流畅',
#   'display_desc': '360P',
#   'superscript': ''}]
# =============================================================================

"""
重要参考内容，致以无比感谢
【Github】 
SocialSisterYi/bilibili-API-collect
blogwy / BilibiliVideoDownload
"""
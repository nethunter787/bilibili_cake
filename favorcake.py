# -*- coding: utf-8 -*-
# =============================================================================
# 依赖环境
# 0.Anaconda Spyder (Tsinghua镜像站下载较快)
# 1.pip install qrcode (windows图标找到Anaconda prompt)
# 2. https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z 合成视频依赖FFmpeg拓展包(potplayer也依赖此)
# 3. (2022年5月2日新增) pip install bypy 然后运行 bypy info 通过激活码绑定百度云账户
# =============================================================================
import sys
import socket
import traceback
import threading
import queue
import contextlib
import os
import qrcode
import urllib.request
import json
import time
import http.cookiejar
import re
import gzip
import math
import ssl
# import bypy

from io import BytesIO
from urllib.error import HTTPError
global AllinOneFolder # 指定下载文件夹
# =============================================================================
# 用户参数配置
# UnixTimeSet 指开始记录的时刻 单位秒
# sleepsec 为检查周期 单位秒
# 如下配置示例视频将下载到路径为 E:\Bilight\DynamicVideos的 文件夹下面
# =============================================================================
UnixTimeSet = int(time.time())-6*60*60
sleepsec = 176 #检查投稿更新的周期
# work_path       = r'C:\Users\Administrator\Desktop\bilicake'
work_path       = os.getcwd()
# work_path       = '/home/ubuntu'
AllinOneFolder  = 'DynamicVideos'
baidu_dir_name  = 'bilicake_videos'
# =============================================================================
# 固定参数配置
# =============================================================================
global VideoFilter    # 视频过滤开关
global context    # 视频过滤开关
VideoFilter = False
cookies_filename        = 'bilibili_cookies_downloader.txt' # 默认与运行文件同目录
cookies_filename_9527   = 'bilibili_cookies_scriber.txt'
proxy       = ''
UA          = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
context     = ssl._create_unverified_context()

# =============================================================================
# 自定义函数部分
# =============================================================================


# ======================BVid 转换 AVid=========================================
table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF' # 码表
tr = {} # 反查码表
# 初始化反查码表
for i in range(58):
    tr[table[i]] = i
s = [11, 10, 3, 8, 4, 6] # 位置编码表
XOR = 177451812 # 固定异或值
ADD = 8728348608 # 固定加法值

def bv2av(x):
    r = 0
    for i in range(6):
        r += tr[x[s[i]]] * 58 ** i
    return (r - ADD) ^ XOR

def av2bv(x):
    x = (x ^ XOR) + ADD
    r = list('BV1  4 1 7  ')
    for i in range(6):
        r[s[i]] = table[x // 58 ** i % 58]
    return ''. join(r)

# ============================================================================
# 从api网站获取获取json
def getjson(api_url,data=None):
    response  = urllib.request.urlopen(api_url,data=data)
    data_json = json.loads(response.read())
    return data_json

# 设置网站归属参数
def getcakepage(url,data=None):
    url_req = urllib.request.Request(url)
    url_req.add_header('referer','https://www.bilibili.com/')
    response = urllib.request.urlopen(url_req, data=data)
    data_json = json.loads(response.read())
    return data_json

# # 基于urllib.request.urlretrieve 模块改写
# 增加添加headers功能 headers 为元组列表 [(key1, val1),(key2, val2),...]
# 去除本地本件/网络文件判断（只接受网络URL输入）
# 去除临时文件生成,必须指定文件名
# 注意：该模块不继承Opener的headers! Request()初始化阶段会有 self.headers = {}
def urlretrieve_evo(url, filename=None, data=None, headers=None):
    url_req = urllib.request.Request(url)
    if headers:
        for key, val in headers:
            url_req.add_header(key, val) #新的header将覆盖同名header,缺少则新增
    with contextlib.closing(urllib.request.urlopen(url_req, data,context=context)) as fp:
    # with contextlib.closing(urllib.request.urlopen(url_req, data)) as fp:   
        fp_info = fp.info()
        if filename:
            tfp = open(filename, 'wb')
        else:
            raise Exception('filename is not given.')
        with tfp:
            '''回调函数
            @blocknum: 已经下载的数据块
            @bs: 数据块的大小
            @size: 远程文件的大小
            '''
            # result = filename, headers
            bs = 1024*8
            size = -1
            read = 0
            blocknum = 0
            if "content-length" in fp_info:
                size = int(fp_info["Content-Length"])
            while True:
                block = fp.read(bs)
                if not block:
                    break
                read += len(block)
                tfp.write(block)
                blocknum += 1
                # 显示下载进度
                # sys.stdout.write('\r>> Downloading %s %.1f%% %.1fKB   ' % (filename, (float(blocknum * bs) / float(size) * 100.0), (float(blocknum * bs) / 1024.0)))
                # sys.stdout.flush()
    return size


# 加载初始化文件
def cake_init(cookies_filename = 'bilibili_cookies.txt',
              UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
              ):
    socket.setdefaulttimeout(60) # 设置60秒超时
    proxy_support = urllib.request.ProxyHandler({'http':proxy,'https':proxy}) if proxy else urllib.request.ProxyHandler({})
    cookiejar = http.cookiejar.MozillaCookieJar(cookies_filename) # 加载cookies内容 cookiejar.save()能够保存文件
    cookie_support = urllib.request.HTTPCookieProcessor(cookiejar)
    opener = urllib.request.build_opener(proxy_support,cookie_support)# urllib钢铁侠组配
    opener.addheaders = [('User-agent', UA)]
    urllib.request.install_opener(opener) #urllib钢铁侠开机初始化
    return cookiejar


# 检测登录有效性 返回值：0 未登录 1 会员 2 大会员
def checklogin():
    check_url  = 'https://api.bilibili.com/x/web-interface/nav'     # 用户状态
    try:
        check_json = getjson(check_url)
        if check_json['data']['isLogin']:
            if check_json['data']['vipStatus']:
                print('VIP is Login')
                return 2
            else:
                print('Normal is Login')
                return 1
        else:
            print('Not Login')
            return 0
    except Exception:
        print('[×] 无法获取登录账号信息')
        traceback.print_exc()
        return 0


# 二维码登录程序 返回值：True 已登录 False 超时未登陆
def qrlogin():
    # 所用到的API网址
    qrurl      = 'https://passport.bilibili.com/qrcode/getLoginUrl'  # 登陆二维码
    checkurl   = 'https://passport.bilibili.com/qrcode/getLoginInfo' # 登陆状态
    # 获取二维码并显示
    qrurl_json = getjson(qrurl)
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
            loginInfoPostRes = urllib.request.urlopen(checkurl,data=oauthKey_coded) # Post方法
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
                print('登陆成功')
                return True
        else:
            print('验证码失效超时,请重新登录')
            return False
        
        
# 傻瓜式一步到位登录
def cake_login(cookies_filename):
    cookiejar = cake_init(cookies_filename)
    if not os.path.exists(cookies_filename):
        print('首次登陆，第一个二维码扫关注账号，第二个二维码扫会员下载账号。')
        while(qrlogin() == False):print('[×] 超时请重新登陆')
        cookiejar.save() #保存cookie文件
    else:
        cookiejar.load(cookies_filename)
        if not checklogin():# 登录信息过期.重新登录
            while(qrlogin() == False):print('[×] 超时请重新登陆')
            cookiejar.save() #保存cookie文件
    return cookiejar
# 查询订阅组的编号 tagid打印
def getTagid():
    mySubscribeGroups = getjson('https://api.bilibili.com/x/relation/tags')
    for i in mySubscribeGroups['data']:
        print('tagid = %10d : name = %10s'%(i['tagid'],i['name']))

        
# 查订阅组下的所有UP的信息 输入tagid 输出字典列表 uid name face
def getSubscribUps(tagid):
    api  = 'https://api.bilibili.com/x/relation/tag?tagid=%d'%tagid
    data_json = getjson(api)
    up_list = []
    for each_up in data_json['data']:
        up_list.append({'uid':each_up['mid'],
                        'name':each_up['uname'],
                        'face':each_up['face'],
                        })
    return up_list

# 获取用户信息
def getUpName(mid):
    try:
        mid = str(mid)
        time.sleep(0.5)
        up_info_api  = 'https://api.bilibili.com/x/space/acc/info?mid=%s'%mid
        up_info_data = getjson(up_info_api)
        return up_info_data['data']['name']#返回名称
    except:
        return None
    
# 输入uid 返回投稿视频的字典列表
def getUpVideos(up_uid,startpage=1,endpage=10,tid=0,keyword=''):
    up_videos = []
    for space_video_page in range(startpage,endpage+1): #最多下载10页 300个视频
        time.sleep(3) # 频率不宜过快
        space_video_search_params_dict={'mid' : up_uid, # UP主UID
                                        'ps'  : 30,    # 每页的视频个数
                                        'tid' : tid,      # 分区筛选号 0为不筛选
                                        'pn'  : space_video_page,      # 页码
                                        'keyword':keyword,   # 搜索关键词
                                        'order':'pubdate',# 降序排序 click(播放)/stow(收藏)
                                        }
        space_video_search_params_urlcoded = urllib.parse.urlencode(space_video_search_params_dict)
        up_videos_api = 'https://api.bilibili.com/x/space/arc/search?%s'%space_video_search_params_urlcoded
        space_video_search_json = getjson(up_videos_api)
        if space_video_page == startpage:
            #获取分类表 如果该页无视频则返回None
            # tlist = space_video_search_json['data']['list']['tlist']
            # for each in tlist :
            #     print('tid:',tlist[each]['tid'],'类名:',tlist[each]['name'],'数目:',tlist[each]['count'])

            #获取视频总数 如果该页无视频则返回0
            space_video_num = space_video_search_json['data']['page']['count']
            
        if space_video_search_json['data']['list']['vlist']: #如果不存在视频则为空列表[]
            thisPageVideos = space_video_search_json['data']['list']['vlist']
            thisPageVideos.reverse()
            thisPageVideos_num = len(thisPageVideos)
            for each_video_id in range(thisPageVideos_num):
                each_video_info = thisPageVideos[thisPageVideos_num-each_video_id-1]
                # up_videos格式
                up_videos.append({'title':each_video_info['title'],
                                  'bvid':each_video_info['bvid'],
                                  'author':each_video_info['author'],
                                  'mid':each_video_info['mid'],
                                  'created':each_video_info['created'],
                                  })
            
            if space_video_page == endpage:
                print('[√] 已获取 [%d/%d] 个视频'%(len(up_videos),space_video_num))
                return up_videos 
        else:#这页不存在视频
            print('[√] 已获取 [%d/%d] 个视频'%(len(up_videos),space_video_num))
            return up_videos
        

def getUnixTimeSet(filename):
    with open(filename) as f:
        DynamicVideos = json.load(f)
    if DynamicVideos:
        UnixTimeSet = DynamicVideos[0]['UnixTime']
    else:
        print('%s文件为空，自动查询一天前'%filename)
        UnixTimeSet = int(time.time()) - 24*60*60
    return UnixTimeSet

# https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_history?uid=599674252&offset_dynamic_id=578820776706551009&type=8&from=&platform=web
# https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_new?uid=599674252&type_list=8&from=&platform=web
# 获取20条最新动态视频BV号
def getDynamicVideos(UnixTimeSet):
    # 获取现在到截止日期UnixTimeSet的所有关注视频动态。
    dynamicVideo_api  = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_new?type_list=8&platform=web'
    try:
        dynamicVideo_json = getjson(dynamicVideo_api)
    except:
        return None
    allDynamicVideos  = dynamicVideo_json['data']['cards'] #每次获得二十条
    # my_attention_list = dynamicVideo_json['data']['attentions'] # 获得我关注的所有uid(包括我自己)
    # max_dynamic_id = dynamicVideo_json['data']['max_dynamic_id'] # The Newest Dynamic ID
    history_offset = dynamicVideo_json['data']['history_offset'] # The Last One
    allDynamicVideos_Lite = []
    # 获取第一页
    for each_video in allDynamicVideos:
        vcard = json.loads(each_video['card'])
        # each_video['desc']['type'] = 8-投稿视频 2-照片动态 4308-直播通知
        allDynamicVideos_Lite.append({'up_uid':each_video['desc']['user_profile']['info']['uid'],
                                      'up_name':each_video['desc']['user_profile']['info']['uname'],
                                      'title':vcard['title'],
                                      'like':vcard['stat']['like'],
                                      'favorite':vcard['stat']['favorite'],
                                      'bvid':each_video['desc']['bvid'],
                                      'time':time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(each_video['desc']['timestamp'])),
                                      'UnixTime':each_video['desc']['timestamp'],
                                      'dynamic_id':each_video['desc']['dynamic_id'],
                                      })
    # 获取后续
    while allDynamicVideos_Lite[-1]['UnixTime'] > UnixTimeSet :
        dynamicVideo_api  = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_history?uid=599674252&offset_dynamic_id=%d&type=8&from=&platform=web'%history_offset
        dynamicVideo_json = getjson(dynamicVideo_api)
        allDynamicVideos  = dynamicVideo_json['data']['cards'] 
        history_offset    = dynamicVideo_json['data']['next_offset'] 
        for each_video in allDynamicVideos:
            vcard = json.loads(each_video['card'])
            allDynamicVideos_Lite.append({'up_uid':each_video['desc']['user_profile']['info']['uid'],
                                          'up_name':each_video['desc']['user_profile']['info']['uname'],
                                          'title':vcard['title'],
                                          'like':vcard['stat']['like'],
                                          'favorite':vcard['stat']['favorite'],
                                          'bvid':each_video['desc']['bvid'],
                                          'time':time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(each_video['desc']['timestamp'])),
                                          'UnixTime':each_video['desc']['timestamp'],
                                          'dynamic_id':each_video['desc']['dynamic_id'],
                                          })
    # 由于每次获取20条，可能会超过边界 从末尾开始删除超边界元素。
    while (True):
        if allDynamicVideos_Lite[-1]['UnixTime'] <= UnixTimeSet:
            allDynamicVideos_Lite.pop(-1)
            if not allDynamicVideos_Lite:
                break
        else:
            break
    return allDynamicVideos_Lite


# 获取收藏夹内容
# https://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid=702240869
# 获取用户所有收藏夹的media_id
def getCollectVideos(media_id,startpage=1,endpage=10,keyword='',tid=0):
    collect_videos = []
    for pagenum in range(startpage,endpage+1):
        api_param = {'media_id' : media_id,
                     'pn' : pagenum,
                     'ps' : 20,
                     'keyword' : keyword,
                     'order':'mtime',
                     'type' : 0,
                     'tid' : tid,
                     'platform':'web',
                     }
        api = 'https://api.bilibili.com/x/v3/fav/resource/list?%s'%urllib.parse.urlencode(api_param)
        api_json = getjson(api)
        medias = api_json['data']['medias']
        if medias:
            for each in medias:
                collect_videos.append({'bvid':each['bvid'],
                               'title':each['title'],
                               'up_uid':each['upper']['mid'],
                               'up_name':each['upper']['name'],
                               'pubtime':each['pubtime'],
                               })
    collect_videos.reverse()
    return collect_videos


# 获取视频状态：播放量点赞投币收藏 
def getVideoState(bvid):
    video_state_params = {'bvid':bvid}
    video_state_params_urlcoded = urllib.parse.urlencode(video_state_params)
    video_state_api = 'https://api.bilibili.com/x/web-interface/archive/stat?%s'%video_state_params_urlcoded
    video_state_json = getjson(video_state_api)
    video_state = {'view':video_state_json['view'],
                  'like':video_state_json['like'],
                  'coin':video_state_json['coin'],     
                  'save':video_state_json['favorite'], # 收藏数
                  }
    return video_state

def getBVInfo(bvid):
    # 访问视频页面
    video_url       = 'https://www.bilibili.com/video/%s'%bvid
    video_html      = urllib.request.urlopen(video_url)
    video_html_rd   = video_html.read()
    # 网页内容需要gizp解码
    buff            = BytesIO(video_html_rd)
    f               = gzip.GzipFile(fileobj=buff) 
    html_unpacked   = f.read()
    video_html_res  = html_unpacked.decode('utf-8')
    downloadInfo_Clue = re.compile(r'__playinfo__=(.*?)</script><script>window')
    downloadInfo_Res  = re.findall(downloadInfo_Clue,video_html_res)
    videoInfo_Clue    = re.compile(r'<script>window.__INITIAL_STATE__=(.*?);\(function\(\)')
    videoInfo_Res     = re.findall(videoInfo_Clue,video_html_res)
    downloadInfo_json = {}
    videoInfo_json    = {}
    if downloadInfo_Res and videoInfo_Res:
        downloadInfo_json = json.loads(downloadInfo_Res[0])
        videoInfo_json    = json.loads(videoInfo_Res[0])
    else:
        print('[×] 稿件被删除 \nhttps://www.bilibili.com/video/%s'%bvid)
        return None
    if not downloadInfo_json:# 检测网页是否获取到Json
        print('[×] Error: Info_Json \nhttps://www.bilibili.com/video/%s'%bvid)
        return None
    if not 'bvid' in videoInfo_json:# 检测网页格式是否正确
        print('[×] Error: videoInfo_json Type \nhttps://www.bilibili.com/video/%s'%bvid)
        return None
    # bv_info = {'downloadInfo':downloadInfo_json,'videoInfo_json':videoInfo_json}
    video_like     = videoInfo_json['videoData']['stat']['like']       # 视频点赞数
    video_favorite = videoInfo_json['videoData']['stat']['favorite']   # 视频收藏数
    video_score = int((((video_favorite+10)/(video_like+10))**2)*10) # 视频分数计算公式
    # video_score_new = video_score+int((math.log10(video_favorite+100)-2)**2) # 根据人气适当的加0~7分通过门限
    return video_score

# 输入视频BVid下载其所有分集
def downloader_BV(up_video_bvid,Filter=False,Folder_Path='.',Folder=''):
    time.sleep(0.2)
    try:
        up_video_name = ''

    # 访问视频页面
        video_url       = 'https://www.bilibili.com/video/%s'%up_video_bvid
        video_html      = urllib.request.urlopen(video_url)
        video_html_rd   = video_html.read()
    # 网页内容需要gizp解码
        buff            = BytesIO(video_html_rd)
        f               = gzip.GzipFile(fileobj=buff) 
        html_unpacked   = f.read()
        video_html_res  = html_unpacked.decode('utf-8')
        downloadInfo_Clue = re.compile(r'__playinfo__=(.*?)</script><script>window')
        downloadInfo_Res  = re.findall(downloadInfo_Clue,video_html_res)
        videoInfo_Clue    = re.compile(r'<script>window.__INITIAL_STATE__=(.*?);\(function\(\)')
        videoInfo_Res     = re.findall(videoInfo_Clue,video_html_res)
        downinfo_json = {}
        videoInfo_json= {}
        if downloadInfo_Res and videoInfo_Res:
            downloadInfo_json = json.loads(downloadInfo_Res[0])
            videoInfo_json    = json.loads(videoInfo_Res[0])
        else:
            return {'flag':False,'bvid':up_video_bvid,'name':up_video_name,'msg':'Info_Res Error'}
        if not downloadInfo_json:# 检测网页是否获取到Json
            return {'flag':False,'bvid':up_video_bvid,'name':up_video_name,'msg':'Info_Json Error'}
        if not 'bvid' in videoInfo_json:# 检测网页格式是否正确
            return {'flag':False,'bvid':up_video_bvid,'name':up_video_name,'msg':'videoInfo_json Type Error'}
    # 获取视频基本信息
        video_bvid     = videoInfo_json['bvid']                 # BV号
        video_title    = videoInfo_json['videoData']['title']   # 标题
        up_video_bvid  = video_bvid
        up_video_name  = video_title
        video_pubdate  = videoInfo_json['videoData']['pubdate'] # 发布日期(Unix时间戳)
        video_cover_url= videoInfo_json['videoData']['pic']     # 封面（URL）
        video_pages    = videoInfo_json['videoData']['pages']   # 分P信息（列表字典）
        # video_formats  = downloadInfo_json['data']['support_formats']  # 支持视频格式
        video_highest_format_qn     = downloadInfo_json['data']['support_formats'][0]['quality'] # 支持的最大视频质量ID
        video_highest_format_desc   = downloadInfo_json['data']['support_formats'][0]['new_description'] # 视频质量描述
        # video_code     = downloadInfo_json['code']
        video_session  = downloadInfo_json['session']
    # UP主信息
        video_up_name  = videoInfo_json['videoData']['owner']['name']      # UP主名字
        video_up_uid   = videoInfo_json['videoData']['owner']['mid']       # UP主UID

        # video_up_face  = videoInfo_json['videoData']['owner']['face']      # UP主头像
    # 视频质量衡量信息
        # video_view     = videoInfo_json['videoData']['stat']['view']       # 视频播放量
        video_like     = videoInfo_json['videoData']['stat']['like']       # 视频点赞数
        # video_coin     = videoInfo_json['videoData']['stat']['coin']       # 视频硬币数
        video_favorite = videoInfo_json['videoData']['stat']['favorite']   # 视频收藏数
    # 计算分数
        video_score = int((((video_favorite+10)/(video_like+10))**2)*10) # 视频分数计算公式
        video_score_new = video_score+int((math.log10(video_favorite+100)-2)**2) # 根据人气适当的加0~7分通过门限
        video_play_msg = '%d赞 %d藏 %d分 日期：%s'%(video_like,video_favorite,video_score,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(video_pubdate)))
        if Filter:
            if video_pubdate < 1557382308 or video_score_new < 7: #2019年5月以前的不下载
                print('[×] 视频不满足下载条件，已过滤。\n发布者：%s\n标题：%s\n数据：%s\n网址：https://www.bilibili.com/video/%s\n'%(video_up_name,video_title,video_play_msg,video_bvid))
                return {'flag':True,'bvid':up_video_bvid,'name':up_video_name,'msg':'[×] Not pass:%s'%video_play_msg}
            # 发布超过一个月 且收藏少 得分少 60*60*24*30 = 2592000
            if video_score <= 10 and video_favorite < 1000 and int(time.time()) - video_pubdate > 2592000:
                print('[×] 视频不满足下载条件，已过滤。\n发布者：%s\n标题：%s\n数据：%s\n网址：https://www.bilibili.com/video/%s\n'%(video_up_name,video_title,video_play_msg,video_bvid))
                return {'flag':True,'bvid':up_video_bvid,'name':up_video_name,'msg':'[×] Not pass:%s'%video_play_msg}
        
        pic_folder_name = '%s//%s_pic'%(Folder_Path,Folder)
        os.mkdir(pic_folder_name) if not os.path.exists(pic_folder_name) else None
        
        if Folder:
            video_folder_name = '%s//%s'%(Folder_Path,Folder)
            os.mkdir(video_folder_name) if not os.path.exists(video_folder_name) else None
        else:
            # 确定下载文件夹
            foldar_name_with_uid = [i for i in os.listdir(Folder_Path) if i.split('_')[-1] == str(video_up_uid)]
            if foldar_name_with_uid: # 先查询是否已经存在UP视频文件夹(通过检测后缀uid)
                video_folder_name = '%s//%s'%(Folder_Path,foldar_name_with_uid[0])
            else: # 没有则新建UP视频文件夹
                video_folder_name = '%s//%s_%d'%(Folder_Path,video_up_name,video_up_uid)
                os.mkdir(video_folder_name) if not os.path.exists(video_folder_name) else None
        # 开始分页下载
        for bvid_page in range(1,len(video_pages)+1):
            # 输入视频基本信息
            bvid  = video_bvid
            cid   = video_pages[bvid_page-1]['cid'] 
            # pname = video_pages[bvid_page-1]['part'] 
            sess  = video_session
            # qn    = video_formats[0]['quality'] # 0位为最大清晰度
            qn = 127
            # 获取最高画质音质的下载链接
            downapi = 'https://api.bilibili.com/x/player/playurl?cid=%d&bvid=%s&qn=%d&type=&otype=json&fourk=1&fnver=0&fnval=2000&session=%s'%(cid,bvid,qn,sess)
            downinfo_json = getjson(downapi)
            video_download_list = downinfo_json['data']['dash']['video']
            audio_download_list = downinfo_json['data']['dash']['audio']
            video_download_list_sorted = sorted(video_download_list,key=lambda x:x['id'],reverse=True) #按id降序
            audio_download_list_sorted = sorted(audio_download_list,key=lambda x:x['id'],reverse=True) 
            video_download_url = video_download_list_sorted[0]['baseUrl'] # 最高画质
            audio_download_url = audio_download_list_sorted[0]['baseUrl']
            if(video_highest_format_qn != video_download_list_sorted[0]['id']):
                print('[!]qn_max = %d , qn_now = %d\n'%(video_highest_format_qn,video_download_list_sorted[0]['id']))
                video_quality_desc = 'Unknow_%d'%video_download_list_sorted[0]['id']
            else:
                video_quality_desc = video_highest_format_desc
            # 确定下载文件名和路径
            detect_str = '%d]_%s.mp4'%(bvid_page,video_bvid)
            file_name_with_puid = [i for i in os.listdir(video_folder_name) if i.split('[P')[-1] == detect_str]
            if file_name_with_puid: # 能够查询到说明存在该bvid后缀的mp4文件
                print("[√] 视频已存在。\n%s[P%d]"%(video_title,bvid_page))# 跳过重复文件下载
                continue 
            else:
                video_filename_raw = "【%02d】【%s】【%s】%s_%s_[P%d]_%s"%(video_score,video_up_name,video_quality_desc,video_title,video_up_uid,bvid_page,video_bvid)
                video_filename_new = re.sub('[^A-Za-z0-9\u4e00-\u9fa5【】\[\]_]+', '', video_filename_raw) # 字符筛选
                video_downpath = '%s//%s'%(video_folder_name,video_filename_new)
                pic_downpath = '%s//%s'%(pic_folder_name,video_filename_new)
                # 破解防盗链并下载视频
                referer_url  = video_url if bvid_page == 1 else '%s?p=%d'%(video_url,bvid_page)
                urlretrieve_evo_headers = [('referer', referer_url),('User-agent', UA)]
                # 封面下载
                try:
                    urlretrieve_evo(video_cover_url,filename='%s.jpg'%pic_downpath,headers=urlretrieve_evo_headers)
                except HTTPError:
                    print('[×] %s 封面下载失败'%up_video_bvid)
                # 视频下载
                try:
                    if len(video_download_list_sorted)>0:
                        video_download_url = video_download_list_sorted[0]['baseUrl'] # 备用链接
                        Vsize = urlretrieve_evo(video_download_url,filename='%s_Video.m4s'%video_downpath,headers=urlretrieve_evo_headers)
                    else:
                        raise Exception('VideoDownSource-1 not aviliable')
                except HTTPError:
                    print('[×] %s下载失败,尝试第二次'%up_video_bvid)
                    if len(video_download_list_sorted)>1:
                        video_download_url_bak = video_download_list_sorted[0]['baseUrl'] # 备用链接
                        Vsize = urlretrieve_evo(video_download_url_bak,filename='%s_Video.m4s'%video_downpath,headers=urlretrieve_evo_headers)
                    else:
                        raise Exception('VideoDownSource-2 not aviliable')
                # 音频下载
                try:
                    if len(video_download_list_sorted)>0:
                        audio_download_url = audio_download_list_sorted[0]['baseUrl']
                        Asize = urlretrieve_evo(audio_download_url,filename='%s_Audio.m4s'%video_downpath,headers=urlretrieve_evo_headers)
                    else:
                        raise Exception('AudioDownSource-1 not aviliable')
                except HTTPError:
                    print('[×] %s下载失败,尝试第二次'%up_video_bvid)
                    if len(video_download_list_sorted)>1:
                        audio_download_url_bak = audio_download_list_sorted[0]['baseUrl']
                        Asize = urlretrieve_evo(audio_download_url_bak,filename='%s_Audio.m4s'%video_downpath,headers=urlretrieve_evo_headers)
                    else:
                        raise Exception('AudioDownSource-2 not aviliable')
                
                # 使用ffmpeg合成视频
                cmd_str = 'ffmpeg -i %s_Video.m4s -i %s_Audio.m4s -codec copy %s.mp4'%(video_downpath,video_downpath,video_downpath)
                # cmd_res = os.popen(cmd_str)
                # cmd_res.close()
                ffmpeg_start_time = time.time()
                os.system(cmd_str) 
                while(time.time() - ffmpeg_start_time<120):
                    time.sleep(2) # 等待合成结束，同时防止爬取速度过快。
                    if os.path.exists('%s.mp4'%video_downpath):
                        break
                    else:
                        print('[-]视频合成中...')
                
                # 删除视频音频文件残留
                try: os.remove('%s_Video.m4s'%video_downpath)
                except Exception: None
                try: os.remove('%s_Audio.m4s'%video_downpath)
                except Exception: None
                print("[√] 下载成功。(%4.1f MB)\n发布者：%s\n视频名：%s[P%d]\n数据：%s"%((Vsize+Asize)/1048576,video_up_name,video_title,bvid_page,video_play_msg))
        return {'flag':True,'bvid':up_video_bvid,'name':up_video_name,'msg':'[√] 下载成功'}
    except HTTPError:
        error_msg = '[×] HTTPError:【%s】%s'%(up_video_bvid,up_video_name)
        print(error_msg)
        try: os.remove('%s_Video.m4s'%video_downpath)
        except Exception: None
        try: os.remove('%s_Audio.m4s'%video_downpath)
        except Exception: None
        return {'flag':False,'bvid':up_video_bvid,'name':up_video_name,'msg':error_msg}
    
    except Exception:
        error_msg = '[×] Failed:【%s】%s'%(up_video_bvid,up_video_name)
        print(error_msg)
        try: os.remove('%s_Video.m4s'%video_downpath)
        except Exception: None
        try: os.remove('%s_Audio.m4s'%video_downpath)
        except Exception: None
        traceback.print_exc()
        return {'flag':False,'bvid':up_video_bvid,'name':up_video_name,'msg':error_msg}


def thread_downloader_BV(name,this_bvid_queue,this_bvid_failed_queue):
    while(True):
        try:
            if this_bvid_queue.empty():
                break
            up_video_bvid = this_bvid_queue.get(timeout = 2)
        except queue.Empty:
            break
        res_dict = downloader_BV(up_video_bvid,Filter=VideoFilter,Folder_Path=work_path,Folder=AllinOneFolder)
        if not res_dict['flag'] :# 当程序遇到错误时。记录错误信息
            this_bvid_failed_queue.put((res_dict['bvid'],res_dict['name'],res_dict['msg']))
    print('[√] %s finished.'%name)

        
# 运行多线程【队列消息传递】
def runThreads(func,Queue_input,threadsnum=4,wait=True):
    Queue_output = queue.Queue()
    Pool_threads = [threading.Thread(target=func, args=('Thread[%d]'%i,Queue_input,Queue_output)) for i in range(threadsnum)]
    for thread_each in Pool_threads: 
        thread_each.start() # 启动线程
    
    # while Queue_input.empty() == False:
    #     time.sleep(10) #每隔5秒监测一次死进程
    #     dead_thread_ids = []
    #     for each_thread in Pool_threads:
    #         if each_thread.isAlive():
    #             None
    #         else:
    #             thread_id = Pool_threads.index(each_thread)
    #             dead_thread_ids.append(thread_id)
    #             print('[×] Thread[%d] 中断'%thread_id)
    #     for dead_thread_id in dead_thread_ids:
    #         Pool_threads[dead_thread_id] = threading.Thread(target=func, args=('Thread[%d]'%dead_thread_id,Queue_input,Queue_output))
    #         Pool_threads[dead_thread_id].start()
    #         print('[√] Thread[%d] 重建'%dead_thread_id)   
    if wait: 
        start_time = time.time()
        for thread_each in Pool_threads: thread_each.join()  # 等待结束
        end_time   = time.time()
        print('[-] 线程耗时:',time.strftime("%H:%M:%S", time.gmtime(end_time-start_time)))
    return Queue_output

# 加载json文件
def loadjson(filepath):
    json_dict = {}
    with open(filepath,"r") as frjson:
        json_dict = json.load(frjson)
    return json_dict

# 更新json
def savejson(json_dict,filepath):
    with open(filepath,"w") as fwjson:
        json.dump(json_dict,fwjson)
    return True

def cakenamevalidate(vfilename):
    vsplit = vfilename.split('.')
    if(len(vsplit)>1):
        videoname = vsplit[-2]
        bvid = videoname.split('_')[-1]
        if(videoname.split('_')[-1][0:2]=='BV' and vsplit[-1] == 'mp4'): #符合规范
            return [bvid,videoname]
        else:
            return []
# 获取文件夹内的合法规范的bvid列表
def getfolderbvlist(folderpath):
    bvlist = {}
    if os.path.exists(folderpath):
        for video in os.listdir(folderpath):
            validate_res = cakenamevalidate(video)
            if validate_res:
                bvlist[validate_res[0]] = validate_res[1] # {bvid : videoname}
    return bvlist

# 更新文件夹内的所有视频状态
def updatefolder(folderpath,ScoreUpdate = False):
    if os.path.exists(folderpath):
        for folderfilename in os.listdir(folderpath):
            validate_res = cakenamevalidate(folderfilename)
            if validate_res:
                bvid = validate_res[0]
                videoname = validate_res[1]
                if videoname[0:3] != '【删】':
                    try:
                        video_score = getBVInfo(bvid)
                        time.sleep(0.2)
                        if video_score == None: # 如果文件已经被删除则标识出来
                            newfolderfilename = '【删】%s'%folderfilename
                            lastpath = os.path.join(folderpath,folderfilename)
                            newpath = os.path.join(folderpath,newfolderfilename)
                            os.rename(lastpath,newpath)
                            print('[!]被删除：%s'%newfolderfilename)
                        else:# 如果文件未删除 则更新分数状态
                            if(ScoreUpdate):
                                # 更新视频分数
                                newfolderfilename = '【%02d】【%s' % (video_score,folderfilename.split('】【')[-1])
                                lastpath = os.path.join(folderpath,folderfilename)
                                newpath = os.path.join(folderpath,newfolderfilename)
                                os.rename(lastpath,newpath)
                                print('%s ->\n%s'%(folderfilename,newfolderfilename))
                    except:
                        print('[×]getBVInfo error: %s'%videoname)


def favortitle(media_id):
    favorInfo_api = 'http://api.bilibili.com/x/v3/fav/folder/info?media_id=%s'%media_id
    favorInfo_json = getcakepage(favorInfo_api)
    return favorInfo_json['data']['title']


# favorcakemove('BV1B8411n75X',['1849465733'],['1685042233'],cookiejar)
def favorcakemove(cookiejar,bvid,src_media_id,tar_media_id):
    for cookie in cookiejar:
        if cookie.name == 'bili_jct': # cookie中此项为csrf
            csrf = cookie.value
    favorcakemove_params = {'src_media_id':','.join(src_media_id),
                          'tar_media_id':','.join(tar_media_id),
                          'resources':'%s:2'%bv2av(bvid),
                          'platform':'web',
                          'csrf':csrf,
                          }
    favorcakemove_params_urlcoded = urllib.parse.urlencode(favorcakemove_params)
    favorcakemove_api = 'https://api.bilibili.com/x/v3/fav/resource/move'
    favorcakemove_json = getcakepage(favorcakemove_api,data=favorcakemove_params_urlcoded.encode('utf-8'))
    # Json格式 {'code': 0, 'message': '0', 'ttl': 1, 'data': 0}
    return favorcakemove_json



print('[-] [收藏夹下载模式]')
cookiejar = cake_login(cookies_filename)
media_id = '1685042233'
work_path = os.getcwd()
AllinOneFolder = 'myfavorcake_down'
#获取收藏夹文件
collect_videos   = getCollectVideos(media_id=media_id)
for collect_video in collect_videos:
    res_downBV = downloader_BV(collect_video['bvid'],Filter=False,Folder_Path=work_path,Folder=AllinOneFolder)
    if(res_downBV['flag'] == False):
        time.sleep(2)
        print('[×]该视频 %s 重新下载中！！！！'%collect_video['bvid'])
        res_downBV = downloader_BV(collect_video['bvid'],Filter=False,Folder_Path=work_path,Folder=AllinOneFolder)
    favorcakemove(cookiejar,collect_video['bvid'],['1685042233'],['1849465733'])

cookiejar = cake_login(cookies_filename_9527)
media_id = '1852811852'
work_path = os.getcwd()

#获取收藏夹文件
collect_videos   = getCollectVideos(media_id=media_id)
for collect_video in collect_videos:
    res_downBV = downloader_BV(collect_video['bvid'],Filter=False,Folder_Path=work_path,Folder=AllinOneFolder)
    if(res_downBV['flag'] == False):
        time.sleep(2)
        print('[×]该视频 %s 重新下载中！！！！'%collect_video['bvid'])
        res_downBV = downloader_BV(collect_video['bvid'],Filter=False,Folder_Path=work_path,Folder=AllinOneFolder)
    favorcakemove(cookiejar,collect_video['bvid'],['1852811852'],['1848295752'])


# VideoFilter = False
# input_list_bvid = ['BV1Yt411m7kA','BV1ts411w7CR',]
# # 将bvid输入下载队列
# input_list_bvid  = []
# Queue_input_bvid = queue.Queue()
# for bvid in input_list_bvid: Queue_input_bvid.put(bvid)
# # 运行多线程下载
# Queue_output_bvid = runThreads(thread_downloader_BV,Queue_input_bvid,threadsnum=2)

# # 输出队列信息处理
# videos_failed   = []
# while not Queue_output_bvid.empty(): 
#     bvid,name,msg = Queue_output_bvid.get()
#     videos_failed.append({'bvid':bvid,'name':name,'msg':msg})
# # 打印出下载失败的视频
# for video in videos_failed: 
#     print('[×] %s %s\nhttps://www.bilibili.com/video/%s'%(video['bvid'],video['msg'],video['bvid']))

# =============================================================================
# 主函数结束
# =============================================================================

# 版本更新日志 20220719
# 收藏夹下载的功能 使用多线程下载
"""
重要参考内容，致以无比感谢
【Github】 
SocialSisterYi/bilibili-API-collect
blogwy / BilibiliVideoDownload
"""

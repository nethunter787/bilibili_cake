# -*- coding: utf-8 -*-
"""
Created on Sat Sep  3 10:18:08 2022

@author: Administrator

List All the folder links in Markdown File 
and all the img_src

"""
import os
import time
time_str = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(time.time()))
bvfolder = r'Z:\DynamicVideos'
bvfilenum = 0
with open('BiliCakeMarkdown_%s.md'%time_str,'w+',encoding="utf-8") as f:
    f.write('# MarkCake %s\n\n'%time_str)
    f.write('\n 【超极】 【极】 【精】 【露】 【露下】 【露下】 【极露】 【抖】 \n')
    if os.path.exists(bvfolder):
        bvfilelist = os.listdir(bvfolder)
        bvfilelist.sort(reverse=True)
        for bvfile in bvfilelist:
            vsplit = bvfile.split('.')
            if(len(vsplit)>1):
                videoname = vsplit[-2]
                bvid = videoname.split('_')[-1]
                if(videoname.split('_')[-1][0:2]=='BV' and vsplit[-1] == 'mp4'): #符合视频规范
                    # if videoname[0:3] != '【删】':
                    bvid = videoname.split('_')[-1];
                    bvpage = videoname.split('_')[-2][2];
                    f.write('* [%s](https://www.bilibili.com/video/%s?p=%s)\n'%(bvfile,bvid,bvpage))
                    bvfilenum += 1
                    # else:
                    #     None
                else:
                    print('Unrecognized Name: %s'%videoname)

print('[√] %d videos recorded.'%bvfilenum)
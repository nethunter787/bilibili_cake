# -*- coding: utf-8 -*-
"""
Created on Sat Sep  3 11:26:01 2022

@author: Administrator
"""
import os
import re

# Get New Bv Name
markcakefile = 'BiliCakeMarkdown_2022_09_03_11_57_44.md'
if not os.path.exists(markcakefile):
    raise Exception('[×] markcakefile path error.')
with open(markcakefile ,'r+',encoding="utf-8") as f:
    markcake = f.read()
    bvname_comp = re.compile('\* \[(.*?)\]\(')
    bvnamelist = re.findall(bvname_comp, markcake)

BvNewNameDict = {}
for bvname in bvnamelist:
    bvkey = '_'.join(bvname.split('_')[-2:])
    BvNewNameDict[bvkey] = bvname;

# Search Bv And Change Name
bvfolder = r'Z:\DynamicVideos'
if os.path.exists(bvfolder):
    for bvfile in os.listdir(bvfolder):
        vsplit = bvfile.split('.')
        if(len(vsplit)>1):
            videoname = vsplit[-2]
            bvid = videoname.split('_')[-1]
            if(videoname.split('_')[-1][0:2]=='BV' and vsplit[-1] == 'mp4'): #符合命名规范
                # if videoname[0:3] != '【删】':
                bvkey = '_'.join(bvfile.split('_')[-2:])
                if bvkey in BvNewNameDict:
                    if BvNewNameDict[bvkey] == bvfile:
                        None # 文件名未修改
                    else:
                        old_file_name = os.path.join(bvfolder,bvfile)
                        new_file_name = os.path.join(bvfolder,BvNewNameDict[bvkey])
                        os.rename(old_file_name,new_file_name)
                        print('[-]Rename:\n%s\n%s'%(old_file_name,new_file_name))
                else:
                    print('[×]新视频未记录，请更新MarkCake：\n%s\n'%videoname)
                # else:
                #     None
            else:
                print('[×]Unrecognized Name: %s'%videoname)
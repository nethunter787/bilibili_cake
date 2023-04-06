# -*- coding: utf-8 -*-
"""
Created on Fri May  6 23:15:11 2022

@author: Sharpstar
@comment: 现在可以指定文件夹来更新
"""
import os
import bypy
import sys
import logging


logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                level=logging.DEBUG,
                filename='baiducake.log',
                filemode='a')

if(len(sys.argv)>1):
    remotepath = sys.argv[1]
else:
    remotepath = 'DynamicVideos'
localpath  = os.path.join(os.getcwd(),remotepath)

try:
    if(os.path.exists(localpath)):
        print("[√] folder is ready to sync : %s"%localpath)
        bp = bypy.ByPy()
        bp.info()
        bp.mkdir(remotepath)
        bp.syncup(localpath,remotepath)
    else:
        print("[×] folder isn't exists. : %s"%localpath)
except Exception as e:
    logging.error(e)
    


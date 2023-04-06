# bilibili下载器  python

# 准备工作

1. 下载[FFmpeg](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z)并将文件夹解压，将内部的bin文件夹添加到系统环境变量PATH。
2. 安装模块 `pip install qrcode`。
3. 安装模块 `pip install bypy`，运行 `bypy info` 通过激活码绑定百度云账户

# 功能模块

- [x] [detectcake.py](./detectcake.py)自动下载关注UP发布的视频。
- [x] [autoUpdateCake.py](./autoUpdateCake.py)将视频生成为Markdown文档链接。
- [x] [desktop_updatecake.py](./desktop_updatecake.py)将视频生成为Markdown文档链接【桌面运行版本】。
- [x] [usercake.py](./usercake.py)下载一个UP主的投稿视频（带视频筛选功能）。
- [x] [onecake.py](./usercake.py)下载投稿视频（输入视频BVID）。
- [x] [favorcake.py](./favorcake.py)自动下载收藏的视频（收藏文件夹的ID需要在文件内制定）。
- [x] [baiducake.py](./baiducake.py)将视频上传至百度云。

# 废弃模块

- [x] [markcake.py](./markcake.py)将视频生成为Markdown文档链接。







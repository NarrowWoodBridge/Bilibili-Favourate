from models import *
from tools_str import *

import os, json

config = Config(
    settingsFolder = "功能性文件",  #配置文件所在的文件夹
    vroot = "B站视频"  #储存所有视频笔记的文件夹
)

user = User(config=config)

#获取之前记录的信息
def load_state(user):
    config=user.config  ###
    renamed = user.renamed  ###
    #1.读取infoDict.json
    if os.path.exists(config.json_save):
        with open(config.json_save, "r", encoding="utf-8") as f:
            user.infoDict = json.load(f)
    #2.1.获取md文件列表
    mdfiles = []  #局部
    for root,dirs,files in os.walk(config.vroot):
        for file in files:
            if len(file) > 3 and file[-3:] == ".md":
                mdfiles.append(root.replace("\\","/")+"/"+file)
    #2.2.读取文件信息
    for filePath in mdfiles:
        lastData = {}
        title = delSuf(filePath.split("/")[-1], ".md")
        fileDirPath = delSuf(filePath,"/{}.md".format(title))
        with open(filePath,"r",encoding="UTF-8") as mdfile:
            useful = ["类型","bvid","title","upper","cover"]  #有用字段
            lines = mdfile.read().split("---\n")[1].rstrip("\n").split("\n")
            for line in lines:
                key = line.split(": ")[0]
                if key in useful:
                    lastData[key] = line.split(": ")[1].rstrip("\n")
        if "title" in lastData:
            titleNow = lastData['title']
            if titleNow != title:  #此时的title为修改后的标题，lastData['title']为原始标题
                renamed[lastData['title']] = [fileDirPath,title]
    print(renamed)
    print("原有信息读取完毕")

from models import *

import os

#按行读取，存为列表
def readfile(file):
    with open(file,"r",encoding="UTF-8") as f:
        lines = f.readlines()
        return [i.rstrip("\n") for i in lines if i!="\n"]

#如果目录不存在则创建目录
def mkdir(path):
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)
    else:
        pass

#判断md文件/文件夹是否存在与某个目录或其子目录下
#若不存在，则返回false
#存在时，aim=none时返回True，aim=file时返回文件路径，aim=dir时返回目录路径
def xexists(user, name, start, aim="none", limit=False, reason=""):
    renamed = user.renamed  ###
    for root, dirs, files in os.walk(start):
        root = root.replace("\\","/")
        if aim != "dir":
            for file in files:
                if file == name+".md" or (name in renamed and root == renamed[name][0] and file == renamed[name][1]+".md"):  #！中间
                    if file != name+".md":
                        print("文件被改名："+name+"->"+file+" ({})".format(reason))
                    if aim == "file":
                        return root+"/"+file
                    return True
        if aim != "file":
            for adir in dirs:
                path = root+"/"+adir
                if adir == name or xexists(user, name, start=path, aim="file", limit=1, reason="通过确认目录.md来确认合集文件夹"):
                    if adir != name:
                        print("文件夹被改名："+name+"->"+adir+" ({})".format(reason))
                    if aim == "dir":
                        return path
                    return True
        if limit:  #限制只搜索当前目录，不搜子目录
            return False
    print("不存在："+name+" ({})".format(reason))
    return False
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


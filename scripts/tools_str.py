#字符串：删后缀
def delSuf(self: str, suffix: str) -> str:
    if suffix and self.endswith(suffix):
        return self[:-len(suffix)]
    else:
        return self[:]

#替换特殊字符
def xreplace(string):
    numOfYinhao = 0
    for char in string:
        if char == '“' or char == '”' or char == '"':
            numOfYinhao += 1
    if numOfYinhao == 2:
        out = ""
        numOfYinhao = 0
        for char in string:
            if char == '“' or char == '”' or char == '"':
                if numOfYinhao == 0:
                    char = "“"
                    numOfYinhao += 1
                else:
                    char = "”"
            out += char
        string = out
    elif numOfYinhao > 2:
        pass
        #print("================"+string)
    return string.replace('/','-').replace('|','｜').replace(':','：').replace('?','？').replace('<','【').replace('>','】').replace('[','【').replace(']','】')

#将字符串列表组合成一个字符串
def addStrs(aList, opt=False):
    #opt表示是否添加末尾换行符，默认不添加
    ret = ""
    for line in aList:
        ret += line+"\n"
    if not opt:
        ret = ret[:-1]  #去掉末尾换行符
    return ret

#按顺序将 Markdown 行拆分为多个区段
def readmdfile(lines,splitList):
    ret = [[]]
    for line in lines:
        line = line.rstrip("\n")
        if len(splitList) != 0 and (splitList[0] in line):  #如果一级标题改成二级呢？
            splitList.pop(0)
            ret.append([])
            continue
        ret[-1].append(line)
    return ret
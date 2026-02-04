

def readmdfile(lines,splitList):
    ret = [[]]
    for line in lines:
        line = line.rstrip("\n")
        if len(splitList) != 0 and line == splitList[0]:
            splitList.pop(0)
            ret.append([])
            continue
        ret[-1].append(line)
    return ret

with open("test/note.md","r",encoding="UTF-8") as mdfile:
    lines = mdfile.readlines()
    A,B,C = readmdfile(lines,["# 视频","# 笔记"])
    print(A)
    print(B)
    print(C)
from models import *
from tools_file import *
from tools_str import *
from webapi import *

def single(user, db , path, checkbox=0, page=0, videoList="", note="", title_file=""):
    config = user.config  ###
    #checkbox表示是否需要勾选框
    #page用于生成[多page视频]中的单个page的链接
    def write_keys(f, db, keys):
        for key in keys:
            if key in db:
                f.write('{}: {}\n'.format(key, db[key]))
    #公有字段
    title = db['title']; upper = db['upper']
    #判断笔记是否已经存在，不存在则创建
    if xexists(user, title, start=config.vroot, aim="file", reason="新建文件：判断文件是否存在"):
        return
    
    mkdir(path)
    if not title_file:
        title_file = title
    with open('{}/{}.md'.format(path, title_file), 'w', encoding="utf-8") as f:
        #字段：根据情况添加，若db中有，就添加，反之亦然
        f.write('---\n')
        if checkbox:
            f.write('target: tasks\nstatus: in progress\ntags: bilibili\n')
        write_keys(f, db, ['类型','bvid','title','upper','cover'])  #简化
        f.write('---\n')
        #封面也根据有无来添加
        if 'cover' in db:
            f.write('![]({})\n'.format(db['cover']))
        #处理和添加视频链接
        f.write('# 视频\n')
        if videoList:
            f.write(videoList)
        elif 'bvid' in db:
            video_url = 'https://www.bilibili.com/video/{}'.format(db['bvid'])
            if page:  #多page视频中的具体page
                video_url += '?p={}'.format(page)
            line = '[{}]({})\n'.format(title, video_url)
            if checkbox:
                line = "- [ ] " + line
            f.write(line)
        #添加笔记区
        f.write('# 笔记\n')
        f.write(note)

#更新合集目录中的视频清单
def updateList(user, mdfileroute, path_ep, aimlist, opt=0, singlelist=[], title2Dict={}):
    config = user.config  ###
    renamed = user.renamed  ###
    #mdfileroute为要更新的视频目录md文件的路径
    #path_ep为此合集所在的文件夹路径
    #aimlist为合集中的所有视频的bvid
    #opt表示合集类型，0为视频全部收藏，1为视频部分收藏
    #singlelist为视频单个收藏类型的合集中被收藏过的视频
    with open(mdfileroute,"r",encoding="UTF-8") as mdfile:
        lines = mdfile.readlines()
        A,B,C = readmdfile(lines,["# 视频","# 笔记"])  #分段读取
        for item in aimlist:
            title = search(user, item, 'title', reason = "获取标题，检测链接是否存在")
            if title==None:  #!!!404
                continue
            title2 = title2Dict[item]
            f = 1  #旗标，1表示未添加
            for num, had in enumerate(B):
                if (item in had) or (title in had) or (title in renamed and renamed[title][1] in had):  #此项已有，无需新增
                    f = 0
                    #网页链接->超链接
                    if item in had:  #(item为视频的bvid)链接类型为网页链接(这是转换链接类型的前提)
                        if (item in singlelist) or (opt == 0):  #需要转换类型的链接(网页链接->超链接)
                            state = had[:6]
                            if opt == 1:
                                #新增：此合集中被收藏的视频
                                B[num] = state + "[["+title+"|" + title2+"]]"
                            else:
                                #新建笔记
                                B[num] = state + "[[" + title2 + "]]"
            if f:  #当前文件中不存在的视频项目的链接，也就是更新后新出现的视频的链接
                if (item in singlelist) or (opt == 0):
                    if opt == 1:
                        #①之前收藏的视频(笔记可被改名)/②上次刷新后新收藏的视频(未创建笔记)-->被此合集收录
                        #①单个视频的笔记不需要移动，也不需要改名，但要获取它的标题/②新建
                        ifExist_title = xexists(user, title, start=config.vroot, aim="file", reason="目录新增：被收藏的视频：获取视频路径以得到标题")
                        if ifExist_title:
                            title = delSuf(ifExist_title.split("/")[-1],".md")
                        B.append("- [ ] [[" + title + "|" + title2 + "]]")
                    else:
                        #此全收藏合集收录了新视频，新建笔记
                        B.append("- [ ] [[" + title2 + "]]")
                else:
                    video_url = 'https://www.bilibili.com/video/{}'.format(item)
                    B.append("- [ ] ["+title2+"]("+video_url+")")
        if opt == 0:
            for num, had in enumerate(B):
                #特殊处理带别名的链接
                if "[[" in had and "|" in had and had.endswith("]]"):
                    state = had[:6]
                    nowTitle = had[8:].split("|")[0]
                    aimTitle = had.split("|")[1][:-2]
                    aimTitle = xreplace(aimTitle)  #别名可能含有特殊字符
                    #改名笔记我们就用改名后的标题，未改名就重命名为超链接别名
                    p = 1  #旗标，1表示此笔记名称未被人为修改
                    for oriTitle in renamed:
                        if renamed[oriTitle][1] == nowTitle:  #“可能是”被改过名的单个视频笔记，需进一步确认
                            if path_ep in renamed[oriTitle][0]:  #确实这个合集里面有这个被改名的笔记
                                aimTitle = nowTitle  #链接名称改为被人为修改后的名称
                                p = 0
                    if p:
                        #此链接对应的视频笔记没有被人为修改，还是视频原标题，且被移动到合集笔记文件夹了
                        #此时的nowTitle就是对应视频的原标题

                        #笔记文件名->超链接别名(aimTitle)
                        path_note = xexists(user, nowTitle, start=config.vroot, aim="file", reason="获取笔记路径，用于改名")  #!!!默认能找到，没考虑重复文件的全路径链接情况
                        # print("改名："+path_note+"==>"+aimTitle)
                        print("改名："+nowTitle+" ==> "+aimTitle)
                        oriFolder = delSuf(path_note, path_note.split("/")[-1])[:-1]
                        newPath = "{}/{}.md".format(oriFolder, aimTitle)
                        os.rename(path_note, newPath)
                        renamed[nowTitle] = [oriFolder, aimTitle]  #记录改名

                    B[num] = state + "[[{}]]".format(aimTitle)

    with open(mdfileroute,"w",encoding="UTF-8") as mdfile:
        mdfile.write(addStrs(A, 1))
        mdfile.write("# 视频\n")
        mdfile.write(addStrs(B, 1))
        mdfile.write("# 笔记\n")
        mdfile.write(addStrs(C))

#批量新建合集中的视频
def batchSingleNote(user, alist, path, checkbox=0, title2Dict={}):
    for bvid in alist:
        all = search(user, bvid, 'all', reason="新建笔记，获取信息")
        title = all['title']
        title2 = ""
        if title2Dict:
            title2 = title2Dict[bvid]
        upper = all['upper']
        cover = all['cover']
        db = {'类型':'single-ep','bvid':bvid,'title':title,'upper':upper,'cover':cover}
        single(user, db, path, checkbox=checkbox, title_file=title2)

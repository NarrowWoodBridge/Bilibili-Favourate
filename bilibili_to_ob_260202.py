import requests
import re
import json
from pprint import *
import os
import shutil

settings = "功能性文件"  #配置文件所在的文件夹
vroot = "B站视频"  #储存所有视频笔记的文件夹

infoDict = {}  #key为bvid，value为视频信息组成的字典{'title':xx, 'upper':xx......}
eps = []  #视频合集最后再一起处理
renamed = {}  #重命名的文件记录字典，key为原始标题，value为[文件夹路径，修改后的标题]

#字符串：删后缀
def delSuf(self: str, suffix: str) -> str:
    if suffix and self.endswith(suffix):
        return self[:-len(suffix)]
    else:
        return self[:]

#获取之前记录的信息
#1.读取infoDict.json
json_save = '{}/infoDict.json'.format(settings)
if os.path.exists(json_save):
    with open(json_save) as f:
        infoDict = json.load(f)
#2.1.获取md文件列表
mdfiles = []
for root,dirs,files in os.walk(vroot):
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

#根据bvid查询视频信息
def search(bvid, aim, reason=""):
    if bvid in infoDict:
        #print("不用再查了: ("+reason+")",end="")
        #print(infoDict[bvid]['title'])
        if aim == "all":
            return infoDict[bvid]
        return infoDict[bvid][aim]
    #获取信息
    new_url = 'https://api.bilibili.com/x/web-interface/view?bvid={}'.format(bvid)
    vid = json.loads(requests.get(url=new_url, headers=headers).text)
    if('data' not in vid):
        print("!!!查询失败：("+reason+")bvid="+bvid)
        return None
    data = vid['data']
    #开始打表
    infoDict[bvid] = {}
    #+++标题
    title = xreplace(data['title'])
    infoDict[bvid]['title'] = title
    #+++up
    upper = xreplace(data['owner']['name'])
    infoDict[bvid]['upper'] = upper
    #+++封面
    cover = data['pic']
    infoDict[bvid]['cover'] = cover
    #返回结果
    print("???查询：("+reason+")"+title)
    if aim == "all":
        return infoDict[bvid]
    return infoDict[bvid][aim]

#按行读取，存为列表
def readfile(file):
    with open(file,"r",encoding="UTF-8") as f:
        lines = f.readlines()
        return [i.rstrip("\n") for i in lines if i!="\n"]
#获取全收藏合集的列表、新增全收藏合集的列表
epset = "{}/全收藏合集.md".format(settings)
epList = readfile(epset)

#读取cookies，取得header
cookie = open("{}/cookies.md".format(settings), 'r', encoding="utf-8").read()
headers = {
    'referer': 'https://space.bilibili.com',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',
    'cookie': cookie
}

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

#判断md文件/文件夹是否存在与某个目录或其子目录下
#若存在，则返回路径，否则返回false
def xexists(name, aim="none", start=vroot, limit=False, reason=""):
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
                if adir == name or xexists(name, aim="file", start=path, limit=1, reason="通过确认目录.md来确认合集文件夹"):
                    if adir != name:
                        print("文件夹被改名："+name+"->"+adir+" ({})".format(reason))
                    if aim == "dir":
                        return path
                    return True
        if limit:
            return False
    print("不存在："+name+" ({})".format(reason))
    return False

#如果目录不存在则创建目录
def mkdir(path):
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)
    else:
        pass

#将字符串列表组合成一个字符串
def add(aList, opt=0):
    ret = ""
    for line in aList:
        ret += line+"\n"
    if not opt:
        ret = ret[:-1]  #去掉末尾换行符
    return ret

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

def single(db , path, checkbox=0, page=0, videoList="", note="", title2=""):
    #checkbox表示是否需要勾选框
    #page用于生成[多page视频]中的单个page的链接

    #各种文件都有的字段
    title = db['title']; upper = db['upper']
    #判断笔记是否已经存在，不存在则创建
    if not xexists(title, aim="file", reason="新建文件：判断文件是否存在"):
        mkdir(path)
        if not title2:
            title2 = title
        with open('{}/{}.md'.format(path, title2), 'w', encoding="utf-8") as f:
            #字段：根据情况添加，若db中有，就添加，反之亦然
            f.write('---\n')
            if checkbox:
                f.write('target: tasks\nstatus: in progress\ntags: bilibili\n')
            f.write('类型: {}\n'.format(db['类型']))
            if 'bvid' in db:
                f.write('bvid: {}\n'.format(db['bvid']))
            f.write('title: {}\n'.format(title))
            f.write('upper: {}\n'.format(upper))
            if 'cover' in db:
                f.write('cover: {}\n'.format(db['cover']))
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

def bilibili_to_ob(path_one,url):
    #爬取同步收藏夹内容
    response = requests.get(url=url, headers=headers)
    json_data = json.loads(response.text)
    medias = json_data['data']['medias']
    for item in medias:  #遍历每一个收藏夹项目(单个视频/多page视频/视频合集)
        bvid = item['bvid']  #'''''''''''''''''''''''''''bvid
        title = xreplace(item['title'])  #''''''''''''''title
        upper = item['upper']['name']  #''''''''''''''''upper
        cover = item['cover']  #''''''''''''''''''''''''cover
        #重新爬取
        new_url = 'https://api.bilibili.com/x/web-interface/view?bvid={}'.format(bvid)
        vid = json.loads(requests.get(url=new_url, headers=headers).text)
        if 'data' in vid:  #有效项目
            data = vid['data']
        else:
            continue
        
        #print("::::::"+title)
        
        if 'ugc_season' not in data:  #没有ugc_season字段->非视频合集->单个视频/多page视频
            pages = data['pages']
            if len(pages) == 1:  #单个视频
                db = {'类型':'single','bvid':bvid,'title':title,'upper':upper,'cover':cover}
                single(db, path_one, checkbox=1)
            else:  #多page视频
                #创建对应文件夹
                path_two = '{}/【02.多Page】/{}'.format(path_one,title)
                path_three = '{}/{}'.format(path_two,'笔记')
                #判断[文件夹或目录文件]是否已经存在,如果不存在，则创建新目录和文件
                if not xexists(title, aim="file"):
                    mkdir(path_three)
                    videoList = ""
                    for i in pages:
                        page_name = xreplace(i['part'])
                        videoList += '- [ ] [[{}]]\n'.format(page_name)
                        #单个视频的笔记
                        db = {'类型':'page','bvid':bvid,'title':page_name,'upper':upper}
                        single(db, path_three, page=i['page'])
                    db2 = {'类型':'pages','bvid':bvid,'title':title,'upper':upper,'cover':cover}
                    single(db2, path_two, videoList=videoList)

        elif 'ugc_season' in data:  #此视频属于某个视频合集
            #补充【当前视频】的信息
            infoDict[bvid] = {}
            #添加视频标题到字典
            infoDict[bvid]['title'] = title
            #添加up名称到字典
            infoDict[bvid]['upper'] = upper
            #添加封面到字典
            infoDict[bvid]['cover'] = cover

            #获取【合集】信息
            epData = data['ugc_season']
            epData['epVideoList'] = epData['sections'][0]['episodes']  #合集中的视频列表
            epVideoList = epData['epVideoList']  #合集中的视频列表
            epTitle = xreplace(epData['title'])  #合集标题  //!!注意字符替换
            epCover = epData['cover']  #合集封面

            #【合集】对应的文件夹
            path_two = '{}/【01.视频合集】/{}'.format(path_one,epTitle)

            #向【集合】中添加当前视频信息；若合集不存在，则添加合集相关信息
            p = 0
            for anEP in eps:
                if epTitle == anEP['epData']['title']:
                    anEP['epSingleVideoData'].append(data)  #向合集数据中添加关于此单独收藏的视频的信息
                    p += 1
            if p == 0:
                eps.append({'epData': epData , 'epSingleVideoData': [data] , 'epPath': path_one})

            #保证【合集目录.md】存在
            db = {'类型':'ep','title':epTitle,'upper':upper,'cover':epCover}
            single(db, path_two)

            #若【当前视频】从属于全收藏合集，则单个视频的笔记(存在的话)要移动到合集文件夹中
            oriRoute = xexists(title, aim="file", reason="文件移动相关：获取视频路径")  #文件原路径，文件不存在则为False
            path_ep = xexists(epTitle, aim="dir", reason="文件移动相关：获取合集文件夹路径")  #合集文件夹路径
            path_epNote = path_ep+"/笔记"  #合集中的笔记文件夹
            #单个视频的笔记已存在且需要被移动
            if oriRoute and epTitle in epList and not path_epNote in oriRoute:
                print("移动："+oriRoute+"==>"+path_epNote)
                nowTitle = delSuf(oriRoute.split("/")[-1],".md")  #移动前的标题
                '''
                if nowTitle == title:  #若笔记标题为视频原标题(未修改)，则将其改名为其在合集中的第二标题
                    for aVideo in epVideoList:
                        if aVideo['bvid'] == bvid:
                            title2 = aVideo['title']
                            nowTitle = title if len(title2)>=24 and len(title) > len(title2) and title.startswith(title2) else title2
                            break
                '''
                newPath = '{}/{}.md'.format(path_epNote,nowTitle)  #移动后的路径
                if title in renamed:
                    renamed[title]=[path_epNote,nowTitle]  #记录这个本就被改名的文件的新路径
                mkdir(path_epNote)
                shutil.move(oriRoute, newPath)  #移动到文件目标路径
                #读取并重写，目的是去除为dv进度条服务的标记
                #分段读取
                with open(newPath,"r",encoding="UTF-8") as mdfile:
                    lines = mdfile.readlines()
                    A,B,C = readmdfile(lines,["# 视频","# 笔记"])
                #删除
                os.remove(newPath)
                #写入
                db = {'类型':'single-ep','bvid':bvid,'title':title,'upper':upper,'cover':cover}
                single(db, path_epNote, note=add(C), title2=nowTitle)

def get_id():
    # 获取mid
    url = 'https://api.bilibili.com/x/web-interface/nav'
    json_data = json.loads(requests.get(url=url, headers=headers).text)
    mid = json_data['data']['mid']
    # 获取
    url = 'https://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid={}&jsonp=jsonp'.format(mid)
    json_data = json.loads(requests.get(url=url, headers=headers).text)

    favorites_list = json_data['data']['list']  #获取所有收藏夹的元数据
    favData = {}
    for i in favorites_list:  #遍历每一个收藏夹的元数据
        id_ = i['id']
        favFolderTitle = re.sub('([^\u4e00-\u9fa5])', '', i['title']).replace('/','-')
        count = i['media_count']
        favData[favFolderTitle] = {'id': id_ , 'count': count}  #title作为键，id和count作为值
    return favData

favFolders = get_id()  #存储账号上所有收藏夹的信息

#获取要抓取的收藏夹的名称
settings2 = "{}/Python脚本设置.md".format(settings)
setting = str(open(settings2, 'r', encoding="utf-8").read()).replace('\n','').replace(' ','')  #读取并替换换行和空格
names = re.findall('##B站同步文件夹(.*?)##', setting)[0].split('-[]')  #正则匹配并列出列表(第一项为空字符串)
names = [i for i in names if i != '']  #去除空项目

#遍历要同步的b站收藏夹，对收藏夹内视频进行“to-ob”的操作
for favFolderName in names:
    print("----------"+favFolderName)
    id_ = favFolders[favFolderName]['id']
    count = favFolders[favFolderName]['count']  #收藏夹内视频数量
    num_page = int(count/20)+1  #每20个视频分为一组，求出一共多少组
    for i in range(num_page):
        url = 'https://api.bilibili.com/x/v3/fav/resource/list?media_id={}&pn={}&ps=20&keyword=&order=mtime&type=0&tid=0&platform=web&jsonp=jsonp'.format(id_, i+1)
        path_one = '{}/{}'.format(vroot, favFolderName)  #本地收藏夹路径
        bilibili_to_ob(path_one, url)

#更新合集目录中的视频清单
def update(mdfileroute, path_ep, aimlist, opt=0, singlelist=[], title2Dict={}):
    #mdfileroute为要更新的视频目录md文件的路径
    #path_ep为此合集所在的文件夹路径
    #aimlist为合集中的所有视频的bvid
    #opt表示合集类型，0为视频全部收藏，1为视频部分收藏
    #singlelist为视频单个收藏类型的合集中被收藏过的视频
    with open(mdfileroute,"r",encoding="UTF-8") as mdfile:
        lines = mdfile.readlines()
        A,B,C = readmdfile(lines,["# 视频","# 笔记"])  #分段读取
        for item in aimlist:
            title = search(item, 'title', reason = "获取标题，检测链接是否存在")
            if title==None:  #!!!404
                continue
            title2 = title2Dict[item]
            f = 1  #旗标，1表示未添加
            for num, had in enumerate(B):
                if item in had or title in had or (title in renamed and renamed[title][1] in had):  #此项已有，无需新增
                    f = 0
                    if item in had:  #(item为视频的bvid)链接类型为网页链接(这是转换链接类型的前提)
                        if item in singlelist or opt == 0:  #需要转换类型的链接(网页链接->超链接)
                            state = had[:6]
                            if opt == 1:
                                #新增：此合集中被收藏的视频
                                B[num] = state + "[["+title+"|" + title2+"]]"
                            else:
                                #新建笔记
                                B[num] = state + "[[" + title2 + "]]"
            if f:  #当前文件中不存在的视频项目的链接，也就是更新后新出现的视频的链接
                if item in singlelist or opt == 0:
                    if opt == 1:
                        #①之前收藏的视频(笔记可被改名)/②上次刷新后新收藏的视频(未创建笔记)-->被此合集收录
                        #①单个视频的笔记不需要移动，也不需要改名，但要获取它的标题/②新建
                        ifExist_title = xexists(title, aim="file", reason="目录新增：被收藏的视频：获取视频路径以得到标题")
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
                if "[[" in had and "|" in had and had.endswith("]]"):
                    state = had[:6]
                    nowTitle = had[8:].split("|")[0]
                    aimTitle = had.split("|")[1][:-2]
                    p = 1
                    for oriTitle in renamed:
                        if renamed[oriTitle][1] == nowTitle:  #“可能是”被改过名的单个视频笔记，需进一步确认
                            if path_ep in renamed[oriTitle][0]:  #确实这个合集里面有这个被改名的笔记
                                aimTitle = nowTitle  #链接名称改为被人为修改后的名称
                                p = 0
                    if p:
                        #此链接对应的视频笔记没有被人为修改，还是视频原标题，且被移动到合集笔记文件夹了
                        #此时的nowTitle就是对应视频的原标题

                        #此时链接名称(aimTitle)为超链接的显示名称，若此名称被人为修改过，则需要将笔记文件的名称改为此名称
                        path_note = xexists(nowTitle, aim="file", reason="获取笔记路径，用于改名")
                        newPath = delSuf(path_note, path_note.split("/")[-1]) + aimTitle + ".md"
                        os.rename(path_note, newPath)

                    B[num] = state + "[[{}]]".format(aimTitle)

    with open(mdfileroute,"w",encoding="UTF-8") as mdfile:
        mdfile.write(add(A, 1))
        mdfile.write("# 视频\n")
        mdfile.write(add(B, 1))
        mdfile.write("# 笔记\n")
        mdfile.write(add(C))

#批量新建合集中的视频
def batchSingleNote(alist, path, checkbox=0, title2Dict={}):
    for bvid in alist:
        all = search(bvid, 'all', reason="新建笔记，获取信息")
        title = all['title']
        title2 = ""
        if title2Dict:
            title2 = title2Dict[bvid]
        upper = all['upper']
        cover = all['cover']
        db = {'类型':'single-ep','bvid':bvid,'title':title,'upper':upper,'cover':cover}
        single(db, path, checkbox=checkbox, title2=title2)

#处理合集
for anEP in eps:  #anEP有三个键：'epData', 'epSingleVideoData' , 'epPath'
    epData = anEP['epData']
    #epData有：title,cover(合集目录已有，这里用不上),epVideoList,sections(里面有合集中视频的信息，我已将其放到epVideoList中)
    epTitle = xreplace(epData['title'])  #合集标题  //!!注意字符替换

    #md目录文件的路径
    mdfileroute = xexists(epTitle,aim="file", reason="处理合集：获取目录路径")
    #文件夹的路径
    path_one = anEP['epPath']
    path_ep = delSuf(mdfileroute,"/"+mdfileroute.split("/")[-1])
    path_three = '{}/{}'.format(path_ep,'笔记')

    #获取最新的合集中的视频bvid列表
    epVideoList = epData['epVideoList']
    aimlist = [i['bvid'] for i in epVideoList]
    #合集中视频的第二标题
    title2Dict = {}
    for epVideo in epVideoList:
        bvid = epVideo['bvid']
        title2 = xreplace(epVideo['title'])
        if len(title2) >= 24:
            title = search(bvid=bvid, aim="title", reason="获取标题，用于和第二标题比较")
            if len(title) > len(title2) and title.startswith(title2):
                title2 = title  #被砍剩下一半的标题谁爱用谁用去吧！
        title2Dict[bvid] = title2
    #被单独收藏的视频的bvid列表
    singlelist = [i['bvid'] for i in anEP['epSingleVideoData']]

    if epTitle in epList:  #全收藏的视频合集
        mkdir(path_three)
        print(">>全收藏："+epTitle)
        #更新目录文件.md
        update(mdfileroute, path_ep, aimlist, opt=0, title2Dict=title2Dict)
        #单个视频的笔记
        batchSingleNote(aimlist, path_three, title2Dict=title2Dict)
    else:  #部分收藏的视频合集
        mkdir(path_ep)
        print(">>部分收藏："+epTitle)
        #更新目录文件.md
        update(mdfileroute, path_ep, aimlist, opt=1, singlelist=singlelist, title2Dict=title2Dict)
        #单个视频的笔记
        batchSingleNote(singlelist, path_one, checkbox=1)

#储存当前已抓取的信息字典
#字典转换
infoJson = json.dumps(infoDict, sort_keys=False, indent=4, separators=(',', ': '))
#字典储存
with open(json_save,"w") as f_save:
    f_save.write(infoJson)
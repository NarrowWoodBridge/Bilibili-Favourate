from models import *
from tools_file import *
from tools_str import *
from webapi import *
from mdnote import *
import User
from User import config, user  #全局共用

import requests, re, json, os, shutil
from pprint import *

#爬取一个收藏夹项目
def bilibili_to_ob(path_one, item, user):
    renamed = user.renamed  ###

    bvid = item['bvid']  #'''''''''''''''''''''''''''bvid
    title = xreplace(item['title'])  #''''''''''''''title
    upper = item['upper']['name']  #''''''''''''''''upper
    cover = item['cover']  #''''''''''''''''''''''''cover

    #print("::::::"+title)  #debug
    data = search(user, bvid, 'all', reason="获取完整视频信息")
    if data == None:
        return #查询失败，跳过此视频
    
    if data['type']=='single':  #单个视频
        db = {'类型':'single','bvid':bvid,'title':title,'upper':upper,'cover':cover}
        single(user, db, path_one, checkbox=1)
    elif data['type']=='pages':  #多page视频
        pages = data['pages']
        #创建对应文件夹
        path_two = '{}/【02.多Page】/{}'.format(path_one,title)
        path_three = '{}/{}'.format(path_two,'笔记')
        #判断[文件夹或目录文件]是否已经存在,如果不存在，则创建新目录和文件
        if not xexists(user, title, start=config.vroot, aim="file"):
            mkdir(path_three)
            videoList = ""
            for i in pages:
                # page_num = i['page']  #分页序号
                page_name = xreplace(i['part'])
                videoList += '- [ ] [[{}]]\n'.format(page_name)
                #单个视频的笔记
                db = {'类型':'page','bvid':bvid,'title':page_name,'upper':upper}
                single(user, db, path_three, page=i['page'])
            db2 = {'类型':'pages','bvid':bvid,'title':title,'upper':upper,'cover':cover}
            single(user, db2, path_two, videoList=videoList)
    elif data['type']=='ep':  #此视频属于某个视频合集
        #获取【合集】信息
        epData = data['epData']
        epTitle = xreplace(epData['title'])  #合集标题  //!!注意字符替换
        epCover = epData['cover']  #合集封面

        #【合集】对应的文件夹
        path_two = '{}/【01.视频合集】/{}'.format(path_one,epTitle)

        #向【集合】中添加当前视频信息；若合集不存在，则添加合集相关信息
        p = 0
        for anEP in user.eps:
            if epTitle == anEP['epData']['title']:
                anEP['epSingleVideos'].append(bvid)  #向合集数据中添加关于此单独收藏的视频的信息
                p += 1
        if p == 0:
            user.eps.append({'epData': epData , 'epSingleVideos': [bvid] , 'epPath': path_one})  #是否拷贝赋值

        #保证【合集目录.md】存在
        db = {'类型':'ep','title':epTitle,'upper':upper,'cover':epCover}
        single(user, db, path_two)

        #若【当前视频】从属于全收藏合集，则单个视频的笔记(存在的话)要移动到合集文件夹中
        oriRoute = xexists(user, title, start=config.vroot, aim="file", reason="文件移动相关：获取视频路径")  #文件原路径，文件不存在则为False
        path_ep = xexists(user, epTitle, start=config.vroot, aim="dir", reason="文件移动相关：获取合集文件夹路径")  #合集文件夹路径
        path_epNote = path_ep+"/笔记"  #合集中的笔记文件夹
        #单个视频的笔记已存在且需要被移动
        if oriRoute and (epTitle in config.fullEpList) and not path_epNote in oriRoute:
            print("移动(实则重建)："+oriRoute+" ==> "+path_epNote)
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
            single(user, db, path_epNote, videoList=addStrs(B,1), note=addStrs(C), title_file=nowTitle)

def main():
    User.load_state(user)  #加载缓存数据和文件重命名信息

    favFolders = getFavFolders(user)  #存储账号上所有收藏夹的信息

    #遍历要同步的b站收藏夹，对收藏夹内视频进行“to-ob”的操作
    for tSyncFolderName, videos in user.syncFolders.items():
        path_one = '{}/{}'.format(config.vroot, tSyncFolderName)  #本地收藏夹路径
        print("----------"+tSyncFolderName)
        for item in videos:  #遍历每一个收藏夹项目(单个视频/多page视频/视频合集)
            bilibili_to_ob(path_one, item, user)

    #处理合集
    for anEP in user.eps:  #anEP有三个键：'epData', 'epSingleVideos' , 'epPath'
        epData = anEP['epData']
        #epData有：title,cover(合集目录已有，这里用不上),epVideoList(合集中视频的信息列表)
        epTitle = xreplace(epData['title'])  #合集标题  //!!注意字符替换

        #md目录文件的路径
        mdfileroute = xexists(user, epTitle, start=config.vroot,aim="file", reason="处理合集：获取目录路径")
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
            #补全被截断的标题
            if len(title2) >= 24:
                title = search(user=user, bvid=bvid, aim="title", reason="获取标题，用于和第二标题比较")
                if len(title) > len(title2) and title.startswith(title2):
                    title2 = title  #被砍剩下一半的标题谁爱用谁用去吧！
            title2Dict[bvid] = title2
        #被单独收藏的视频的bvid列表
        singlelist = anEP['epSingleVideos']

        if epTitle in config.fullEpList:  #全收藏的视频合集
            mkdir(path_three)
            print(">>全收藏："+epTitle)
            #更新目录文件.md
            updateList(user, mdfileroute, path_ep, aimlist, opt=0, title2Dict=title2Dict)
            #单个视频的笔记
            batchSingleNote(user, aimlist, path_three, title2Dict=title2Dict)
        else:  #部分收藏的视频合集
            mkdir(path_ep)
            print(">>部分收藏："+epTitle)
            #更新目录文件.md
            updateList(user, mdfileroute, path_ep, aimlist, opt=1, singlelist=singlelist, title2Dict=title2Dict)
            #单个视频的笔记
            batchSingleNote(user, singlelist, path_one, checkbox=1)

    user.save_state()  #储存当前已抓取的信息字典

main()

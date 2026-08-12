import requests, json, re

from tools_str import *

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from models import User, VideoInfo

def getFavFolders(user: User):
    config = user.config  ###
    # 获取mid
    url = 'https://api.bilibili.com/x/web-interface/nav'
    json_data = json.loads(requests.get(url=url, headers=config.headers).text)
    mid = json_data['data']['mid']
    # 获取
    url = 'https://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid={}&jsonp=jsonp'.format(mid)
    json_data = json.loads(requests.get(url=url, headers=config.headers).text)

    favorites_list = json_data['data']['list']  #获取所有收藏夹的元数据
    favData = {}
    for i in favorites_list:  #遍历每一个收藏夹的元数据
        id_ = i['id']
        favFolderTitle = re.sub('([^\u4e00-\u9fa5])', '', i['title']).replace('/','-')
        count = i['media_count']
        favData[favFolderTitle] = {'id': id_ , 'count': count}  #title作为键，id和count作为值
    return favData

def getFavFolderVideos(user: User, tFavFolder):
    config = user.config  ###
    ret = []
    id_ = tFavFolder['id']
    count = tFavFolder['count']  #收藏夹内视频数量
    num_page = int(count/20)+1  #每20个视频分为一组，求出一共多少组
    for i in range(num_page):
        url = 'https://api.bilibili.com/x/v3/fav/resource/list?media_id={}&pn={}&ps=20&keyword=&order=mtime&type=0&tid=0&platform=web&jsonp=jsonp'.format(id_, i+1)
        #爬取同步收藏夹内容
        response = requests.get(url=url, headers=config.headers)
        json_data = json.loads(response.text)
        medias = json_data['data']['medias']
        for item in medias:  #遍历每一个收藏夹项目(单个视频/多page视频/视频合集)
            ret.append(item)
    return ret

#根据bvid查询视频信息
def search(user: User, bvid, aim, reason=""):
    #aim为要查询的目标信息，若为"all"，则返回全部信息
    config = user.config  ###
    infoDict = user.infoDict  ###
    if bvid in infoDict:
        #print("不用再查了: ("+reason+")",end="")
        #print(infoDict[bvid]['title'])
        if aim == "all":
            return infoDict[bvid]
        return infoDict[bvid][aim]
    #获取信息
    new_url = 'https://api.bilibili.com/x/web-interface/view?bvid={}'.format(bvid)
    vid = json.loads(requests.get(url=new_url, headers=config.headers).text)
    if('data' not in vid):
        print("!!!查询失败：("+reason+")bvid="+bvid)
        return None
    data = vid['data']
    #开始打表
    infoDict[bvid] = {
        'type': '',
        'title': xreplace(data['title']),
        'upper': xreplace(data['owner']['name']),
        'cover': data['pic']
    }
    curDict = infoDict[bvid]  ###
    if 'ugc_season' not in data:  #没有ugc_season字段->非视频合集->单个视频/多page视频
        if len(data['pages'])==1:
            curDict['type'] = "single"
        else:
            curDict['type'] = "pages"
            pages = [ {'page':i['page'],'part':xreplace(i['part'])} for i in data['pages']]
            curDict['pages'] = pages
    else:
        curDict['type'] = "ep"
        epDataOri = data['ugc_season']
        epVideoListOri = epDataOri['sections'][0]['episodes']  #合集中的视频列表
        epData = {
            'title': xreplace(epDataOri['title']),  #合集标题  //!!注意字符替换
            'cover': epDataOri['cover'],  #合集封面
            'epVideoList': [ {
                'bvid': i['bvid'],
                'title': xreplace(i['title'])
            } for i in epVideoListOri ]
        }
        curDict['epData'] = epData
    #返回结果
    print("???查询：("+reason+")"+infoDict[bvid]['title'])
    if aim == "all":
        return infoDict[bvid]
    return infoDict[bvid][aim]

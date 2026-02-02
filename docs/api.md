# Bilibili 收藏夹同步脚本 API 文档

## 概述
该脚本用于同步 B 站收藏夹到本地笔记目录（Obsidian 风格），并维护合集信息、笔记文件及元数据缓存。

## 配置与目录
### 变量配置
- settings：配置文件目录（默认 功能性文件）
- vroot：本地笔记根目录（默认 B站视频）

### 配置文件
- 功能性文件
	- infoDict.json：缓存视频信息（title/upper/cover）
	- cookies.md：请求所需 cookie
	- Python脚本设置.md：同步收藏夹的配置
	- 全收藏合集.md：全收藏合集列表

## 数据结构
- infoDict：{ bvid: { title, upper, cover } }
- eps：合集临时列表，每项包含：
  - epData：合集元数据
  - epSingleVideoData：此合集里被单独收藏的视频数据
  - epPath：收藏夹本地路径
- renamed：已改名文件记录
  - { 原始标题: [文件夹路径, 改名后的标题] }

## 函数 API

### delSuf(self: str, suffix: str) -> str
删除字符串尾部指定后缀。

### search(bvid, aim, reason="")
按 bvid 查询视频信息并写入缓存。
- aim："title" | "upper" | "cover" | "all"

### readfile(file) -> list[str]
按行读取文件，返回非空行列表。

### xreplace(string) -> str
替换不合法/特殊字符，规整引号并进行文件名安全替换。

### xexists(name, aim="none", start=vroot, limit=False, reason="")
检查文件/目录是否存在（支持改名记录）。
- aim："file" | "dir" | "none"

### mkdir(path)
创建目录（若不存在）。

### add(aList, opt=0) -> str
将字符串列表拼接成文本。opt=0 时去掉末尾换行。

### readmdfile(lines, splitList) -> list[list[str]]
按分割标记拆分 md 内容。

### single(db, path, checkbox=0, page=0, videoList="", note="", title2="")
创建单个笔记文件。
- db：包含 类型/title/upper 等字段
- checkbox：是否生成任务勾选
- page：多 P 视频页码
- videoList：自定义视频列表
- note：笔记内容
- title2：文件名覆盖

### bilibili_to_ob(path_one, url)
同步单个收藏夹分页数据到本地目录，处理单视频/多 P/合集逻辑。

### get_id() -> dict
获取账号所有收藏夹元数据 { title: { id, count } }。

### update(mdfileroute, path_ep, aimlist, opt=0, singlelist=[], title2Dict={})
更新合集目录 md 内容（含链接转换和笔记改名逻辑）。

### batchSingleNote(alist, path, checkbox=0, title2Dict={})
批量创建合集中的单视频笔记。

## 主流程
1. 读取缓存信息与已有 md，建立 renamed。
2. 读取 cookies 与设置，确定同步收藏夹。
3. 分页同步收藏夹，生成笔记/目录并收集合集信息 eps。
4. 处理 eps，更新合集目录与批量创建笔记。
5. 保存 infoDict.json。

## 结构优化建议
1. 拆分模块
   - io_utils.py：文件读写、路径、md 解析
   - bili_api.py：HTTP 请求与数据解析
   - notes.py：笔记生成/更新
   - main.py：流程编排
2. 引入配置对象
   - 用 dataclass 管理 settings/vroot/headers，减少全局变量扩散。
3. 统一错误处理与重试
   - 网络请求加超时、重试与异常捕获。
4. 缓存策略改进
   - search 中加入缓存过期判断或 API 失败回退。
5. 日志分级
   - 使用 logging 替代 print，支持 quiet/verbose。
6. 路径操作标准化
   - 全面改用 pathlib.Path，减少字符串拼接。
7. 流程分离
   - 将“收集数据”和“写入文件”两步解耦，便于测试与扩展。

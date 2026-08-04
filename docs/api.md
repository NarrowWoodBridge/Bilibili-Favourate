# `main.py` API 与运行说明

本文档以 [`scripts/main.py`](../scripts/main.py) 为准，记录脚本的运行约定、数据结构、函数行为及当前限制。

## 1. 脚本定位

`main.py` 将当前 Bilibili 账号中指定的收藏夹同步到本地 Markdown 目录，生成适合 Obsidian 使用的视频笔记，并维护视频信息缓存、合集目录和用户手动改名记录。

该文件目前是一个**直接执行的脚本**，不是可安全导入的库：模块顶层包含读取配置、访问网络、移动或改写文件等操作。执行 `import scripts.main` 也会触发完整同步流程。

## 2. 运行方式与依赖

### 2.1 依赖

- Python 3
- 第三方包：`requests`
- 一个可正常访问 Bilibili API 的网络环境
- 有效的 Bilibili 登录 Cookie

安装依赖：

```bash
python -m pip install requests
```

### 2.2 启动

脚本中的路径均相对于**当前工作目录**，因此应在仓库根目录执行：

```bash
python scripts/main.py
```

脚本没有命令行参数。同步范围由 `功能性文件/Python脚本设置.md` 决定。

## 3. 全局配置与文件约定

### 3.1 全局变量

| 变量 | 默认值 | 作用 |
| --- | --- | --- |
| `settings` | `功能性文件` | 配置和缓存文件所在目录 |
| `vroot` | `B站视频` | 所有本地视频笔记的根目录 |
| `infoDict` | `{}` | 以 `bvid` 为键的视频信息缓存 |
| `eps` | `[]` | 本轮同步期间收集的合集信息 |
| `renamed` | `{}` | 已被用户手动改名的笔记索引 |
| `headers` | 运行时生成 | Bilibili 请求头，包含 Cookie |

### 3.2 配置文件

#### `功能性文件/cookies.md`

必需。文件内容会被原样放入请求头的 `cookie` 字段。只写 Cookie 值，不要添加 Markdown 标题或代码块。

Cookie 属于敏感凭据，不应提交到 Git、粘贴到日志或对外分享。Cookie 失效后，`getFavFolders()` 等请求将无法取得账号数据。

#### `功能性文件/Python脚本设置.md`

必需。脚本只读取 `## B站同步文件夹` 与下一个二级标题之间的勾选项。解析前会删除全部空格和换行，因此下面两项会被识别为 `电影` 和 `体育`：

```markdown
## B站同步文件夹

- [ ] 电影
- [ ] 体育

## 其他设置
```

注意：

- `## B站同步文件夹` 后必须还有一个 `##` 二级标题，用来结束匹配区间。
- 当前解析器只以去空格后的 `-[]` 分隔项目，因此必须使用 `- [ ]`；写成 `- [x]` 会得到错误的收藏夹名称。
- `getFavFolders()` 会删除收藏夹标题中的所有非中文字符；配置名称必须与处理后的标题完全一致，否则访问 `favFolders[favFolderName]` 时会触发 `KeyError`。

#### `功能性文件/全收藏合集.md`

必需。每行填写一个需要完整同步的合集标题。标题必须与 Bilibili 返回、再经 `xreplace()` 处理后的合集标题完全相同。

- 在列表中：创建合集内全部视频的笔记。
- 不在列表中：只为收藏夹中实际单独收藏的视频创建笔记，其他视频保留为网页链接。

#### `功能性文件/infoDict.json`

可选缓存。文件存在时，脚本启动即读取；文件不存在时从空字典开始。同步结束后会将当前 `infoDict` 覆盖写回该文件。

缓存没有过期或强制刷新机制。已有 `bvid` 不会再次请求 Bilibili，因此标题、封面、UP 主或合集内容可能不是最新值。

### 3.3 输出目录

典型结构如下：

```text
B站视频/
└── <收藏夹名>/
    ├── <单视频标题>.md
    ├── 【01.视频合集】/
    │   └── <合集标题>/
    │       ├── <合集标题>.md
    │       └── 笔记/
    │           └── <合集内视频标题>.md
    └── 【02.多Page】/
        └── <视频标题>/
            ├── <视频标题>.md
            └── 笔记/
                └── <分P标题>.md
```

部分收藏合集中的单视频笔记仍放在收藏夹根目录；全收藏合集中的笔记放在合集的 `笔记` 子目录。

## 4. 核心数据结构

### 4.1 `infoDict`

键为 `bvid`，值为视频缓存记录：

```python
{
    "BV...": {
        "type": "single",       # single | pages | ep
        "title": "视频标题",
        "upper": "UP主名称",
        "cover": "https://..."
    }
}
```

不同类型的附加字段：

- `single`：无附加字段。
- `pages`：包含 `pages`。当前 `search()` 实际缓存为 `list[str]`，每项是一个分 P 标题。
- `ep`：包含 `epData`。

`epData` 的结构：

```python
{
    "title": "合集标题",
    "cover": "https://...",
    "epVideoList": [
        {"bvid": "BV...", "title": "合集内标题"}
    ]
}
```

### 4.2 `eps`

本轮同步使用的合集临时列表：

```python
[
    {
        "epData": { ... },
        "epSingleVideos": ["BV..."],
        "epPath": "B站视频/<收藏夹名>"
    }
]
```

- `epData`：来自 `infoDict[bvid]["epData"]`。
- `epSingleVideos`：该合集中被当前收藏夹单独收藏的视频 `bvid`。
- `epPath`：发现该合集时对应的收藏夹本地路径。

合集按处理后的 `epData.title` 合并，而不是按独立合集 ID 合并。

### 4.3 `renamed`

启动时扫描 `vroot` 下已有的 `.md` 文件，从 YAML 区域比较原始 `title` 与当前文件名：

```python
{
    "原始视频标题": ["所在文件夹路径", "当前文件名（不含 .md）"]
}
```

`xexists()` 和 `updateList()` 使用该映射识别用户手动改名的笔记。

### 4.4 收藏夹 API 条目 `item`

`bilibili_to_ob()` 至少使用以下字段：

```python
{
    "bvid": "BV...",
    "title": "视频标题",
    "upper": {"name": "UP主名称"},
    "cover": "https://..."
}
```

## 5. 函数 API

### `delSuf(self: str, suffix: str) -> str`

当 `self` 以非空 `suffix` 结尾时删除该后缀，否则返回原字符串的切片副本。

- `self`：待处理字符串。
- `suffix`：要删除的后缀；空字符串不会触发删除。
- 返回：处理后的字符串。

### `search(bvid, aim, reason="")`

查询或读取一个视频的信息，并将新查询结果写入全局 `infoDict`。

- `bvid`：视频 BV 号。
- `aim`：`"all"` 或记录中的字段名，如 `"type"`、`"title"`、`"upper"`、`"cover"`、`"pages"`、`"epData"`。
- `reason`：仅用于控制台日志，说明本次查询原因。
- 返回：`aim == "all"` 时返回完整记录，否则返回对应字段；脚本判定响应不含 `data` 时返回 `None`。
- 副作用：可能访问 `https://api.bilibili.com/x/web-interface/view`，并更新 `infoDict`。

依赖全局变量 `headers`、`infoDict` 和函数 `xreplace()`。缓存命中时不会校验字段是否齐全；无效 `aim` 会触发 `KeyError`。

### `readfile(file) -> list[str]`

以 UTF-8 按行读取文件，去掉每行末尾的 `\n`，忽略内容恰好为 `"\n"` 的空行。

- 只包含空格或制表符的行不会被忽略。
- 文件不存在、不可读或编码错误时，异常直接向上传播。

### `xreplace(string) -> str`

对标题进行有限的引号规整和文件名字符替换。

当字符串中 `“`、`”`、`"` 三类引号合计恰好出现两次时，将它们依次统一为中文左、右引号。随后执行：

| 原字符 | 替换为 |
| --- | --- |
| `/` | `-` |
| `|` | `｜` |
| `:` | `：` |
| `?` | `？` |
| `<`、`[` | `【` |
| `>`、`]` | `】` |

返回替换后的字符串，不修改传入对象。

### `xexists(name, aim="none", start=vroot, limit=False, reason="")`

在 `start` 及其子目录中查找指定笔记或合集目录，并兼容 `renamed` 中记录的改名笔记。

- `name`：不带 `.md` 后缀的原始标题。
- `aim`：
  - `"file"`：只查文件，找到时返回完整 Markdown 路径。
  - `"dir"`：只查目录，找到时返回完整目录路径。
  - 其他值（默认 `"none"`）：文件或目录均可，找到时返回 `True`。
- `start`：搜索起始目录。
- `limit`：为真时只处理 `os.walk()` 的当前第一层后返回，不继续向下搜索。
- `reason`：仅用于日志。
- 返回：按 `aim` 返回路径、`True` 或 `False`。

目录判定不仅比较目录名；如果某个子目录内存在同名 `.md`，也会将该子目录视为目标合集目录。

### `mkdir(path) -> None`

目录不存在时调用 `os.makedirs(path)` 递归创建；已存在时不做任何处理。

### `addStrs(aList, opt=False) -> str`

将字符串列表逐项用换行符连接。

- `opt` 为假：删除最终的一个换行符。
- `opt` 为真：保留最终换行符。
- 空列表始终返回空字符串。

### `readmdfile(lines, splitList) -> list[list[str]]`

按顺序将 Markdown 行拆分为多个区段。

- `lines`：可迭代的文本行。
- `splitList`：按出现顺序排列的分隔文本，例如 `["# 视频", "# 笔记"]`。
- 返回：成功找到全部分隔符时，得到“分隔符数量加一”个区段；命中的分隔行不会保留在结果中。
- 副作用：通过 `pop(0)` **原地清空或缩短**传入的 `splitList`。

匹配规则是 `splitList[0] in line`，不是整行相等。因此正文中只要包含当前分隔文本，也会触发分段。

### `single(db, path, checkbox=0, page=0, videoList="", note="", title_file="") -> None`

创建一个视频或合集 Markdown 笔记。若 `xexists(db["title"], aim="file")` 已找到对应笔记，则直接返回，不更新已有文件。

- `db`：笔记字段字典，必须包含 `title` 和 `upper`；可包含 `类型`、`bvid`、`cover`。
- `path`：输出目录，不存在时自动创建。
- `checkbox`：为真时添加任务元数据，并把自动生成的视频链接写为 `- [ ] ...`。
- `page`：非零时给自动生成的 Bilibili 链接增加 `?p=<page>`。
- `videoList`：自定义 `# 视频` 区内容；非空时优先于自动生成链接。
- `note`：原样写入 `# 笔记` 区。
- `title_file`：覆盖输出文件名；为空时使用 `db["title"]`。

写入的 YAML 字段只会从以下键中选择，顺序固定：

```text
类型, bvid, title, upper, cover
```

`checkbox` 为真时还会在这些字段之前写入：

```yaml
target: tasks
status: in progress
tags: bilibili
```

注意：存在性检查使用 `db["title"]`，不是 `title_file`；两者不同时，调用方需要自行避免目标文件名冲突。

### `bilibili_to_ob(path_one, item) -> None`

处理收藏夹 API 返回的一个视频条目。参数 `item` 是字典，不是 URL。

- `path_one`：收藏夹对应的本地目录，如 `B站视频/电影`。
- `item`：见“收藏夹 API 条目 `item`”一节。
- 返回：无显式返回值；`search()` 返回 `None` 时跳过当前视频。

按 `search(bvid, "all")["type"]` 分支：

- `single`：在收藏夹根目录创建带任务勾选框的单视频笔记。
- `pages`：在 `【02.多Page】/<视频标题>/` 下创建目录笔记，并在 `笔记/` 下为每个分 P 创建笔记。
- `ep`：创建合集目录笔记，将合集信息追加到全局 `eps`；全收藏合集中的已有单视频笔记可能被移动并重写到合集 `笔记/` 目录。

副作用包括创建目录和文件、更新 `eps`/`renamed`、移动并重写已有笔记。

### `getFavFolders() -> dict`

获取当前 Cookie 对应账号创建的所有收藏夹元数据。

请求顺序：

1. `/x/web-interface/nav` 获取账号 `mid`。
2. `/x/v3/fav/folder/created/list-all` 获取收藏夹列表。

返回结构：

```python
{
    "处理后的收藏夹标题": {
        "id": 123456,
        "count": 20
    }
}
```

收藏夹标题通过 `re.sub('([^\u4e00-\u9fa5])', '', title)` 处理，即仅保留基本汉字范围。不同原始标题可能因此映射为同一个键，后出现的条目会覆盖先出现的条目。

### `updateList(mdfileroute, path_ep, aimlist, opt=0, singlelist=[], title2Dict={}) -> None`

更新合集目录 Markdown 的 `# 视频` 区域，并保留 `# 视频` 之前和 `# 笔记` 之后的原有内容。

- `mdfileroute`：合集目录 Markdown 文件路径。
- `path_ep`：合集文件夹路径，用于判断改名笔记是否属于当前合集。
- `aimlist`：合集内全部视频的 `bvid` 列表。
- `opt`：`0` 表示全收藏合集，`1` 表示部分收藏合集。
- `singlelist`：部分收藏合集中被单独收藏的视频 `bvid`。
- `title2Dict`：`{bvid: 合集内显示标题}`；必须覆盖 `aimlist` 中的每个 `bvid`。

主要行为：

- 已有网页链接按收藏状态转换为 Obsidian Wiki 链接。
- 新视频追加到目录；部分收藏但未单独收藏的视频保留 Bilibili 网页链接。
- 全收藏合集会为链接选择合集内标题，并可能将未被用户手动改名的笔记重命名。
- 写回时统一恢复 `# 视频`、`# 笔记` 两个标题。

该函数只新增或转换条目，不会删除已从 Bilibili 合集中移除的旧条目。输入文件必须包含按顺序出现的 `# 视频` 和 `# 笔记`，否则 `A, B, C = ...` 无法正常解包。

### `batchSingleNote(alist, path, checkbox=0, title2Dict={}) -> None`

批量为 `bvid` 列表创建单视频笔记。

- `alist`：`bvid` 列表。
- `path`：输出目录。
- `checkbox`：传给 `single()`。
- `title2Dict`：可选的 `{bvid: 文件名}` 映射；提供后用合集内标题作为文件名，否则使用视频原标题。只要该字典非空，就必须覆盖 `alist` 中的每个 `bvid`。

每条记录通过 `search(bvid, "all")` 获取，并以 `类型: single-ep` 写入笔记。

## 6. 笔记格式

由 `single()` 生成的典型单视频笔记：

```markdown
---
target: tasks
status: in progress
tags: bilibili
类型: single
bvid: BVxxxxxxxxxx
title: 视频原标题
upper: UP主名称
cover: https://example.com/cover.jpg
---
![](https://example.com/cover.jpg)
# 视频
- [ ] [视频原标题](https://www.bilibili.com/video/BVxxxxxxxxxx)
# 笔记
```

脚本后续依赖 YAML 区的 `title` 字段识别用户改名，并依赖 `# 视频`、`# 笔记` 分段。手动编辑时应保留这些结构。

## 7. 顶层同步流程

1. 读取 `infoDict.json`。
2. 扫描 `vroot` 下已有 Markdown，通过 YAML `title` 与文件名建立 `renamed`。
3. 读取全收藏合集列表和 Cookie，建立请求头。
4. 调用 `getFavFolders()` 获取账号收藏夹。
5. 从 `Python脚本设置.md` 解析待同步收藏夹名称。
6. 每 20 条分页请求 `/x/v3/fav/resource/list`，逐条调用 `bilibili_to_ob()`。
7. 遍历 `eps`，更新合集目录并批量创建视频笔记。
8. 将 `infoDict` 覆盖写入 `infoDict.json`。

脚本通过控制台输出查询、改名、移动、不存在等状态，没有结构化日志或退出码约定。

## 8. 当前实现限制

以下是 `main.py` 当前行为，调用或修改脚本时需要特别注意：

1. **不能无副作用地导入**：核心流程位于模块顶层，没有 `main()` 或 `if __name__ == "__main__"` 保护。
2. **网络错误未统一处理**：请求没有超时、重试、`raise_for_status()` 或 JSON 解析保护；Cookie 失效、限流、404、网络中断都可能直接抛出异常。
3. **多 P 数据结构不一致**：`search()` 把 `pages` 缓存为 `list[str]`，但 `bilibili_to_ob()` 按包含 `part`、`page` 的字典读取，执行多 P 分支时会触发类型错误。
4. **缓存不会自动更新**：命中 `infoDict` 后直接返回，合集新增视频、标题变化等不会被刷新。
5. **Markdown 解析较严格**：启动扫描假定每个 `.md` 都含有 `---\n` 分隔的 YAML；合集更新假定固定存在 `# 视频` 和 `# 笔记`。
6. **标题清洗不完整**：`xreplace()` 未处理 Windows 文件名中的反斜杠、星号、尾随句点、保留设备名等情况。
7. **分页会多请求一次**：页数使用 `int(count / 20) + 1`；当收藏数正好是 20 的倍数时会请求一个额外空页。
8. **文件改名或移动可能重写内容**：全收藏合集迁移笔记时只保留脚本识别的 YAML 字段、视频区和笔记区，其他自定义 YAML 字段可能丢失。

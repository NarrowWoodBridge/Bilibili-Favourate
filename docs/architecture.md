# 架构与同步流程

## 模块职责

| 模块 | 职责 |
| --- | --- |
| `scripts/main.py` | 同步编排；区分普通视频、多 P 和合集 |
| `scripts/models.py` | `Config`、`User`、`VideoInfo` 数据类 |
| `scripts/User.py` | 创建全局 `config`/`user`，加载缓存和改名记录 |
| `scripts/webapi.py` | 请求收藏夹列表、收藏夹视频和视频详情 |
| `scripts/mdnote.py` | 创建笔记、更新合集目录、批量创建合集笔记 |
| `scripts/tools_file.py` | 文件读取、建目录、递归查找笔记 |
| `scripts/tools_str.py` | 标题清洗、字符串拼接、Markdown 分段 |

模块使用绝对模块名导入，运行入口依赖 `scripts/` 自动加入 `sys.path`，因此推荐使用 `python scripts/main.py`，而不是将它作为包导入。

## 核心对象

`Config` 负责把固定路径下的 Markdown 配置转换为运行时字段：

- `settingsFolder`：默认由 `scripts/User.py` 设为 `功能性文件`。
- `vroot`：默认设为 `B站视频`。
- `headers`：包含 Cookie 的请求头。
- `syncFolderList`：配置中要同步的收藏夹名称。
- `fullEpList`：需要完整创建笔记的合集名称。

`User` 保存一轮同步的可变状态：

- `infoDict`：按 `bvid` 缓存视频信息。
- `renamed`：原始标题到当前路径和文件名的映射。
- `syncFolders`：收藏夹名称到收藏夹视频列表的映射。
- `eps`：等待统一更新的合集列表。

`VideoInfo` 已定义但当前流程没有实例化它；视频信息仍以普通字典传递。

## 当前执行顺序

```text
导入 scripts/User.py
  -> 创建 Config，读取 Cookie 和 Markdown 配置
  -> 创建 User
     -> 请求远端收藏夹列表
     -> 请求选中收藏夹的全部视频

执行 main()
  -> load_state() 读取 infoDict.json，并扫描手动改名
  -> 再次请求远端收藏夹列表（返回值当前未使用）
  -> 遍历 User.syncFolders
     -> bilibili_to_ob() 创建普通视频/多 P/合集目录
     -> 将合集信息汇总到 User.eps
  -> 统一更新完整合集或部分收藏合集
  -> save_state() 覆盖写回 infoDict.json
```

这意味着导入相关模块并不是无副作用操作：构造 `Config` 会读取本地凭据，构造 `User` 会访问网络，而 `main.py` 文件末尾会直接调用 `main()`。

## 已有笔记与改名识别

`load_state()` 遍历 `B站视频/` 下的所有 `.md`，读取第一个 YAML 分隔区中有限的字段。若 YAML `title` 与当前文件名不同，就记录为用户手动改名。

`xexists()` 查找笔记时依次使用：

1. 原始标题对应的文件名；
2. `renamed` 中记录的目录和当前文件名。

查找主要以标题为标识，而不是以 `bvid` 为唯一键。标题重复、同名合集和多 P 共享 `bvid` 的情况仍可能发生冲突。

## 合集处理

遇到属于 UGC 合集的视频时，`bilibili_to_ob()` 先确保合集目录笔记存在，并把数据放入 `User.eps`。所有收藏夹处理结束后，`main()` 再统一：

1. 从 `epVideoList` 生成完整 `bvid` 列表和显示标题映射；
2. 对疑似被 API 截断的合集内标题，用视频详情标题补全；
3. 更新合集目录中的链接；
4. 按完整或部分收藏策略批量创建视频笔记；
5. 必要时移动、改名和重写旧笔记。

详细函数契约见[模块 API](api.md)，实现风险见[已知问题](known-issues.md)。


# 数据与输出格式

## 输出目录

默认输出根目录是 `B站视频/`，每个同步收藏夹建立一个一级目录：

```text
B站视频/
└── <收藏夹名>/
    ├── <普通视频标题>.md
    ├── 【01.视频合集】/
    │   └── <合集标题>/
    │       ├── <合集标题>.md
    │       └── 笔记/
    │           └── <合集内标题>.md
    └── 【02.多Page】/
        └── <视频标题>/
            ├── <视频标题>.md
            └── 笔记/
                └── <分P标题>.md
```

部分收藏的合集仍会创建合集目录和目录笔记，但被单独收藏的视频笔记通常位于收藏夹根目录。完整合集的视频笔记位于合集的 `笔记/` 目录。

## 笔记结构

`single()` 生成的普通视频笔记形如：

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

后续同步依赖 YAML 中的 `title` 识别用户手动改名，并依赖 `# 视频`、`# 笔记` 两个一级标题更新合集目录。手动编辑时请保留这些字段和标题。

脚本会写入以下 `类型`：

| 值 | 含义 |
| --- | --- |
| `single` | 普通单视频 |
| `pages` | 多 P 视频的目录笔记 |
| `page` | 多 P 视频中的一个分 P 笔记 |
| `ep` | 视频合集的目录笔记 |
| `single-ep` | 合集中的单个视频笔记 |

## 合集目录链接

- 完整合集：目录中的每个条目使用 Obsidian Wiki 链接，并为所有视频创建笔记。
- 部分收藏合集：已单独收藏的视频使用 Wiki 链接，未单独收藏的视频使用 Bilibili 网页链接。
- 用户改过文件名时，脚本尝试保留改名后的 Wiki 链接。

当前更新逻辑只新增或转换条目，不会删除已从 Bilibili 合集中移除的旧条目。

## 缓存 `infoDict.json`

缓存以 `bvid` 为键：

```json
{
  "BV...": {
    "type": "pages",
    "title": "视频标题",
    "upper": "UP主名称",
    "cover": "https://...",
    "pages": [
      {"page": 1, "part": "分P标题"}
    ]
  }
}
```

合集记录还包含 `epData`：

```json
{
  "title": "合集标题",
  "cover": "https://...",
  "epVideoList": [
    {"bvid": "BV...", "title": "合集内标题"}
  ]
}
```

缓存没有过期和自动刷新机制。命中已有 `bvid` 时，标题、封面、UP 主和合集内容都不会重新请求。

## 运行期集合数据

`User.eps` 在一轮同步中汇总待处理合集：

```python
{
    "epData": { ... },
    "epSingleVideos": ["BV..."],
    "epPath": "B站视频/<收藏夹名>"
}
```

当前实现按清洗后的合集标题合并记录，而不是按合集 ID。若同名合集出现在多个收藏夹中，首次记录的 `epPath` 会决定后续处理位置。


# 搜索与匹配计算说明

本文档描述当前代码中的搜索、发布前匹配和匹配度计算逻辑。实现入口：

- `backend/retrieval.py`：分词、词法相关度、BM25L、向量过滤、RRF 和展示分数。
- `backend/app.py`：`/api/search`、`/api/semantic-search`、`/api/match-check`。
- `backend/embedding.py`：`Qwen/Qwen3-VL-Embedding-2B` 模型加载与编码。

## 1. 三种查询路径

| 场景 | 接口 | 主要逻辑 | 返回数量 |
| --- | --- | --- | --- |
| 关键字搜索 | `GET /api/search` | PostgreSQL `ILIKE` | 前端当前请求最多 200 条并分页 |
| 混合搜索 | `GET /api/semantic-search` | BM25L + pgvector + 加权 RRF | 最多 10 条，可以少于 10 条 |
| 发布前匹配 | `POST /api/match-check` | 相反方向的混合召回 + 规则重排 | 最多 10 条，可以少于 10 条 |

未输入搜索词时，物品库使用 `GET /api/lost-items?all=true`，一次返回当前状态、方向和分类筛选下的全部记录。这不属于相关性搜索。

## 2. 搜索字段

搜索只使用物品内容，不使用位置或时间。

| 字段 | 关键字搜索 | BM25L | 内容向量 |
| --- | --- | --- | --- |
| 物品名称 `item_name` | 是 | 是，重复 2 次 | 是 |
| 物品分类 `item_type` | 否 | 是，重复 2 次 | 否 |
| 物品描述 `description` | 是 | 是 | 是 |
| 图片 `image_url` | 否 | 否 | 是 |
| 丢失地点 `location` | 否 | 否 | 否 |
| 存放地点 `storage_location` | 否 | 否 | 否 |
| 时间 | 否 | 否 | 否 |

正式发布记录的向量由名称、描述和图片生成。历史数据在编码字段变更后通过 `backend/rebuild_content_vectors.py` 重建。

## 3. 中文分词与查询扩展

文本先转小写、合并空白，再保留中文块和英数字块。中文同时生成：

1. `jieba` 词元。
2. 单个汉字。
3. 连续双字词元。

例如“一卡通”会包含“一卡通、一、卡、通、一卡、卡通”等词元。单字词元不会用于普通多字查询的弱匹配，避免只共享一个汉字就召回。

当前领域扩展：

| 查询词 | 扩展词 |
| --- | --- |
| `书` | 书籍、教材、课本、词典、图书、读物 |
| `校园卡` | 一卡通、校园一卡通、学生卡 |
| `一卡通` | 校园卡、校园一卡通、学生卡 |
| `学生卡` | 校园卡、一卡通、校园一卡通 |

扩展关系用于 BM25 查询和词法相关度，不会退化成只匹配“卡”等单字，因此不会把卡包、钥匙等全部召回。

## 4. 词法相关度

对查询 `q` 和记录 `d` 计算词法相关度 `L(q,d)`：

| 命中方式 | `L` |
| --- | ---: |
| 查询完整出现在物品名称 | `1.00` |
| 查询完整出现在分类 | `0.95` |
| 扩展词出现在名称或分类 | `0.95` |
| 查询完整出现在描述 | `0.85` |
| 扩展词出现在描述 | `0.85` |

如果没有完整或扩展命中，则计算有效词元覆盖率：

```text
coverage = 查询有效词元与文档有效词元的交集数量 / 查询有效词元数量
```

- 多词元查询的 `coverage < 0.5` 时，`L = 0`，记录被 BM25 分支排除。
- 其他有覆盖的情况：`L = min(0.75, 0.45 + 0.30 * coverage)`。
- 完全没有覆盖时：`L = 0`。

单个汉字不会直接按子字符串匹配复合词。例如搜索“书”不会因为“书包”中包含“书”而命中；它通过上面的书籍领域扩展匹配教材和词典。

## 5. BM25L 召回

系统使用 `rank-bm25` 的 BM25L。BM25L 相比默认 Okapi BM25 更适合当前较小的数据集，可避免极小语料中唯一词 IDF 变为 0 的问题。

处理过程：

1. 查询加入领域扩展词后分词。
2. 所有已通过状态、方向和分类筛选的记录构建内容文本并分词。
3. 只保留 `L > 0` 的记录。
4. 先按词法相关度 `L`、再按 BM25L 分数排序。
5. 最多召回 `RETRIEVAL_CANDIDATE_LIMIT=10` 条。

物品名称和分类在文档中各重复两次，用于提高字段权重。

## 6. 向量召回

查询文本通过 `Qwen/Qwen3-VL-Embedding-2B` 编码并归一化。PostgreSQL 使用 pgvector 余弦距离：

```text
vector_similarity = 1 - (item_vector <=> query_vector)
```

数据库先取向量排名前 10，再执行两层过滤。设头部最佳相似度为 `V_best`：

```text
vector_cutoff = max(0.48, V_best - 0.08)
```

只有 `vector_similarity >= vector_cutoff` 的记录进入融合。因此 Top 10 是上限，系统不会为了凑满 10 条而返回明显无关物品。

## 7. 加权 RRF 排序

BM25L 分数和余弦相似度量纲不同，系统不直接相加，而使用加权 Reciprocal Rank Fusion。默认 `k=60`：

```text
rrf_score(d) = 0.7 / (60 + bm25_rank(d))
             + 0.3 / (60 + vector_rank(d))
```

记录不在某个分支中时，该分支贡献为 0。最终按 `rrf_score` 降序排列，最多保留 10 条候选。

这里的 `rrf_score` 只用于排序，对外返回字段名为 `retrieval_score`，不直接展示为百分比。

## 8. 页面匹配度

页面显示的“匹配度”是校准后的综合相关度，不是概率，也不是原始余弦相似度。

先把原始向量分 `V` 校准到 `V_cal`：

```text
V_cal = clamp((V - 0.30) / 0.50, 0, 1)
```

再结合词法相关度 `L`：

```text
如果 L >= 0.95：
    display_score = min(0.98, 0.90 + 0.10 * V_cal)

如果 0 < L < 0.95：
    display_score = min(0.95, 0.65 * L + 0.35 * V_cal)

如果 L = 0：
    display_score = V
```

最终 `display_score < 0.65` 的记录不会返回。接口相关字段：

| 字段 | 含义 |
| --- | --- |
| `similarity` | 页面展示的综合匹配度 `display_score` |
| `vector_similarity` | 原始向量余弦相似度，可能为空 |
| `retrieval_score` | 加权 RRF 排序分，不是百分比 |

## 9. 发布前匹配

`/api/match-check` 只查询与待发布记录方向相反、状态为 `active` 的记录：

- 发布寻物 `lost` 时，只匹配招领 `found`。
- 发布招领 `found` 时，只匹配寻物 `lost`。

它使用相同的 BM25L、向量过滤和 RRF，然后做轻量规则重排：

```text
分类完全一致：融合分 * 1.35
名称词元有交集：融合分 * 1.20
地点词元有交集：融合分 * 1.15
```

公开搜索不使用地点；地点只在发布前的失物/招领配对重排中作为弱信号。

## 10. 配置参数

| 环境变量 | 默认值 | 作用 |
| --- | ---: | --- |
| `RETRIEVAL_CANDIDATE_LIMIT` | `10` | 每个召回分支候选上限，代码硬上限为 10 |
| `BM25_WEIGHT` | `0.7` | RRF 中 BM25L 权重 |
| `VECTOR_WEIGHT` | `0.3` | RRF 中向量权重 |
| `VECTOR_SIMILARITY_THRESHOLD` | `0.48` | 向量绝对最低相似度 |
| `VECTOR_SIMILARITY_MAX_DROP` | `0.08` | 相对最佳向量结果允许的最大分差 |
| `RESULT_RELEVANCE_THRESHOLD` | `0.65` | 最终结果最低综合匹配度 |

## 11. 维护命令

重建全部历史记录的内容向量：

```bash
conda activate hugging_face
cd /Users/sagiri/WorkSpace/find-my-bot/backend
python rebuild_content_vectors.py
```

插入或补齐搜索测试数据：

```bash
python seed_search_test_data.py
```

运行检索测试：

```bash
python -m pytest -q tests/test_retrieval.py
```

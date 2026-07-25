> 项目备注：本文是学校 GenAI API 服务手册的文本副本，作为外部接口参考保留。FoundIt 当前实际使用学校兼容 OpenAI 格式的 `GPT-5.5` 做图片识别和智能客服回答；本地 embedding 默认使用项目内 `model/models--Qwen--Qwen3-VL-Embedding-2B`，不使用本文中的 BGE-M3 或 reranker 作为当前项目检索主链路。

上海科技大学 GenAI API 服务使用手册1
目 录
1 GenAI API 服务介绍 .................................................................................................. 1
2 模型介绍 ..................................................................................................................... 1
2.1 GPT-5.4 模型接口................................................................................................. 1
2.2 GPT-5.3-Codex 模型接口..................................................................................... 1
2.3 DeepSeek-R1 模型接口......................................................................................... 1
2.4 DeepSeek-V3.2 模型接口..................................................................................... 2
2.5 Qwen-instruct 模型接口..................................................................................... 2
2.6 DeepSeek-Math-V2 模型接口.............................................................................. 3
2.7 Qwen-code 模型接口............................................................................................ 3
2.8 BGE-M3 嵌入模型接口........................................................................................... 3
2.9 bge-reranker-v2-m3 重排序模型接口.............................................................. 3
2.10 Stable Diffusion 的运行环境......................................................................... 4
3 访问方式 ..................................................................................................................... 4
3.1 模型调用接口........................................................................................................ 4
3.2 访问信息的获取.................................................................................................... 4
4 接口调用示例 ............................................................................................................. 5
4.1 cURL 调用示例...................................................................................................... 5
4.1.1 流式调用： .................................................................................................................. 5
4.1.2 多模态调用（图像理解） .......................................................................................... 5
4.2 Python 调用示例................................................................................................... 5
4.2.1 基础对话 ...................................................................................................................... 5
4.2.2 流式对话 ...................................................................................................................... 6
4.2.3 流式对话 ...................................................................................................................... 6
4.2.4 多模态调用（图像理解） .......................................................................................... 7
4.2.5 多模态调用限制 .......................................................................................................... 9
4.3 OpenClaw 配置示例............................................................................................... 9
1
* 图书信息中心更新于 2026 年 3 月。
I
4.4 Stable Diffusion 环境的访问......................................................................... 10
5 常见人工智能应用架构 ........................................................................................... 10
5.1 基于提示词工程的对话应用.............................................................................. 10
5.2 检索增强生成知识库（RAG）应用.................................................................... 11
5.3 智能助手类应用（Agent）................................................................................ 11
附录：模型选型指南 ................................................................................................... 11
Ⅱ
Ⅱ


上海科技大学 GenAI API 服务使用手册
3
3. "messages": [...],
4. "temperature": 0.7,
5. "top_p": 0.8,
6. "top_k": 20,
7. "presence_penalty": 1.5,
8. "repetition_penalty": 1.0
9. }
2.6 DeepSeek-Math-V2 模型接口
DeepSeek-Math-V2 模型接口目前实际运行的是 DeepSeek-Math-V2，为 DeepSeek 于 2025
年 11 月 27 日发布的数学专用模型。该模型参数达 685B，是业内首个达到国际奥林匹克数
学竞赛（IMO）金牌水平且全面开源的数学模型。DeepSeek-Math-V2 专注于定理证明和自我验
证能力，在 IMO 2025 和 CMO 2024 上取得金牌级成绩，Putnam 2024 以扩展测试计算实现
118/120（接近满分）。该模型构建在 DeepSeek-V3.2-Exp-Base 之上，注重推理过程的严谨性
和完整性。
经评估审核通过后，提供基于 DeepSeek-Math-V2 模型的 API 访问，适合公式推导与符
号计算、数学证明与逻辑推理、科学计算与工程分析或教育辅导与习题解答。
2.7 Qwen-code 模型接口
Qwen-code 模型接口目前实际运行的是 Qwen3-Coder-Next，为阿里巴巴通义千问团队于
2026 年 2 月 4 日发布的编程专用模型。该模型采用极致高效的 MoE 架构，总参数达 80B，
每次推理仅激活 3B 参数，大幅降低了显存与算力需求。Qwen3-Coder-Next 专为编程智能体
设计，聚焦于长时程、多工具、可交互的真实编程任务，擅长代码生成、调试优化、代码审查
等场景，编程能力出色，超过 Claude 3.7 接近 Claude 4 的水平。
经评估审核通过后，提供基于 Qwen3-Coder-Next 模型的 API 访问，适合代码生成与程
序开发、代码调试与优化、代码审查与重构或编程智能体与自动化开发。
2.8 BGE-M3 嵌入模型接口
BGE-M3 模型接口目前实际运行的是 BGE-M3，为北京智源人工智能研究院（BAAI）于 2024
年 2 月发布的第三代通用嵌入模型。该模型支持超过 100 种语言，具备多语言、跨语言检索
能力，一站式集成了稠密检索（Dense）、稀疏检索（Sparse）、多向量检索（Multi-Vector）
三种检索功能。BGE-M3 最大输入长度为 8192 token，多次刷新 BEIR、MTEB、C-MTEB 等评测
榜单，成为首个中国国产 AI 模型。全球下载量超过 1500 万。
经评估审核通过后，提供基于 BGE-M3 模型的 API 访问，适合用于 RAG 向量数据库构建，
对文档的语义检索与文档搜索、文档聚类与分类或语义相似度计算。
2.9 bge-reranker-v2-m3 重排序模型接口
bge-reranker-v2-m3 模型接口目前实际运行的是 bge-reranker-v2-m3，为北京智源人工
智能研究院（BAAI）发布的检索重排序模型。该模型专为检索结果精排优化，配合 BGE-M3 使
上海科技大学 GenAI API 服务使用手册
4
用可显著提升 RAG 检索精度。bge-reranker-v2-m3 支持多语言场景，能够对初检结果进行相
关性重排序，帮助搜索系统、问答系统、推荐系统获得更精准的结果排序。
经评估审核通过后，提供基于 bge-reranker-v2-m3 模型的 API 访问，适合用于 RAG 检
索精度优化，对文档搜索结果重排序、问答系统答案排序或推荐系统结果优化。
2.10 Stable Diffusion 的运行环境
Stable Diffusion 是一种基于潜在扩散模型的文本生成图像技术，由 CompVis、Stability
AI 和 LAION 联合开发。它能够将文本描述转化为高质量图像，广泛应用于虚拟角色设计、商
品建模和艺术创作等领域。
学校通过 ComfyUI 环境向用户提供 Stable Diffusion 服务（非 API）。ComfyUI 是一个
基于节点的可视化工作流框架，相较于传统 WebUI 具有以下优势：
(1) 节点式工作流：通过拖拽节点构建图像生成流程，直观灵活。
(2) 可视化编程：支持复杂工作流设计，便于调试和优化。
(3) 高效资源管理：支持模型缓存、显存优化，提升生成效率。
(4) 扩展生态：丰富的自定义节点和插件，支持 ControlNet、AnimateDiff 等高级功能。
(5) 工作流复用：可保存、分享和复用完整工作流配置。
经评估审核通过后，学校提供基于 ComfyUI 的 Stable Diffusion 运行环境访问，适用
于图像编辑与风格迁移、创意设计、自动化内容生成等场景。
3 访问方式
在资源有限的条件下，为促进资源充分、合理和合规使用，上海科技大学 GenAI API 服务
采用申请评估机制，且仅限校内访问。申请者在获得所在院所/部门、图书信息中心的评估审核
通过后，服务将向申请者开放使用。
3.1 模型调用接口
经评估审核通过后，由图书信息中心负责协调运行模型所需环境的构建，并向用户提供接
口（API）的具体信息，接口采用与 OpenAI 兼容的 API，所以可以将提供的接口当成 OpenAI 的
本地替代。
3.2 访问信息的获取
评估审核通过后，用户可通过上海科技大学 GenAI 平台的 API Key 管理界面获取模型
接入信息。
接口统一为：https://genaiapi.shanghaitech.edu.cn/api/v1/start
上海科技大学 GenAI API 服务使用手册
5
4 接口调用示例
4.1 cURL 调用示例
4.1.1 流式调用：
1. curl -X POST https://genaiapi.shanghaitech.edu.cn/api/v1/start \
2. -H "Content-Type: application/json" \
3. -H "Authorization: Bearer YOUR_API_KEY" \
4. -d '{
5. "stream": true,
6. "messages": [
7. {"role": "system", "content": "You are a helpful assistant."},
8. {"role": "user", "content": “你好，请介绍一下自己。”}
9. ]
10. }'
4.1.2 多模态调用（图像理解）
1. curl -X POST https://genaiapi.shanghaitech.edu.cn/api/v1/start \
2. -H "Content-Type: application/json" \
3. -H "Authorization: Bearer YOUR_API_KEY" \
4. -d '{
5. "stream": false,
6. "model": "qwen2.5-vl-instruct",
7. "messages": [
8. {
9. "role": "user",
10. "content": [
11. {"type": "text", "text": “请描述这张图片的内容”｝，
12. {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
13. ]
14. }
15. ]
16. }'
4.2 Python 调用示例
4.2.1 基础对话
1. import requests
2.
3. API_URL = "https://genaiapi.shanghaitech.edu.cn/api/v1/start"
4. API_KEY = "YOUR_API_KEY" # 替换为您的 API Key
5.
6. headers = {
7. "Content-Type": "application/json",
8. "Authorization": f"Bearer {API_KEY}"
9. }
10.
上海科技大学 GenAI API 服务使用手册
6
11.# 通用对话示例
12.payload = {
13. "stream": False,
14. "messages": [
15. {"role": "system", "content": "You are a helpful assistant."},
16. {"role": "user", "content": “你好，请介绍一下自己”｝
17. ]
18.}
19.
20.response = requests.post(API_URL, headers=headers, json=payload)
21.print(response.json())
4.2.2 流式对话
1. import requests
2.
3. API_URL = "https://genaiapi.shanghaitech.edu.cn/api/v1/start"
4. API_KEY = "YOUR_API_KEY"
5.
6. headers = {
7. "Content-Type": "application/json",
8. "Authorization": f"Bearer {API_KEY}"
9. }
10.
11.payload = {
12. "stream": True,
13. "messages": [
14. {"role": "user", "content": “请解释什么是机器学习”｝
15. ]
16.}
17.
18.response = requests.post(API_URL, headers=headers, json=payload, stream=True)
19.for line in response.iter_lines():
20. if line:
21. print(line.decode("utf-8"))
4.2.3 流式对话
1. import requests
2.
3. API_URL = "https://genaiapi.shanghaitech.edu.cn/api/v1/start"
4. API_KEY = "YOUR_API_KEY"
5.
6. headers = {
7. "Content-Type": "application/json",
8. "Authorization": f"Bearer {API_KEY}"
9. }
10.
11.# 调用 DeepSeek-R1-0528 推理模型
上海科技大学 GenAI API 服务使用手册
7
12.payload = {
13. "stream": False,
14. "model": "deepseek-r1:671b",
15. "messages": [
16. {"role": "user", "content": “请证明：根号 2 是无理数”｝
17. ]
18.}
19.response = requests.post(API_URL, headers=headers, json=payload)
20.print(response.json())
21.
22.# 调用 Qwen-code 编程模型
23.payload = {
24. "stream": False,
25. "model": "qwen-code",
26. "messages": [
27. {"role": "user", "content": “请用 Python 实现一个二叉树的前序遍历”｝
28. ]
29.}
30.response = requests.post(API_URL, headers=headers, json=payload)
31.print(response.json())
32.
33.# 调用 DeepSeek-Math-V2 数学模型
34.payload = {
35. "stream": False,
36. "model": "deepseek-math",
37. "messages": [
38. {"role": "user", "content": “求解积分 ∫(x²+2x+1)dx"}
39. ]
40.}
41.response = requests.post(API_URL, headers=headers, json=payload)
42.print(response.json())
4.2.4 多模态调用（图像理解）
1. import requests
2. import base64
3.
4. API_URL = "https://genaiapi.shanghaitech.edu.cn/api/v1/start"
5. API_KEY = "YOUR_API_KEY"
6.
7. headers = {
8. "Content-Type": "application/json",
9. "Authorization": f"Bearer {API_KEY}"
10.}
11.
12.# 方式一：通过图片 URL
13.payload = {
14. "stream": False,
上海科技大学 GenAI API 服务使用手册
8
15. "model": "qwen2.5-vl-instruct", # 或 qwen-instruct
16. "messages": [
17. {
18. "role": "user",
19. "content": [
20. {"type": "text", "text": “请描述这张图片的内容”｝，
21. {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
22. ]
23. }
24. ]
25.}
26.response = requests.post(API_URL, headers=headers, json=payload)
27.print(response.json())
28.
29.# 方式二：通过 Base64 编码的本地图片
30.with open("local_image.jpg", "rb") as f:
31. image_base64 = base64.b64encode(f.read()).decode("utf-8")
32.
33.payload = {
34. "stream": False,
35. "model": "qwen2.5-vl-instruct",
36. "messages": [
37. {
38. "role": "user",
39. "content": [
40. {"type": "text", "text": “这张图片里有什么？”｝，
41. {"type": "image_url", "image_url": {"url":
f"data:image/jpeg;base64,{image_base64}"}}
42. ]
43. }
44. ]
45.}
46.response = requests.post(API_URL, headers=headers, json=payload)
47.print(response.json())
48.
49.# 方式三：视频理解
50.payload = {
51. "stream": False,
52. "model": "qwen2.5-vl-instruct",
53. "messages": [
54. {
55. "role": "user",
56. "content": [
57. {"type": "text", "text": “请分析这段视频的内容”｝，
58. {"type": "video_url", "video_url": {"url": "https://example.com/video.mp4"}}
59. ]
60. }
上海科技大学 GenAI API 服务使用手册
9
61. ]
62.}
63.response = requests.post(API_URL, headers=headers, json=payload)
64.print(response.json())
4.2.5 多模态调用限制
限制项 说明
单次最大图片数 10 张
单张图片大小（URL） ≤ 10 MB
单张图片大小（Base64） ≤ 10 MB
视频文件大小（URL） ≤ 2 GB
图片格式 JPEG、PNG、BMP、GIF、WebP
图片 URL 要求 公开可访问，无需登录、无防盗链、无 IP 限制
注意：本地模型服务仅限校内访问。如通过图片 URL 调用，需确保 URL 可在校园网内访
问，或使用 Base64 编码方式传入本地图片。
4.3 OpenClaw 配置示例
OpenClaw 是 一 个 本 地 AI Agent 运 行 框 架 ， 支 持 配 置 多 种 模 型 后 端 。 用 户 可 在
`openclaw/openclaw.json` 中配置 GenAI API 网关。
配置示例：
1. {
2. "providers": {
3. "genai": {
4. "type": "openai-compatible",
5. "baseUrl": "https://genaiapi.shanghaitech.edu.cn/api/v1",
6. "apiKey": "YOUR_API_KEY",
7. "models": {
8. "gpt-5.4": {
9. "name": "GPT-5.4",
10. "context": 128000
11. },
12. "gpt-5.3-codex": {
13. "name": "GPT-5.3-Codex",
14. "context": 128000
15. },
16. "deepseek-r1:671b": {
17. "name": "DeepSeek-R1-0528",
18. "context": 65536
19. },
20. "deepseek-v3:671b": {
21. "name": "DeepSeek-V3.2",
22. "context": 131072
23. },
24. "qwen-instruct": {
上海科技大学 GenAI API 服务使用手册
10
25. "name": "Qwen3.5-397B-A17B",
26. "context": 262144
27. },
28. "qwen2.5-vl-instruct": {
29. "name": "Qwen3.5-397B-A17B",
30. "context": 262144
31. },
32. "qwen-code": {
33. "name": "Qwen3-Coder-Next",
34. "context": 262144
35. },
36. "deepseek-math": {
37. "name": "DeepSeek-Math-V2",
38. "context": 163840
39. }
40. }
41. }
42. },
43. "modelAliases": {
44. "r1": "deepseek-r1:671b",
45. "v3": "deepseek-v3:671b",
46. "qwen": "qwen-instruct",
47. "coder": "qwen-code",
48. "math": "deepseek-math",
49. "gpt": "gpt-5.4"
50. }
51.}
配置完成后，需要重启 OpenClaw 的 Gateway 后，可通过别名或完整模型 ID 调用相应模
型。
4.4 Stable Diffusion 环境的访问
经评估审核通过后，用户将通过邮件获取 ComfyUI 的 Web URL，可直接通过浏览器访问使
用。
注意：
(1) 如需使用自定义 LoRA 模型文件，请在申请时提前沟通提供。
(2) 因资源有限，服务采用分时共享方式，高峰期可能出现排队等待。
5 常见人工智能应用架构
5.1 基于提示词工程的对话应用
提示词（Prompts）是一段人类可读的文本，它被输入到大语言模型或其他人工智能系统中，
以获得特定的输出或完成某个任务。简单来说，它是一个指令或问题，用于引导人工智能系统
按照我们的意图产生所需的响应。
上海科技大学 GenAI API 服务使用手册
11
基于提示词（Prompts），快速交付简单的 Web APP 工具，是最简单的人工智能应用交付
方式，大致可参考如下步骤进行尝试：
(1) 确定应用场景和功能需求。
(2) 设计并测试 Prompts 与模型参数。
(3) 编排 Prompts 与用户输入。
(4) 发布应用。
(5) 观测并持续迭代。
生成型应用与对话型应用在提示词编排上略有差异，对话型应用需结合“对话生命周期”
来满足更复杂的用户情景和上下文管理需求。
5.2 检索增强生成知识库（RAG）应用
基于检索增强生成的知识库（Retrieval Augmented Generation，RAG）以向量检索（Vector
Retrieval）为核心，是解决对话模型获取外部知识和缓解幻觉问题的主要解决方案。
使用该技术可经济且高效地构建基于生成式人工智能驱动的客服机器人、专业知识库、人
工智能搜索引擎等应用。
RAG 典型架构：
(1) 文档嵌入：使用 BGE-M3 将知识库文档转换为向量。
(2) 相似度检索：根据用户查询检索最相关的文档片段。
(3) 结果重排：使用 bge-reranker-v2-m3 优化检索结果排序。
(4) 答案生成：将检索结果作为上下文，调用 Qwen3.5-397B-A17B 或 DeepSeek-V3.2 生成回
答。
5.3 智能助手类应用（Agent）
智能助手（Agent Assistant）应用利用大语言模型的推理能力，能够自主对复杂的人类任
务进行目标规划、任务拆解、工具调用、过程迭代，并在没有人类干预的情况下完成任务。
用户可以通过“提示词”编写智能助手指令。为了能够达到更优的预期效果，也可以在指
令中明确任务目标、工作流程、资源和限制等。
(1) 通用智能助手： GPT-5.4、DeepSeek-V3.2、Qwen3.5-397B-A17B 等模型具备强大的推理和
工具调用能力，适合构建通用型智能助手，能够处理多样化的任务场景。
(2) 编程智能助手：GPT-5.3-Codex 和 Qwen3-Coder-Next 专为编程智能体设计，能够承担长
时间运行的复杂编程任务，支持深度调研、自主调用工具、端到端流程执行，适合构建软
件开发自动化助手。
附录：模型选型指南
任务类型 任务类型 Model ID
通用对话与问答 GPT-5.4 GPT-5.4
DeepSeek-V3.2 deepseek-v3:671b
上海科技大学 GenAI API 服务使用手册
12
Qwen3.5-397B-A17B qwen-instruct
复杂推理与数学 DeepSeek-R1-0528 deepseek-r1:671b
DeepSeek-Math-V2 deepseek-math
代码生成与调试
GPT-5.3-Codex gpt-5.3-codex
Qwen3-Coder-Next qwen-code
Qwen3.5-397B-A17B qwen-instruct
DeepSeek-R1-0528 deepseek-r1:671b
图像理解与 OCR Qwen3.5-397B-A17B qwen-instruct
语义检索与 RAG BGE-M3 bge-m3
bge-reranker-v2-m3 bge-reranker
长文档处理 DeepSeek-V3.2 deepseek-v3:671b
Qwen3.5-397B-A17B qwen-instruct
注：平台根据模型发展，会持续跟进，以正式发布的模型相关说明为准。

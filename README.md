# Singapore Housing Macro Agent · 初版

输入报告日期，获取官方宏观数据，检查候选指标的质量，选择合适的一组指标并生成可追溯的住房市场分析报告。

**目前的能力边界：**候选目录包含十二个已核验的公开序列，最终选择由真实数据检查结果决定，不预设五个入选指标。`rules` 是可离线测试的确定性基线，`llm` 是调用 SoCLaaS 或 OpenAI 的工具型 Agent。规则模式的解释来自人工审阅的机制模板，不能当成一次模型运行。初版不声称已经证明这些指标的预测能力，也不训练房价模型。

## 开始使用

需要 Python 3.11 或更新版本。以下命令均在本项目目录运行。运行下载需要联网；重现已保存的报告无需联网或 API 密钥。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -v
```

先直接重现附带的真实数据报告：

```bash
python -m housing_agent replay examples/sample_run --output runs/replayed-report.md
```

每次 replay 的输出文件必须是新文件，不覆盖原始运行目录。若同名文件已存在，请换一个名称。

重新访问官方接口并生成报告：

```bash
python -m housing_agent run --as-of 2026-09-30 --mode rules --limit 5 --output runs/new-report
```

`--limit` 是最多选择几个指标，不是必须凑满。输出目录必须不存在；重新运行请使用新名称，以保存不同数据版本。

默认 `--source-policy auto`：居民失业率和季度就业收入直接下载 MOM 官方文件，SORA 直接下载 MAS 日度文件并取经验证的月末值；其余九个候选通过 SingStat。所有下载在一次 `run` 内完成，无需手动准备文件。可用 `--source-policy singstat` 明确选择原有的单一来源路径。`--source-run` 则优先使用已验证快照，不发起任何新数据请求。

## 配置真实 Agent

```bash
python -m pip install -r requirements-llm.lock
# 仅首次配置时复制；已有 .env 时直接编辑，保留现有配置。
cp -n .env.example .env
```

在本地编辑 `.env`。使用 NUS SoCLaaS 时填写：

```dotenv
LLM_PROVIDER=soclaas
SOCLAAS_API_KEY=你的本地密钥
SOCLAAS_MODEL=qwen3.6:35b
```

运行完整流程：

```bash
python -m housing_agent run --as-of 2026-09-30 --mode llm --provider soclaas --limit 5 --output runs/live-soclaas
```

SoCLaaS 使用固定的 NUS 服务地址和 Chat Completions 接口。固定模型 ID 避免 `default` 别名改变时意外换模型；服务端更新同一 ID 下的权重仍可能改变结果。前两个阶段强制调用列举和检查工具，最终选择仍经过相同的数据与证据校验。

如需使用 OpenAI，在 `.env` 中填写 `OPENAI_API_KEY`、`OPENAI_MODEL`，并运行：

```bash
python -m housing_agent run --as-of 2026-09-30 --mode llm --provider openai --limit 5 --output runs/live-openai
```

OpenAI 路径保留 Responses 接口。两个服务使用各自的密钥和模型设置，互不回退。`--provider` 优先于 `LLM_PROVIDER`，都未配置时默认 OpenAI；`--model` 优先于相应服务的模型环境变量。程序只加载 `.env.example` 中列出的设置，已有环境变量优先，不执行配置内容。密钥仅保存在本地；`.env` 被 Git 忽略，交付压缩包也排除它。

若官方数据接口暂时不可用，可以**显式**复用附带的真实数据快照，并发起新的模型分析：

```bash
python -m housing_agent run --as-of 2026-09-30 --mode llm --provider soclaas --source-run examples/sample_run --output runs/soclaas-from-snapshot
```

`--source-run` 会核验原运行文件的校验和，以保存的完整观察重新计算报告日的数据与质量，再调用模型。新报告标明原始数据获取时间及“未刷新来源”，不会把旧快照当成刚下载的数据。它与 `replay` 不同：`replay` 只重现已保存文本，完全不调用模型。新鲜取数失败时不会自动切换快照。

这会产生真实 API 调用和相应费用。模型最多运行八轮，每轮最多生成四千 token；实际输入、输出和总用量、返回模型名称与耗时写入 `agent_trace.json` 和 `manifest.json`。这些是调用上限，不是美元费用上限。API 缺失、拒绝访问、超时或输出校验失败会明确报错，不会暗中改用规则模板并声称是 Agent 结果。

## 指标怎样选

直接查看[十二项指标池总表](examples/indicator_pool/indicator_pool.md)：每项同时列出口径与频率、纳入候选池的经济理由、官方来源、本次数据状态、选择结果及限制。表格依据 `independent_sources_run` 保存的真实取数与选择记录导出：三项取得数据并入选，九项因 SingStat 维护未取得数据。导出没有重新取数、重新筛选或调用模型。HTML 版本提供搜索和状态筛选，下载后在浏览器打开 `examples/indicator_pool/indicator_pool.html` 即可。

1. 在官方 SingStat 目录中搜索人口、GDP、失业、收入、利率、信贷、住宅和消费价格等主题，保存查询结果。
2. 按已审阅的候选目录尝试下载十二条序列：核验 SingStat 的表号、行号与元数据，或核验 MOM/MAS 文件的字段、标题、单位、频率和转换规则。
3. 以报告日期检查有效观察、近十年完整性、历史长度、时效性和比较基期。缺失的季度不能靠“往前数四行”补出来。
4. `rules` 根据数据可用性评分和经济类别多样性选择；`llm` 先调用查询与检查工具，再结合质量结果和经济机制提出选择与解释。两个模式都不能选入不合格数据。
5. 报告列出所有候选的入选/排除状态与说明。模型缺少逐项排除理由时明确标为系统补齐，不能当成模型解释。被排除不一定表示数据很差，也可能是名额限制或同类指标重复。

**候选目录的定义仍需要人工审阅。**官方搜索结果不会自动变成任意新指标，也不会自动修改解析代码。新增候选时更新 `housing_agent/data/catalogue.json`，核验真实 API 行名、单位、定义与经济理由，再执行测试。数据质量评分不是相关系数，也不是预测准确率。

完整性在最近十年窗口内、第一条到最后一条已捕获观察之间按真实日历计算；尾部缺期另外通过时效性检查。最低历史是年度三期、季度八期、月度二十四期；完整性至少四分之三。详细阈值与评分组成保存在每个候选的 `quality` 字段，属于可审阅的工程规则，不是估计得到的经济定律。

中文名称、候选经济理由、口径提醒及配置来源在 `housing_agent/data/indicator_notes.json` 中维护；实际取数成功时，表格优先保留该次下载的来源、英文定义、单位与频率。配置来源不代表本次下载成功，失败候选不会借用旧快照的数值或将占位零分显示成实际质量评分。表格中的“纳入候选池理由”是人工审阅的研究假设，“本次选择理由”来自保存的规则或模型决策，两者分开保存。

## 日期口径

`--as-of` 表示**观察日期截止日**，使用当前下载到的数据版本，不保证还原当时已经公布的信息。年度人口的官方参考日是六月末；其他序列通常按期末筛选。已知的观察级发布日期会被检查，但本数据源一般没有这些字段。

因此，“截至过去某日的观察分析”不能当作无前视信息的历史回测。表格的最后更新时间不等于每条观察的首次发布日期。报告和运行记录始终披露这个限制。

MAS 文件同时提供 SORA 所属日期和发布/指数日期。月末归属使用前者，后者作为原始字段与月份闭合依据保留；历史复合利率可能是回溯构建，因此不会将后者冒充整条历史序列首次可得的日期。MOM 文件的下载时间也不会当成每个季度的发布日期。

## 输出文件

| 文件 | 用途 |
|---|---|
| `report.md` / `report.html` | 分析报告及不依赖外部资源的文本预览 |
| `indicator_pool.md` / `indicator_pool.html` / `indicator_pool.json` | 全部候选的来源与理由总表、可搜索表格预览、完整结构化记录；每次成功生成报告时自动更新 |
| `discovery.json` / `catalogue.json` | 官方目录搜索结果与本次候选配置 |
| `raw/` / `retrievals.json` | 原始官方响应、请求地址、重试记录、时间与哈希 |
| `normalized.json` | 保留原始值、期间和位置的规范化观察，包含下载到的完整历史 |
| `processed.csv` | 已按报告日期筛选的观察，保留原始响应的位置和哈希 |
| `evaluations.json` | 按报告日筛选后的观察、质量检查、计算公式与输入记录 |
| `selection.json` | 入选、排除理由和已保存的解释 |
| `agent_trace.json` | 仅真实 Agent 模式产生；实际模型/工具交互、校验结果和 token 用量 |
| `report_context.json` / `manifest.json` | 报告配置、状态、代码版本和全部运行文件的 SHA-256 |

追溯路径：报告证据 ID → `evaluations.json` 的变化公式和输入观察 → `raw_index`/`raw_locator` → `raw/` 的原始响应。CSV 保留行列位置，XLSX 保留工作表与单元格，MAS 月度采样保留原始日度日期。独立下载的定义与转换说明单独保存，明确标为程序生成的适配器元数据，不冒充官方 API 返回。报告数字由确定性程序填入；模型叙述禁止添加数字，并校验证据 ID。语法检查仍不能证明所有经济解释正确，需人工复核。

## 官方数据源维护

2026 年 10 月 1 日的 HTTP 502 已核实：Table Builder 返回明确的官方维护提示，普通官网首页仍可访问。详情见[诊断记录](docs/evidence/singstat-maintenance-diagnosis.json)。这类服务端维护需要等待官方恢复，修改模型或 API 密钥无法修复。

默认模式识别明确的维护公告后，停止继续请求 SingStat，但仍尝试 MOM 与 MAS。报告列出未能获取的候选；只有通过质量检查的数据才参与选择，可能少于五项。全部数据不合格时才结束运行，不编造报告或调用模型。没有维护提示的临时 502 仍按有限重试处理。显式使用 `--source-policy singstat` 时，保留原有的维护即停止行为与 `source_maintenance` 记录。

维护结束后，用普通 `run` 命令和新输出目录重新下载即可恢复其余候选的尝试。若需要基于以前保存的完整覆盖继续分析，可使用前述 `--source-run` 选项；报告会保留原始抓取时间，明确注明未刷新数据。程序不会把旧快照自动混进新下载结果。

## 其他命令与文档

为已有运行补出指标池表，不修改原运行、不重新取数或选择，也不调用模型：

```bash
python -m housing_agent indicator-pool examples/independent_sources_run --output runs/indicator-pool-export
```

命令先验证原运行文件的 SHA-256，再输出三个表格文件及独立的 `manifest.json`，记录所用运行和输入文件哈希。输出必须是原运行目录之外的新目录。

```bash
python -m housing_agent discover "residential properties" --output runs/discovery
python -m housing_agent --help
```

- [工程设计与局限](docs/engineering-report.md)
- [已核验的数据源与口径](docs/source-evidence.md)
- [测试与实际运行证据](docs/validation.md)
- [官网直接取数样例报告](examples/independent_sources_run/report.md)（SingStat 维护期间，MOM/MAS 三项实时下载通过；规则模式）
- [真实 SoCLaaS 样例报告](examples/soclaas_verified_run/report.md)（已保存的官方数据 + 新模型调用）
- [规则基线样例报告](examples/sample_run/report.md)

此仓库保留实际开发提交历史。准备正式提交时，请按题目要求将压缩包改为 `Firstname Lastname Engineering Task.zip`，包含 `.git`；排除 `.env`、虚拟环境和无关运行目录。是否已完成真实模型联调，以 `docs/validation.md` 记录为准。

# 硅基流动 GLM 接入与费用

服务：SiliconFlow；固定地址：`https://api.siliconflow.cn/v1`；模型：`zai-org/GLM-5.3`。密钥保存在本地被 Git 忽略的 `.env`，不包含在代码、报告和发布包中。三个服务使用独立配置，不会自动借用其他服务的密钥或模型。

## 已验证的接口行为

2026 年 10 月 1 日两次小规模真实请求均成功：具名工具选择、严格工具 schema、单工具调用，以及携带 `reasoning_content` 的后续工具对话均被接受。证据见[首次探测](evidence/siliconflow-glm-probe.json)和[多轮探测](evidence/siliconflow-glm-roundtrip-probe.json)。探测使用了合成算术任务，并不证明住房分析质量。

首次发送 `enable_thinking=false` 后仍返回推理内容与推理 token；这不是成功关闭推理的证据。Z.ai 官方维护者也说明 GLM-5.3 不支持非推理模式，见[原厂说明](https://huggingface.co/zai-org/GLM-5.3/discussions/21)。正式配置发送 `enable_thinking=true`、`thinking_budget=4096`，不沿用 SoCLaaS 的 `reasoning_effort=none`。

[硅基流动接口文档](https://docs.siliconflow.cn/docs/api/chat-completions-post)说明 `max_tokens` 不包含推理 token。程序设置每次 `max_tokens=4000`、最多八次调用、每次一百二十秒超时，SDK 自动重试为零。请求的推理预算不是已验证的 GLM 硬限制；超时也不能保证服务端未计费。中断、截断和失败会保存为失败，不暗中改用规则模式。

## 计价口径

2026 年 10 月 1 日核验的[官方价格页](https://www.siliconflow.cn/pricing)与[GLM-5.3 上线公告](https://siliconflow.cn/news/is96b67809iqvyxrumd90q7x)：每百万 token，未命中缓存的输入为人民币 8 元，命中缓存的输入为 2 元，输出为 28 元。

估算费用 = 未缓存输入 × 8 / 1,000,000 + 缓存输入 × 2 / 1,000,000 + 输出 × 28 / 1,000,000。

以服务端返回的 `completion_tokens` 作为输出总量，其中 `reasoning_tokens` 是子集，不能再加一次。缓存 token 也是输入总量的子集。若服务端没有提供可核验的缓存拆分，按输入全部未缓存保守估算。价格估算不等于账户账单；余额、优惠和最终扣费应以控制台为准。

之前的 35B 流程实际输入 41,113、输出 2,656，按该价格且不考虑缓存约为 0.4035 元；这是按旧模型用量换算，不能当作 GLM 的实际开销。另一轮多次修正用量对应约 1.5062 元。初次联调预留 50 元是预算建议，不是程序自动执行的充值或消费限额。

新模型沿用同一套官方取数、确定性计算、候选质量门槛、证据校验和非数值叙述约束。更换模型不会把工程质量评分变成预测准确率，也不会免除经济口径复核。

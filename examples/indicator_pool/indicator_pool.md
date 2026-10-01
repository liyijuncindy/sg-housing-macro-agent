# 新加坡住宅市场：完整候选指标池

依据已保存运行导出；未刷新数据、未重新筛选、未调用模型。<br>
本表导出时间：2026-10-01T11:13:03+00:00<br>
报告截止日期：2026-10-01；运行：independent\_sources\_run；来源运行：independent\_sources\_run<br>
原运行报告生成时间：2026-10-01T09:19:06+00:00；模式：Deterministic rules; reviewed qualitative templates, no model call<br>
实际来源的抓取时间见下；抓取时间不等于数据观测期或官方发布日期。<br>
实际来源抓取范围：2026-10-01T09:19:06+00:00 至 2026-10-01T09:19:07+00:00；0 项已获取来源缺少有效时区时间戳。<br>
共 12 个候选，3 个进入本次报告。<br>

> 这是完整候选池，按配置顺序保留全部指标；进入候选池不等于进入本次报告。
> 质量分只衡量数据可用性，未验证这些指标的预测能力，也不证明因果关系。
> 中文候选理由与限制是随版本保存的编辑说明；模型或规则的本次选择理由另行标注，原文完整保留。
> 没有原始文件来源或有效观测时，不填入旧数据，也不把失败记录中的占位零分当作真实质量评分。
> 报告日期按观测参考日期或期间末筛选当前捕获版本，不等于重建当时可获得的信息集合。

| 指标 | 口径与频率 | 纳入候选池理由 | 官方来源 | 本次数据状态 | 本次选择与理由 | 限制 |
|---|---|---|---|---|---|---|
| 居民人口<br>M810001:2 | 每年 6 月底的新加坡公民及永久居民人数；自 2003 年起，不包括参考日已连续在海外居住至少 12 个月的居民。<br>年度；人 | 用于观察本地住房需求的潜在人口基础；若家庭形成和购买能力同步增加，人口增长可能支持购房或租房需求。 | 新加坡统计局（DOS）<br>[SingStat 官方表：人口与人口结构](<https://tablebuilder.singstat.gov.sg/table/TS/M810001>)<br>配置来源，本次未获取 | 维护期间未获取；最新期间和值：未提供；质量分：未评估或未提供 | 维护期间未获取；未进行本次质量评分，不能据此认定指标无效。由确定性规则选择，未调用模型解释。<br>确定性筛选规则（非模型理由）；原文见下方折叠依据 | 人口不等于家庭数、购房人数或住房需求预测；1990 年前的人口概念及 2003 年覆盖变化限制长期可比性。年度参考日为 6 月 30 日，不是年底。 |
| 非居民人口<br>M810001:5 | 每年 6 月底在新加坡工作、学习或居住但无永久居民身份的外国人数，不包括游客及短期访客。<br>年度；人 | 用于观察人口流动相关的租赁需求；其中寻求普通住宅住宿的人口增加，可能支持租房需求，并间接影响住房市场。 | 新加坡统计局（DOS）<br>[SingStat 官方表：人口与人口结构](<https://tablebuilder.singstat.gov.sg/table/TS/M810001>)<br>配置来源，本次未获取 | 维护期间未获取；最新期间和值：未提供；质量分：未评估或未提供 | 维护期间未获取；未进行本次质量评分，不能据此认定指标无效。由确定性规则选择，未调用模型解释。<br>确定性筛选规则（非模型理由）；原文见下方折叠依据 | 包含宿舍等普通住宅租赁以外的住宿安排，不能直接换算为租房人数；未区分收入、签证类别、家庭规模或住房类型。年度参考日为 6 月 30 日。 |
| 实际国内生产总值（GDP）<br>M015661:1 | 按 2015 年链式价格计量的季度国内生产总值，单位为百万新加坡元，覆盖新加坡整体经济。<br>季度；百万新元 | 用于观察总体经济活动；经济增长可能通过就业、收入和信心影响购房能力及就业相关的租赁需求。 | 新加坡统计局（DOS）<br>[SingStat 官方表：季度实际 GDP](<https://tablebuilder.singstat.gov.sg/table/TS/M015661>)<br>配置来源，本次未获取 | 维护期间未获取；最新期间和值：未提供；质量分：未评估或未提供 | 维护期间未获取；未进行本次质量评分，不能据此认定指标无效。由确定性规则选择，未调用模型解释。<br>确定性筛选规则（非模型理由）；原文见下方折叠依据 | 该序列未标注季节调整，优先比较同比；初步估计及历史值可能修订。GDP 与住房可能受共同因素影响，不能据此认定因果或预测能力。 |
| 居民失业率（经季节调整）<br>M182342:2 | 季度末居民劳动力中的失业者比例，已经季节调整；居民指新加坡公民及永久居民，单位为百分比。<br>季度；% | 用于观察居民就业压力；失业率上升可能削弱购房信心、偿贷能力和租金承受能力。 | MINISTRY OF MANPOWER<br>[MOM official CSV](<https://stats.mom.gov.sg/Pages/Unemployment-Summary-Table.aspx>)<br>本次实际来源 | 最新可用：2026-Q2；2.9 %；质量分：95/100 | 已选；满足本次数据门槛。在该经济类别中数据质量分最高，优先补足类别覆盖；同分按指标 ID 排序。由确定性规则选择，未调用模型解释。<br>确定性筛选规则（非模型理由）；原文见下方折叠依据 | 不涵盖非居民劳动力，也不衡量工资、就业不足或岗位稳定性；季调值可修订。变化应以百分点表示，保留实际来源的公布精度。 |
| 就业居民平均月度就业总收入（含公积金、不含奖金）<br>M184101:1 | 本次实际来源口径：Mean gross monthly employment income of employed residents, including employer/platform operator CPF contributions and excluding bonus; before employee CPF and personal income tax deductions.<br>季度；新元 | 用于观察每名就业居民的收入能力；收入增加可能改善购房融资能力和租金承受能力，与经济总量指标形成补充。 | MINISTRY OF MANPOWER<br>[MOM official XLSX](<https://stats.mom.gov.sg/Pages/Income-Summary-Table.aspx>)<br>本次实际来源 | 最新可用：2026-Q2；6,605 新元；初步值（官方标记）；质量分：95/100 | 已选；满足本次数据门槛。在该经济类别中数据质量分最高，优先补足类别覆盖；同分按指标 ID 排序。由确定性规则选择，未调用模型解释。<br>确定性筛选规则（非模型理由）；原文见下方折叠依据 | 是个人均值，不是家庭收入中位数或到手现金；高收入者及就业人员构成变化会影响均值。优先比较同比，保留实际来源提供的初步值标记；平台运营商 CPF 的说明须结合当前直连 MOM 原文，不能替代旧快照的来源说明。 |
| 个人可支配收入总额（名义）<br>M016081:1 | 按现价计量的季度个人可支配收入总额，单位为百万新加坡元。<br>季度；百万新元 | 用于观察可供居民部门消费和储蓄的总体收入规模；收入总额增加可能支持住房购买及租赁支出。 | 新加坡统计局（DOS）<br>[SingStat 官方表：个人可支配收入](<https://tablebuilder.singstat.gov.sg/table/TS/M016081>)<br>配置来源，本次未获取 | 维护期间未获取；最新期间和值：未提供；质量分：未评估或未提供 | 维护期间未获取；未进行本次质量评分，不能据此认定指标无效。由确定性规则选择，未调用模型解释。<br>确定性筛选规则（非模型理由）；原文见下方折叠依据 | 是名义总额，不是人均、户均或家庭收入中位数；增长也可能来自物价或人口增加。序列未标注季节调整，优先比较同比。 |
| 三个月复利 SORA（月末值）<br>M700071:23 | 三个月复利新加坡隔夜平均利率的月末值，单位为年利率百分比。<br>月度；%/年 | 用于观察融资成本；基准利率上升可能随房贷重定价提高偿贷负担，并改变购房与租房选择，对租金的净影响不预设方向。 | MONETARY AUTHORITY OF SINGAPORE<br>[MAS direct public daily CSV; verified month-end sampling](<https://eservices.mas.gov.sg/statistics/dir/DomesticInterestRates.aspx>)<br>本次实际来源 | 最新可用：2026-09；1.2336 %/年；质量分：100/100 | 已选；满足本次数据门槛。在该经济类别中数据质量分最高，优先补足类别覆盖；同分按指标 ID 排序。由确定性规则选择，未调用模型解释。<br>确定性筛选规则（非模型理由）；原文见下方折叠依据 | 月末值不是月均值，也不是具体房贷报价；变化以基点表示，传导取决于利差及重定价安排。使用 MAS 日频路径时，按 SORA 计息日期而非公布日期归月，缺少月末完整性证据的月份暂不纳入；实际转换以该次来源元数据为准。 |
| 住房与过桥贷款余额<br>M701091:1.2.1 | 商业银行向居民提供的消费类住房及过桥贷款月末余额，单位为百万新加坡元。<br>月度；百万新元 | 用于观察住房融资活动及其规模；贷款余额扩张可能与融资购房需求同步变化，也可能反映房价上涨后的借款增加。 | 新加坡金融管理局（MAS）<br>[SingStat 官方表（原发布：MAS）：商业银行贷款](<https://tablebuilder.singstat.gov.sg/table/TS/M701091>)<br>配置来源，本次未获取 | 维护期间未获取；最新期间和值：未提供；质量分：未评估或未提供 | 维护期间未获取；未进行本次质量评分，不能据此认定指标无效。由确定性规则选择，未调用模型解释。<br>确定性筛选规则（非模型理由）；原文见下方折叠依据 | 是贷款存量，不是新增按揭、审批量或信贷可得性；还款也会改变余额。新报表口径自 2021 年 7 月开始，不能直接拼接旧口径；存在反向因果。 |
| 已竣工私人住宅存量<br>M400841:1 | 季度末取得临时入伙准证（TOP）或法定竣工证书（CSC）的私人住宅总套数，包括有地及非有地住宅、已入住及空置单位。<br>季度；套 | 用于观察当期可使用的住宅供给规模，并为人口及空置套数提供参照；新增竣工住宅可能缓解相对于需求的供给约束。 | 新加坡市区重建局（URA）<br>[SingStat 官方表（原发布：URA）：私人住宅存量与空置](<https://tablebuilder.singstat.gov.sg/table/TS/M400841>)<br>配置来源，本次未获取 | 维护期间未获取；最新期间和值：未提供；质量分：未评估或未提供 | 维护期间未获取；未进行本次质量评分，不能据此认定指标无效。由确定性规则选择，未调用模型解释。<br>确定性筛选规则（非模型理由）；原文见下方折叠依据 | 官方名称中的 available 指已竣工总存量，不是挂牌出售或出租量；不含 HDB 组屋、执行共管公寓（EC）及官方列明的其他排除项。1995—1996 年覆盖扩展影响长期可比性。 |
| 空置私人住宅套数<br>M400841:2 | 季度末已竣工但空置的私人住宅套数；覆盖有地及非有地住宅，范围与同表已竣工存量一致。<br>季度；套 | 用于观察住宅吸收情况；在总存量、区位和需求可比的条件下，空置增加可能对应较弱的价格或租金压力。 | 新加坡市区重建局（URA）<br>[SingStat 官方表（原发布：URA）：私人住宅存量与空置](<https://tablebuilder.singstat.gov.sg/table/TS/M400841>)<br>配置来源，本次未获取 | 维护期间未获取；最新期间和值：未提供；质量分：未评估或未提供 | 维护期间未获取；未进行本次质量评分，不能据此认定指标无效。由确定性规则选择，未调用模型解释。<br>确定性筛选规则（非模型理由）；原文见下方折叠依据 | 这是套数，不是空置率；必须结合同期已竣工存量，空置套数上升仍可能伴随空置率下降。不含 HDB 及 EC，与存量、供应储备同属住房供给指标组。 |
| 非有地私人住宅供应储备<br>M400391:2 | 季度末处于不同开发阶段的非有地私人住宅供应储备套数，包含规划及建设中的项目。<br>季度；套 | 用于观察未来潜在供给及市场预期；项目陆续竣工后可能增加购买和租赁市场的住宅供给。 | 新加坡市区重建局（URA）<br>[SingStat 官方表（原发布：URA）：私人住宅开发供应储备](<https://tablebuilder.singstat.gov.sg/table/TS/M400391>)<br>配置来源，本次未获取 | 维护期间未获取；最新期间和值：未提供；质量分：未评估或未提供 | 维护期间未获取；未进行本次质量评分，不能据此认定指标无效。由确定性规则选择，未调用模型解释。<br>确定性筛选规则（非模型理由）；原文见下方折叠依据 | 不是已竣工住宅，也不是确定的竣工预测；交付时间、阶段和取消情况会变化。不含有地住宅、HDB 及 EC，与存量、空置同属住房供给指标组。 |
| 整体消费者价格指数（CPI）<br>M213751:1 | 基于官方家庭支出权重的整体消费者价格指数，以 2024 年为 100，按月公布。<br>月度；指数 | 用于观察生活成本和实际购买力；通胀可能影响家庭预算、持有成本及融资环境，对房价和租金的净作用不预设方向。 | 新加坡统计局（DOS）<br>[SingStat 官方表：消费者价格指数](<https://tablebuilder.singstat.gov.sg/table/TS/M213751>)<br>配置来源，本次未获取 | 维护期间未获取；最新期间和值：未提供；质量分：未评估或未提供 | 维护期间未获取；未进行本次质量评分，不能据此认定指标无效。由确定性规则选择，未调用模型解释。<br>确定性筛选规则（非模型理由）；原文见下方折叠依据 | 不是住宅售价指数或建筑成本指数；包含住房相关分项，与租金可能存在指标重叠，不能视为独立的因果或已验证预测变量。 |

## 原始依据

<details><summary>居民人口（M810001:2）</summary>

<p><strong>选择理由来源</strong></p><pre>确定性筛选规则（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>Excluded by data-quality rules: SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>来源定义原文</strong></p><pre>Singapore citizens and permanent residents as at end-June; from 2003 excludes residents continuously overseas for at least 12 months at the reference date.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Singapore resident population, not number of households or homebuyers.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>数据警告原文</strong></p><pre>未提供</pre>

</details>

<details><summary>非居民人口（M810001:5）</summary>

<p><strong>选择理由来源</strong></p><pre>确定性筛选规则（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>Excluded by data-quality rules: SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>来源定义原文</strong></p><pre>Foreigners working, studying or living in Singapore without permanent residence, excluding tourists and short-term visitors, as at end-June.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Singapore non-resident population; housing needs include arrangements beyond private residential rentals.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>数据警告原文</strong></p><pre>未提供</pre>

</details>

<details><summary>实际国内生产总值（GDP）（M015661:1）</summary>

<p><strong>选择理由来源</strong></p><pre>确定性筛选规则（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>Excluded by data-quality rules: SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>来源定义原文</strong></p><pre>Quarterly gross domestic product measured in chained 2015 Singapore dollars; a measure of real domestic economic activity.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Whole Singapore economy; million Singapore dollars at chained 2015 prices.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>数据警告原文</strong></p><pre>未提供</pre>

</details>

<details><summary>居民失业率（经季节调整）（M182342:2）</summary>

<p><strong>选择理由来源</strong></p><pre>确定性筛选规则（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>Selected for economic-family coverage (labour_market): highest data-quality score within this family, with deterministic id tie-breaking. The family defaults to the theme when not specified.</pre>

<p><strong>来源定义原文</strong></p><pre>Resident unemployment rate at quarter-end, seasonally adjusted; residents are citizens and permanent residents.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Resident labour force, not the entire resident population or non-resident workforce.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.</pre>

<p><strong>源文件注释</strong></p><pre>Resident means Singapore citizens and permanent residents. This adapter selects quarter rows and the seasonally_adjusted_unemployment_rate column, preserving the published CSV precision. It excludes annual averages and unadjusted rates. Seasonal adjustment can be revised. The CSV does not provide observation publication dates or preliminary flags; none are inferred. Definitions and current release notes: https://stats.mom.gov.sg/Pages/Unemployment-Summary-Table.aspx</pre>

<p><strong>源行注释</strong></p><pre>Resident means Singapore citizens and permanent residents. This adapter selects quarter rows and the seasonally_adjusted_unemployment_rate column, preserving the published CSV precision. It excludes annual averages and unadjusted rates. Seasonal adjustment can be revised. The CSV does not provide observation publication dates or preliminary flags; none are inferred. Definitions and current release notes: https://stats.mom.gov.sg/Pages/Unemployment-Summary-Table.aspx</pre>

<p><strong>原始文件</strong></p><pre>raw/mom_resident_unemployment_01_70f48654b5a63952.csv</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>832bf5774be0a6d48d85e8869d58327140c2bd04bb053064a8cbdc95ffa7ded1</pre>

</details>

<details><summary>就业居民平均月度就业总收入（含公积金、不含奖金）（M184101:1）</summary>

<p><strong>选择理由来源</strong></p><pre>确定性筛选规则（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>Selected for economic-family coverage (household_income): highest data-quality score within this family, with deterministic id tie-breaking. The family defaults to the theme when not specified.</pre>

<p><strong>来源定义原文</strong></p><pre>Mean gross monthly employment income of employed residents, including employer/platform operator CPF contributions and excluding bonus; before employee CPF and personal income tax deductions.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Employed citizens and permanent residents excluding full-time National Servicemen; Singapore dollars per employed person.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.</pre>

<p><strong>源文件注释</strong></p><pre>1. Residents refer to Singapore Citizens and Permanent Residents. 2. Gross monthly income refers to income earned from employment. For employees, it refers to the gross monthly wages or salaries before deduction of employee CPF contributions and personal income tax. It comprises basic wages, overtime pay, commissions, tips and other allowances. For self-employed persons, gross monthly income refers to the average monthly profits from their business, trade or profession (i.e. total receipts less business expenses incurred) before deduction of income tax and platform workers’ share of CPF contributions. 3. Data are for all employed persons excluding full-time National Servicemen. 4. The change in mean gross monthly income (GMI) (change in income per worker) is a suitable statistic for comparison with the change in labour productivity (change in value-added per worker) as both are expressed on a “per worker” basis.  When studying the change in mean gross monthly income of any quarter, it would be more meaningful to compare it with the same quarter of prior years, so as to limit seasonal variations that mask the underlying actual trend in income. Also, as the mean GMI pertains to mean earnings, it can be skewed upwards by a small number of very high income earners. 5. p: preliminary.</pre>

<p><strong>源行注释</strong></p><pre>1. Residents refer to Singapore Citizens and Permanent Residents. 2. Gross monthly income refers to income earned from employment. For employees, it refers to the gross monthly wages or salaries before deduction of employee CPF contributions and personal income tax. It comprises basic wages, overtime pay, commissions, tips and other allowances. For self-employed persons, gross monthly income refers to the average monthly profits from their business, trade or profession (i.e. total receipts less business expenses incurred) before deduction of income tax and platform workers’ share of CPF contributions. 3. Data are for all employed persons excluding full-time National Servicemen. 4. The change in mean gross monthly income (GMI) (change in income per worker) is a suitable statistic for comparison with the change in labour productivity (change in value-added per worker) as both are expressed on a “per worker” basis.  When studying the change in mean gross monthly income of any quarter, it would be more meaningful to compare it with the same quarter of prior years, so as to limit seasonal variations that mask the underlying actual trend in income. Also, as the mean GMI pertains to mean earnings, it can be skewed upwards by a small number of very high income earners. 5. p: preliminary.</pre>

<p><strong>原始文件</strong></p><pre>raw/mom_mean_employment_income_02_8fc73a0c377c47e2.xlsx</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>dc0ab955ae76b339d1955d7f2482b80121258a957ce51896a2bf773f581c1d77</pre>

</details>

<details><summary>个人可支配收入总额（名义）（M016081:1）</summary>

<p><strong>选择理由来源</strong></p><pre>确定性筛选规则（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>Excluded by data-quality rules: SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>来源定义原文</strong></p><pre>Quarterly aggregate personal disposable income at current prices.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Singapore aggregate nominal personal disposable income; million Singapore dollars, not median household income.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>数据警告原文</strong></p><pre>未提供</pre>

</details>

<details><summary>三个月复利 SORA（月末值）（M700071:23）</summary>

<p><strong>选择理由来源</strong></p><pre>确定性筛选规则（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>Selected for economic-family coverage (financing_cost): highest data-quality score within this family, with deterministic id tie-breaking. The family defaults to the theme when not specified.</pre>

<p><strong>来源定义原文</strong></p><pre>Three-month compounded Singapore Overnight Rate Average (SORA), observed at month-end and expressed as an annual percentage rate.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Singapore-dollar benchmark interest rate; not an individual mortgage offer.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.</pre>

<p><strong>源行注释</strong></p><pre>Monthly sampling uses the last SORA Value Date, not the SORA Publication Date. Both dates are preserved in observations. Group daily records by the calendar month of SORA Value Date and select the last value-date record, not the last publication-date record and not an average. The month must end on or before as_of. Its last record&#x27;s SORA Publication Date must cross that month-end, providing conservative evidence that the last business-day record was received. Otherwise omit the month instead of substituting an earlier value. This can temporarily omit the newest month. A null final value remains null. The original daily CSV dates and row position are retained. Source publication dates are CSV labels, also described by MAS as compounded-index value dates; they do not prove when the historical three-month series was first available. No observation published_at is invented.</pre>

<p><strong>来源转换说明</strong></p><pre>Group daily records by the calendar month of SORA Value Date and select the last value-date record, not the last publication-date record and not an average. The month must end on or before as_of. Its last record&#x27;s SORA Publication Date must cross that month-end, providing conservative evidence that the last business-day record was received. Otherwise omit the month instead of substituting an earlier value. This can temporarily omit the newest month. A null final value remains null. The original daily CSV dates and row position are retained. Source publication dates are CSV labels, also described by MAS as compounded-index value dates; they do not prove when the historical three-month series was first available. No observation published_at is invented.</pre>

<p><strong>原始文件</strong></p><pre>raw/mas_sora_daily_04_78ea273ef62f7c09.csv</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>53828a3f009324dce050a6a8bd0285bc071da79271bb62d4151a944d1ec257c9</pre>

</details>

<details><summary>住房与过桥贷款余额（M701091:1.2.1）</summary>

<p><strong>选择理由来源</strong></p><pre>确定性筛选规则（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>Excluded by data-quality rules: SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>来源定义原文</strong></p><pre>Commercial-bank consumer housing and bridging loans to residents outstanding at month-end.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Commercial-bank lending stock to residents; million Singapore dollars, not new monthly mortgage approvals.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>数据警告原文</strong></p><pre>未提供</pre>

</details>

<details><summary>已竣工私人住宅存量（M400841:1）</summary>

<p><strong>选择理由来源</strong></p><pre>确定性筛选规则（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>Excluded by data-quality rules: SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>来源定义原文</strong></p><pre>Completed private residential units at quarter-end with a Temporary Occupation Permit or Certificate of Statutory Completion; this is the housing stock labelled available by URA.</pre>

<p><strong>来源覆盖范围</strong></p><pre>All landed and non-landed private residential units; excludes hostels, HDB flats, tenement houses, parsonages and Executive Condominiums.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>数据警告原文</strong></p><pre>未提供</pre>

</details>

<details><summary>空置私人住宅套数（M400841:2）</summary>

<p><strong>选择理由来源</strong></p><pre>确定性筛选规则（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>Excluded by data-quality rules: SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>来源定义原文</strong></p><pre>Number of vacant completed private residential units at quarter-end, not the vacancy rate.</pre>

<p><strong>来源覆盖范围</strong></p><pre>All landed and non-landed private residential units; same exclusions and coverage as the completed stock in table M400841 row 1.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>数据警告原文</strong></p><pre>未提供</pre>

</details>

<details><summary>非有地私人住宅供应储备（M400391:2）</summary>

<p><strong>选择理由来源</strong></p><pre>确定性筛选规则（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>Excluded by data-quality rules: SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>来源定义原文</strong></p><pre>Total non-landed private residential units in the pipeline at quarter-end across development statuses.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Non-landed private residential pipeline; excludes hostels, HDB flats, tenement houses, parsonages and Executive Condominiums.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>数据警告原文</strong></p><pre>未提供</pre>

</details>

<details><summary>整体消费者价格指数（CPI）（M213751:1）</summary>

<p><strong>选择理由来源</strong></p><pre>确定性筛选规则（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>Excluded by data-quality rules: SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>来源定义原文</strong></p><pre>All-items Consumer Price Index, 2024 = 100, based on the official household expenditure weighting pattern.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Singapore consumer prices; index, not residential property sale prices.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. SingStat Table Builder is undergoing maintenance. The SingStat Table Builder and SANDRA (Statistics ANd Data Retrieval A.I. assistant) are currently undergoing maintenance. We will work to complete the maintenance work ASAP. Thank you for your patience.</pre>

<p><strong>数据警告原文</strong></p><pre>未提供</pre>

</details>

中文说明来源：housing\_agent/data/indicator\_notes.json

说明内容 SHA-256：`81bfd13fd3ab8bed3d1ae94f6c13d057bece37e28574aff3efee151b3d72618a`。完整说明随 JSON 保存。

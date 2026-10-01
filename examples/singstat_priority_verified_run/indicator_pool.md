# 新加坡住宅市场：完整候选指标池

报告截止日期：2026-10-01；运行：singstat\_priority\_verified\_run；来源运行：singstat\_priority\_verified\_run<br>
原运行报告生成时间：2026-10-01T11:45:38+00:00；模式：Live SoCLaaS Chat Completions tool-calling agent \(qwen3.6:35b\)<br>
实际来源的抓取时间见下；抓取时间不等于数据观测期或官方发布日期。<br>
实际来源抓取范围：2026-10-01T11:47:03+00:00 至 2026-10-01T11:47:07+00:00；0 项已获取来源缺少有效时区时间戳。<br>
共 16 个候选，5 个进入本次报告。<br>

> 这是完整候选池，按配置顺序保留全部指标；进入候选池不等于进入本次报告。
> 质量分只衡量数据可用性，未验证这些指标的预测能力，也不证明因果关系。
> 中文候选理由与限制是随版本保存的编辑说明；模型或规则的本次选择理由另行标注，原文完整保留。
> 没有原始文件来源或有效观测时，不填入旧数据，也不把失败记录中的占位零分当作真实质量评分。
> 报告日期按观测参考日期或期间末筛选当前捕获版本，不等于重建当时可获得的信息集合。

| 指标 | 口径与频率 | 纳入候选池理由 | 官方来源 | 本次数据状态 | 本次选择与理由 | 限制 |
|---|---|---|---|---|---|---|
| 居民人口<br>M810001:2 | 每年 6 月底的新加坡公民及永久居民人数；自 2003 年起，不包括参考日已连续在海外居住至少 12 个月的居民。<br>年度；人 | 用于观察本地住房需求的潜在人口基础；若家庭形成和购买能力同步增加，人口增长可能支持购房或租房需求。 | SINGAPORE DEPARTMENT OF STATISTICS<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M810001>)<br>本次实际来源 | 最新可用：2026；4,231,524 人；质量分：100/100 | 已达到数据门槛，未进入本次报告；不代表预测能力较差。原因为系统补充，不能当作模型逐项解释。<br>系统补充说明（非模型理由）；原文见下方折叠依据 | 人口不等于家庭数、购房人数或住房需求预测；1990 年前的人口概念及 2003 年覆盖变化限制长期可比性。年度参考日为 6 月 30 日，不是年底。 |
| 非居民人口<br>M810001:5 | 每年 6 月底在新加坡工作、学习或居住但无永久居民身份的外国人数，不包括游客及短期访客。<br>年度；人 | 用于观察人口流动相关的租赁需求；其中寻求普通住宅住宿的人口增加，可能支持租房需求，并间接影响住房市场。 | SINGAPORE DEPARTMENT OF STATISTICS<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M810001>)<br>本次实际来源 | 最新可用：2026；1,976,999 人；质量分：100/100 | 已达到数据门槛，未进入本次报告；不代表预测能力较差。原因为系统补充，不能当作模型逐项解释。<br>系统补充说明（非模型理由）；原文见下方折叠依据 | 包含宿舍等普通住宅租赁以外的住宿安排，不能直接换算为租房人数；未区分收入、签证类别、家庭规模或住房类型。年度参考日为 6 月 30 日。 |
| 实际国内生产总值（GDP）<br>M015661:1 | 按 2015 年链式价格计量的季度国内生产总值，单位为百万新加坡元，覆盖新加坡整体经济。<br>季度；百万新元 | 用于观察总体经济活动；经济增长可能通过就业、收入和信心影响购房能力及就业相关的租赁需求。 | SINGAPORE DEPARTMENT OF STATISTICS<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M015661>)<br>本次实际来源 | 最新可用：2026-Q2；155,247.2 百万新元；质量分：95/100 | 已选；满足本次数据门槛。模型选择理由见原文。<br>模型原始理由；原文见下方折叠依据 | 该序列未标注季节调整，优先比较同比；初步估计及历史值可能修订。GDP 与住房可能受共同因素影响，不能据此认定因果或预测能力。 |
| 居民失业率（经季节调整）<br>M182342:2 | 季度末居民劳动力中的失业者比例，已经季节调整；居民指新加坡公民及永久居民，单位为百分比。<br>季度；% | 用于观察居民就业压力；失业率上升可能削弱购房信心、偿贷能力和租金承受能力。 | MINISTRY OF MANPOWER<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M182342>)<br>本次实际来源 | 最新可用：2026-Q2；2.9 %；质量分：95/100 | 已选；满足本次数据门槛。模型选择理由见原文。<br>模型原始理由；原文见下方折叠依据 | 不涵盖非居民劳动力，也不衡量工资、就业不足或岗位稳定性；季调值可修订。变化应以百分点表示，保留实际来源的公布精度。 |
| 就业居民平均月度就业总收入（含公积金、不含奖金）<br>M184101:1 | 就业居民的平均月度就业总收入，含雇主公积金（CPF）缴款、不含奖金；单位为新加坡元，按季度公布。覆盖就业公民及永久居民，不包括全职国民服役人员。当前直连 MOM 口径还明确包含平台运营商 CPF 缴款。<br>季度；新元 | 用于观察每名就业居民的收入能力；收入增加可能改善购房融资能力和租金承受能力，与经济总量指标形成补充。 | MINISTRY OF MANPOWER<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M184101>)<br>本次实际来源 | 最新可用：2026-Q2；6,605 新元；质量分：95/100 | 已选；满足本次数据门槛。模型选择理由见原文。<br>模型原始理由；原文见下方折叠依据 | 是个人均值，不是家庭收入中位数或到手现金；高收入者及就业人员构成变化会影响均值。优先比较同比，保留实际来源提供的初步值标记；平台运营商 CPF 的说明须结合当前直连 MOM 原文，不能替代旧快照的来源说明。 |
| 个人可支配收入总额（名义）<br>M016081:1 | 按现价计量的季度个人可支配收入总额，单位为百万新加坡元。<br>季度；百万新元 | 用于观察可供居民部门消费和储蓄的总体收入规模；收入总额增加可能支持住房购买及租赁支出。 | SINGAPORE DEPARTMENT OF STATISTICS<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M016081>)<br>本次实际来源 | 最新可用：2026-Q2；94,423.4 百万新元；质量分：95/100 | 已达到数据门槛，未进入本次报告；不代表预测能力较差。原因为系统补充，不能当作模型逐项解释。<br>系统补充说明（非模型理由）；原文见下方折叠依据 | 是名义总额，不是人均、户均或家庭收入中位数；增长也可能来自物价或人口增加。序列未标注季节调整，优先比较同比。 |
| 三个月复利 SORA（月末值）<br>M700071:23 | 三个月复利新加坡隔夜平均利率的月末值，单位为年利率百分比。<br>月度；%/年 | 用于观察融资成本；基准利率上升可能随房贷重定价提高偿贷负担，并改变购房与租房选择，对租金的净影响不预设方向。 | MONETARY AUTHORITY OF SINGAPORE<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M700071>)<br>本次实际来源 | 最新可用：2026-08；1.1863 %/年；质量分：97.14/100 | 已选；满足本次数据门槛。模型选择理由见原文。<br>模型原始理由；原文见下方折叠依据 | 月末值不是月均值，也不是具体房贷报价；变化以基点表示，传导取决于利差及重定价安排。使用 MAS 日频路径时，按 SORA 计息日期而非公布日期归月，缺少月末完整性证据的月份暂不纳入；实际转换以该次来源元数据为准。 |
| 住房与过桥贷款余额<br>M701091:1.2.1 | 商业银行向居民提供的消费类住房及过桥贷款月末余额，单位为百万新加坡元。<br>月度；百万新元 | 用于观察住房融资活动及其规模；贷款余额扩张可能与融资购房需求同步变化，也可能反映房价上涨后的借款增加。 | MONETARY AUTHORITY OF SINGAPORE<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M701091>)<br>本次实际来源 | 最新可用：2026-08；256,563.5 百万新元；质量分：97.14/100 | 已达到数据门槛，未进入本次报告；不代表预测能力较差。原因为系统补充，不能当作模型逐项解释。<br>系统补充说明（非模型理由）；原文见下方折叠依据 | 是贷款存量，不是新增按揭、审批量或信贷可得性；还款也会改变余额。新报表口径自 2021 年 7 月开始，不能直接拼接旧口径；存在反向因果。 |
| 已竣工私人住宅存量<br>M400841:1 | 季度末取得临时入伙准证（TOP）或法定竣工证书（CSC）的私人住宅总套数，包括有地及非有地住宅、已入住及空置单位。<br>季度；套 | 用于观察当期可使用的住宅供给规模，并为人口及空置套数提供参照；新增竣工住宅可能缓解相对于需求的供给约束。 | URBAN REDEVELOPMENT AUTHORITY<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M400841>)<br>本次实际来源 | 最新可用：2026-Q2；424,581 套；质量分：95/100 | 已达到数据门槛，未进入本次报告；不代表预测能力较差。原因为系统补充，不能当作模型逐项解释。<br>系统补充说明（非模型理由）；原文见下方折叠依据 | 官方名称中的 available 指已竣工总存量，不是挂牌出售或出租量；不含 HDB 组屋、执行共管公寓（EC）及官方列明的其他排除项。1995—1996 年覆盖扩展影响长期可比性。 |
| 空置私人住宅套数<br>M400841:2 | 季度末已竣工但空置的私人住宅套数；覆盖有地及非有地住宅，范围与同表已竣工存量一致。<br>季度；套 | 用于观察住宅吸收情况；在总存量、区位和需求可比的条件下，空置增加可能对应较弱的价格或租金压力。 | URBAN REDEVELOPMENT AUTHORITY<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M400841>)<br>本次实际来源 | 最新可用：2026-Q2；26,961 套；质量分：95/100 | 已达到数据门槛，未进入本次报告；不代表预测能力较差。原因为系统补充，不能当作模型逐项解释。<br>系统补充说明（非模型理由）；原文见下方折叠依据 | 这是套数，不是空置率；必须结合同期已竣工存量，空置套数上升仍可能伴随空置率下降。不含 HDB 及 EC，与存量、供应储备同属住房供给指标组。 |
| 非有地私人住宅供应储备<br>M400391:2 | 季度末处于不同开发阶段的非有地私人住宅供应储备套数，包含规划及建设中的项目。<br>季度；套 | 用于观察未来潜在供给及市场预期；项目陆续竣工后可能增加购买和租赁市场的住宅供给。 | URBAN REDEVELOPMENT AUTHORITY<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M400391>)<br>本次实际来源 | 最新可用：2026-Q2；51,677 套；质量分：95/100 | 已达到数据门槛，未进入本次报告；不代表预测能力较差。原因为系统补充，不能当作模型逐项解释。<br>系统补充说明（非模型理由）；原文见下方折叠依据 | 不是已竣工住宅，也不是确定的竣工预测；交付时间、阶段和取消情况会变化。不含有地住宅、HDB 及 EC，与存量、空置同属住房供给指标组。 |
| 整体消费者价格指数（CPI）<br>M213751:1 | 基于官方家庭支出权重的整体消费者价格指数，以 2024 年为 100，按月公布。<br>月度；指数 | 用于观察生活成本和实际购买力；通胀可能影响家庭预算、持有成本及融资环境，对房价和租金的净作用不预设方向。 | SINGAPORE DEPARTMENT OF STATISTICS<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M213751>)<br>本次实际来源 | 最新可用：2026-08；103.334 指数；质量分：97.14/100 | 已达到数据门槛，未进入本次报告；不代表预测能力较差。原因为系统补充，不能当作模型逐项解释。<br>系统补充说明（非模型理由）；原文见下方折叠依据 | 不是住宅售价指数或建筑成本指数；包含住房相关分项，与租金可能存在指标重叠，不能视为独立的因果或已验证预测变量。 |
| 居民住户数<br>M810371:1 | 年度居民住户总数，居民住户按住户参考人为新加坡公民或永久居民界定；这是住户存量，不是人口数或当年新成立住户数。<br>年度；户 | 补充人口之外的居住单位数量：住户增加可能带来更多住房需求，具体取决于家庭构成、居住安排、租购选择和支付能力。 | SINGAPORE DEPARTMENT OF STATISTICS<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M810371>)<br>本次实际来源 | 最新可用：2025；1,487,100 户；质量分：100/100 | 已选；满足本次数据门槛。模型选择理由见原文。<br>模型原始理由；原文见下方折叠依据 | 人口普查、综合住户调查及六月综合劳动力调查的来源交替，调查估计存在抽样波动；元数据未给出每年一致的确切参考日，程序采用保守年末截点，不代表数据实际在年底测量。与人口指标共用需求组。 |
| 居民就业住户月度就业收入中位数<br>M810361:5 | 至少有一名就业成员、且参考人为公民或永久居民的住户，其月度就业收入中位数；单位为新加坡元，含雇主 CPF 及年度奖金的十二分之一，未计政府转移与税收。<br>年度；新元 | 补充典型就业住户的支付能力，区别于个人平均工资或全社会收入总额；可能有助于观察购房和租房负担的收入基础。 | SINGAPORE DEPARTMENT OF STATISTICS<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M810361>)<br>本次实际来源 | 最新可用：2025；12,027 新元；质量分：100/100 | 已达到数据门槛，未进入本次报告；不代表预测能力较差。原因为系统补充，不能当作模型逐项解释。<br>系统补充说明（非模型理由）；原文见下方折叠依据 | 是每户中位数，不是户内人均收入或个人工资；排除没有就业者的住户及住家家政工人的收入，含 CPF、奖金，非到手现金。与既有收入指标共用收入组，不代表已验证的预测能力。 |
| 年末就业总人数<br>M183111:7 | 年末就业总人数，单位为千人，覆盖居民和非居民雇员及自雇人士；包括外籍家政工人，不包括履行两年全职国民服役的人员。<br>年度；千人 | 补充失业率之外的就业规模；就业人数增加可能扩大收入基础，并支持与工作相关的住房需求。 | MINISTRY OF MANPOWER<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M183111>)<br>本次实际来源 | 最新可用：2025；4,117 千人；质量分：100/100 | 已达到数据门槛，未进入本次报告；不代表预测能力较差。原因为系统补充，不能当作模型逐项解释。<br>系统补充说明（非模型理由）；原文见下方折叠依据 | 不是居民就业人数、职位空缺或当年新增雇员；包含家政工人及其他不一定单独租住普通住宅的就业者。覆盖经 MOM 官方定义及总量对照核实，与居民失业率共用劳动力市场组。 |
| HDB 组屋存量（年中）<br>M400751:1.1 | 每年 6 月底的 HDB 组屋总套数，包括尚未私有化的 HUDC 住宅。<br>年度；套 | 补足私人住宅供给之外的公共住房规模；组屋供给可能影响居住选择，并与私人住房的购买及租赁需求相互作用。 | SINGAPORE DEPARTMENT OF STATISTICS<br>[SingStat Table Builder](<https://tablebuilder.singstat.gov.sg/table/TS/M400751>)<br>本次实际来源 | 最新可用：2026；1,177,601 套；质量分：100/100 | 已达到数据门槛，未进入本次报告；不代表预测能力较差。原因为系统补充，不能当作模型逐项解释。<br>系统补充说明（非模型理由）；原文见下方折叠依据 | 是存量，不是当年竣工、BTO 推出、转售成交或可出租套数；公共与私人住房在资格及政策上不同。参考日为 6 月 30 日，与私人住宅存量、空置和供应储备共用住房供给组。 |

## 原始依据

<details><summary>居民人口（M810001:2）</summary>

<p><strong>选择理由来源</strong></p><pre>系统补充说明（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>System exclusion: eligible candidate was not selected in the model&#x27;s submitted subset; the model did not provide an individual exclusion reason.</pre>

<p><strong>来源定义原文</strong></p><pre>Singapore citizens and permanent residents as at end-June; from 2003 excludes residents continuously overseas for at least 12 months at the reference date.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Singapore resident population, not number of households or homebuyers.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.
Used source-backed observation dates within the period for 48 observations; other observations use period-end cutoffs.</pre>

<p><strong>源文件注释</strong></p><pre>More information available on the following: Population Trends report (https://www.singstat.gov.sg/publication-resources/population-trends-2026); Information Paper on &#x27;Singapore Resident Population, 2003-2007&#x27; (https://www.singstat.gov.sg/publication-resources/singapore-resident-population-2003-2007);  How Singapore&#x27;s Population Estimates Are Compiled (https://www.singstat.gov.sg/publication-resources/understanding-singapore-population-estimates); Rate of Natural Increase (https://www.singstat.gov.sg/publication-resources/singapores-rate-of-natural-increase-for-population); Old-Age Support Ratio (https://www.singstat.gov.sg/infographics/old-age-support-ratio); Are the Old-Age Support Ratio Trends Similar Across Different Working-Age Group (https://www.singstat.gov.sg/publication-resources/are-the-old-age-support-ratio-trends-similar-across-different-working-age-groups).</pre>

<p><strong>源行注释</strong></p><pre>Data are as at end-June.  Data prior to 1990 are based on de facto concept (i.e. the person is present in the country at the reference period), while data from 1990 onwards are based on de jure concept (i.e. the person&#x27;s place of usual residence).  Data from 2003 onwards exclude residents who are overseas for a continuous period of 12 months or longer as at the reference period.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M810001_111a5f764bb0c97b.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>998bd3587b86d8d74e329bcc6a6a5225966482a689d42eec3a165e2f3452d6d2</pre>

</details>

<details><summary>非居民人口（M810001:5）</summary>

<p><strong>选择理由来源</strong></p><pre>系统补充说明（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>System exclusion: eligible candidate was not selected in the model&#x27;s submitted subset; the model did not provide an individual exclusion reason.</pre>

<p><strong>来源定义原文</strong></p><pre>Foreigners working, studying or living in Singapore without permanent residence, excluding tourists and short-term visitors, as at end-June.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Singapore non-resident population; housing needs include arrangements beyond private residential rentals.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.
Used source-backed observation dates within the period for 48 observations; other observations use period-end cutoffs.</pre>

<p><strong>源文件注释</strong></p><pre>More information available on the following: Population Trends report (https://www.singstat.gov.sg/publication-resources/population-trends-2026); Information Paper on &#x27;Singapore Resident Population, 2003-2007&#x27; (https://www.singstat.gov.sg/publication-resources/singapore-resident-population-2003-2007);  How Singapore&#x27;s Population Estimates Are Compiled (https://www.singstat.gov.sg/publication-resources/understanding-singapore-population-estimates); Rate of Natural Increase (https://www.singstat.gov.sg/publication-resources/singapores-rate-of-natural-increase-for-population); Old-Age Support Ratio (https://www.singstat.gov.sg/infographics/old-age-support-ratio); Are the Old-Age Support Ratio Trends Similar Across Different Working-Age Group (https://www.singstat.gov.sg/publication-resources/are-the-old-age-support-ratio-trends-similar-across-different-working-age-groups).</pre>

<p><strong>源行注释</strong></p><pre>Data are as at end-June.  Non-resident population comprises foreigners who were working, studying or living in Singapore but not granted permanent residence, excluding tourists and short-term visitors.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M810001_495ed32846bcfef1.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>553d1d43645babc2d30ac1bbe939abe2c2cbde0d36a4fb5088ec1f7171e4ca4d</pre>

</details>

<details><summary>实际国内生产总值（GDP）（M015661:1）</summary>

<p><strong>选择理由来源</strong></p><pre>模型原始理由</pre>

<p><strong>选择理由原文</strong></p><pre>Selected as an aggregate economic activity indicator. This series provides a quarterly view of real domestic output that may influence employment, incomes and housing confidence. The series is fully eligible and covers the full recent period, though it is not seasonally adjusted.</pre>

<p><strong>来源定义原文</strong></p><pre>Quarterly gross domestic product measured in chained 2015 Singapore dollars; a measure of real domestic economic activity.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Whole Singapore economy; million Singapore dollars at chained 2015 prices.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.</pre>

<p><strong>源文件注释</strong></p><pre>Disaggregated chain-linked data generally do not add up to the total.  Advance estimates for GDP in chained (2015) dollars are available at www.singstat.gov.sg/advgdp.  The advance GDP estimates are computed largely from data in the first two months of the quarter (e.g. 1st Quarter is based on Jan and Feb; 2nd Quarter is based on Apr and May).  They are intended as an early indication of the GDP growth in the quarter, and are subjected to revision when more comprehensive data become available.  For more information on national accounts methodologies, please visit Singstat website (https://www.singstat.gov.sg/find-data/explore-data-themes/economy-prices/national-accounts/related-information) to view and download related publications.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M015661_98fd049aa87c5bb9.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>138acbe058be5f2b1786287fa818e0efe86cebcd6877fbb79c9e832dc1093baf</pre>

</details>

<details><summary>居民失业率（经季节调整）（M182342:2）</summary>

<p><strong>选择理由来源</strong></p><pre>模型原始理由</pre>

<p><strong>选择理由原文</strong></p><pre>Selected as a labour-market condition measure for residents. A seasonally adjusted unemployment rate offers insight into workforce stability, which affects housing demand. The series is fully eligible with good coverage. It is excluded from the household income family to maintain theme diversity.</pre>

<p><strong>来源定义原文</strong></p><pre>Resident unemployment rate at quarter-end, seasonally adjusted; residents are citizens and permanent residents.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Resident labour force, not the entire resident population or non-resident workforce.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.</pre>

<p><strong>源文件注释</strong></p><pre>Total population comprises residents and non residents.  Residents refer to Singapore citizens and permanent residents.  Data for June 1995, 2000 and 2005 were obtained from the General Household Survey (June 1995 and 2005) and Population Census (June 2000) conducted by the Singapore Department of Statistics, Ministry of Trade and Industry.  The Labour Force Survey was not conducted in these periods.</pre>

<p><strong>源行注释</strong></p><pre>The seasonally adjusted figures are derived using X-12 ARIMA to remove the seasonal influences in the data series.  The seasonally adjusted unemployment figures are subject to annual revisions when the latest set of seasonal factors is updated, taking into account observations for the latest available year.  Residents refer to Singapore citizens and Singapore Permanent Residents.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M182342_48b7788b41cef5e4.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>84b73c77a3fa5e42e0f44d882ba2c465d8d7d8e426020c3f02578f7976904f27</pre>

</details>

<details><summary>就业居民平均月度就业总收入（含公积金、不含奖金）（M184101:1）</summary>

<p><strong>选择理由来源</strong></p><pre>模型原始理由</pre>

<p><strong>选择理由原文</strong></p><pre>Selected as a quarterly income measure for employed residents. Mean gross employment income reflects purchasing power and borrowing capacity for the resident workforce. While the mean can be skewed by high earners, it complements the household median income by offering a workforce-level perspective. The series is fully eligible.</pre>

<p><strong>来源定义原文</strong></p><pre>Mean gross monthly employment income of employed residents, including employer CPF contributions and excluding bonus; employees&#x27; amounts are before employee CPF and income tax deductions.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Employed citizens and permanent residents excluding full-time National Servicemen; Singapore dollars per employed person.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.</pre>

<p><strong>源文件注释</strong></p><pre>1. Residents refer to Singapore Citizens and Permanent Residents.  2. Gross monthly income refers to income earned from employment. For employees, it refers to the gross monthly wages or salaries before deduction of employee CPF contributions and personal income tax. It comprises basic wages, overtime pay, commissions, tips and other allowances. For self-employed persons, gross monthly income refers to the average monthly profits from their business, trade or profession (i.e. total receipts less business expenses incurred) before deduction of income tax.  3. Data are for all employed persons excluding full-time National Servicemen.  4. The change in mean gross monthly income (GMI) (change in income per worker) is a suitable statistic for comparison with the change in labour productivity (change in value-added per worker) as both are expressed on a &#x27;per worker&#x27; basis. When studying the change in mean gross monthly income of any quarter, it would be more meaningful to compare it with the same quarter of prior years, so as to limit seasonal variations that mask the underlying actual trend in income.  Also, as the mean GMI pertains to mean earnings, it can be skewed upwards by a small number of very high income earners.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M184101_fb465df65995a904.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>d8cbf8315336bd54bc69fc88739a236d44e8e9c0163deb5b497a83ea158917fe</pre>

</details>

<details><summary>个人可支配收入总额（名义）（M016081:1）</summary>

<p><strong>选择理由来源</strong></p><pre>系统补充说明（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>System exclusion: eligible candidate was not selected in the model&#x27;s submitted subset; the model did not provide an individual exclusion reason.</pre>

<p><strong>来源定义原文</strong></p><pre>Quarterly aggregate personal disposable income at current prices.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Singapore aggregate nominal personal disposable income; million Singapore dollars, not median household income.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M016081_3de81f4c4307fd66.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>927b20623c10c369782544e906b5387db81cbbef6b8e412ef62d0496f0804535</pre>

</details>

<details><summary>三个月复利 SORA（月末值）（M700071:23）</summary>

<p><strong>选择理由来源</strong></p><pre>模型原始理由</pre>

<p><strong>选择理由原文</strong></p><pre>Selected as a financing cost indicator. The SORA benchmark provides monthly observations of the Singapore dollar interest rate environment, which directly affects mortgage affordability. While not an individual mortgage offer, it is a key reference for floating-rate loans. The series is highly eligible with extensive history. It is excluded from the inflation family because its primary role is financing cost rather than price-level tracking.</pre>

<p><strong>来源定义原文</strong></p><pre>Three-month compounded Singapore Overnight Rate Average (SORA), observed at month-end and expressed as an annual percentage rate.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Singapore-dollar benchmark interest rate; not an individual mortgage offer.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.</pre>

<p><strong>源文件注释</strong></p><pre>Interest rates at the end-period are as at the end of month.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M700071_5ec2ab86786f7bd2.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>844467d877f0fc311402be16f7fb1e606b894eb34185683c8a20f9039d4c70a2</pre>

</details>

<details><summary>住房与过桥贷款余额（M701091:1.2.1）</summary>

<p><strong>选择理由来源</strong></p><pre>系统补充说明（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>System exclusion: eligible candidate was not selected in the model&#x27;s submitted subset; the model did not provide an individual exclusion reason.</pre>

<p><strong>来源定义原文</strong></p><pre>Commercial-bank consumer housing and bridging loans to residents outstanding at month-end.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Commercial-bank lending stock to residents; million Singapore dollars, not new monthly mortgage approvals.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.</pre>

<p><strong>源文件注释</strong></p><pre>The industry categories are refined according to the Singapore Standard Industrial Classification adopted by the Singapore Department of Statistics.  Data have been revised from July 2021 following changes to the MAS Notices 610 and 1003.  The previous series have been discontinued and can be found on the MAS Website under the Money and Banking page of the Statistics section.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M701091_11d6417c6fe41133.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>b8bc0b0d9f1fa8d7fe20072630210799fc9d32057a3ea71765b2032259933e8d</pre>

</details>

<details><summary>已竣工私人住宅存量（M400841:1）</summary>

<p><strong>选择理由来源</strong></p><pre>系统补充说明（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>System exclusion: eligible candidate was not selected in the model&#x27;s submitted subset; the model did not provide an individual exclusion reason.</pre>

<p><strong>来源定义原文</strong></p><pre>Completed private residential units at quarter-end with a Temporary Occupation Permit or Certificate of Statutory Completion; this is the housing stock labelled available by URA.</pre>

<p><strong>来源覆盖范围</strong></p><pre>All landed and non-landed private residential units; excludes hostels, HDB flats, tenement houses, parsonages and Executive Condominiums.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.</pre>

<p><strong>源文件注释</strong></p><pre>Data cover all completed private residential units, i.e. private residential units issued with a Temporary Occupation Permit or a Certificate of Statutory Completion.  Data exclude hostels, Housing and Development Board flats, tenement houses, parsonages and Executive Condominiums.  With effect from 1st Quarter 1995, the coverage was expanded to include another 44,891 private residential units built before 1974 (comprising 7,206 detached, 10,006 semi-detached, 16,900 terrace and 10,779 apartments).  With effect from 2nd Quarter 1996, the coverage was further expanded to include 12,489 apartment units comprising HUDC units which have not been privatised, apartments above shops and privatised apartments previously under the Government Housing Schemes for employees.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M400841_9cbe20a8bfdb6540.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>e6363fdf9c307229226c70f6210a01bed31099f9e2cca622a1f7faa1a8741cbd</pre>

</details>

<details><summary>空置私人住宅套数（M400841:2）</summary>

<p><strong>选择理由来源</strong></p><pre>系统补充说明（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>System exclusion: eligible candidate was not selected in the model&#x27;s submitted subset; the model did not provide an individual exclusion reason.</pre>

<p><strong>来源定义原文</strong></p><pre>Number of vacant completed private residential units at quarter-end, not the vacancy rate.</pre>

<p><strong>来源覆盖范围</strong></p><pre>All landed and non-landed private residential units; same exclusions and coverage as the completed stock in table M400841 row 1.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.</pre>

<p><strong>源文件注释</strong></p><pre>Data cover all completed private residential units, i.e. private residential units issued with a Temporary Occupation Permit or a Certificate of Statutory Completion.  Data exclude hostels, Housing and Development Board flats, tenement houses, parsonages and Executive Condominiums.  With effect from 1st Quarter 1995, the coverage was expanded to include another 44,891 private residential units built before 1974 (comprising 7,206 detached, 10,006 semi-detached, 16,900 terrace and 10,779 apartments).  With effect from 2nd Quarter 1996, the coverage was further expanded to include 12,489 apartment units comprising HUDC units which have not been privatised, apartments above shops and privatised apartments previously under the Government Housing Schemes for employees.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M400841_de38dc09e41862f3.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>0104a610532cf4ac51fba4e4ee1eceed2f7960241c4bbf9e818ed72ec5ac8d54</pre>

</details>

<details><summary>非有地私人住宅供应储备（M400391:2）</summary>

<p><strong>选择理由来源</strong></p><pre>系统补充说明（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>System exclusion: eligible candidate was not selected in the model&#x27;s submitted subset; the model did not provide an individual exclusion reason.</pre>

<p><strong>来源定义原文</strong></p><pre>Total non-landed private residential units in the pipeline at quarter-end across development statuses.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Non-landed private residential pipeline; excludes hostels, HDB flats, tenement houses, parsonages and Executive Condominiums.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.</pre>

<p><strong>源文件注释</strong></p><pre>Data exclude hostels, HDB flats, tenement houses, parsonages and Executive Condominiums.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M400391_fb25f7621ca819ff.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>f088bab517f48eb2861a305667fb52c24ceca6eaed2d855d6bcf6d0f8fa56a01</pre>

</details>

<details><summary>整体消费者价格指数（CPI）（M213751:1）</summary>

<p><strong>选择理由来源</strong></p><pre>系统补充说明（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>System exclusion: eligible candidate was not selected in the model&#x27;s submitted subset; the model did not provide an individual exclusion reason.</pre>

<p><strong>来源定义原文</strong></p><pre>All-items Consumer Price Index, 2024 = 100, based on the official household expenditure weighting pattern.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Singapore consumer prices; index, not residential property sale prices.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.</pre>

<p><strong>源文件注释</strong></p><pre>The weighting pattern of the Consumer Price Index (CPI) was derived from the expenditure values collected from the Household Expenditure Survey (HES) 2023 and updated to 2024 values by taking into account price changes between 2023 and 2024.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M213751_62f62cd25bf5df72.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>28aec21bd4c894fbc1df63dd140903d8342e8e064bd3ad8e9997aa02a58c9669</pre>

</details>

<details><summary>居民住户数（M810371:1）</summary>

<p><strong>选择理由来源</strong></p><pre>模型原始理由</pre>

<p><strong>选择理由原文</strong></p><pre>Selected as a structural demand indicator measuring the number of resident households. Household counts serve as a proxy for potential housing demand and are distinct from population counts or new household formation. The series is fully eligible. It is excluded from the population demand family only in the sense of overlapping themes, but as a distinct identifier it captures a different demographic dimension. The annual frequency limits short-term timing precision.</pre>

<p><strong>来源定义原文</strong></p><pre>Annual number of resident households; household counts are distinct from population and are not the number of newly formed households.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Resident households. Source estimates combine Census of Population, General Household Survey and Comprehensive June Labour Force Survey; sampling variability and source changes apply.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.</pre>

<p><strong>源文件注释</strong></p><pre>Data for 1980, 1990, 2000, 2010 and 2020 are based on the Census of Population while data for 1995, 2005, 2015 and 2025 are based on the General Household Survey. Data for all other years are based on the Comprehensive June Labour Force Survey. Survey estimates are subject to sampling variability.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M810371_8461ccdf2c645031.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>3b1c98d7f8191a8c4ab000444fe34c827a556ab416c85e2623154d79c458595d</pre>

</details>

<details><summary>居民就业住户月度就业收入中位数（M810361:5）</summary>

<p><strong>选择理由来源</strong></p><pre>系统补充说明（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>System exclusion: eligible candidate was not selected in the model&#x27;s submitted subset; the model did not provide an individual exclusion reason.</pre>

<p><strong>来源定义原文</strong></p><pre>Median nominal monthly household employment income among resident employed households, including employer CPF contributions and one-twelfth of annual bonus, before Government transfers and taxes.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Households whose reference person is a citizen or permanent resident and with at least one employed member. Income sums employment and business income of employed household members, excluding live-in domestic workers.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.</pre>

<p><strong>源文件注释</strong></p><pre>Data refer to resident employed households. A resident employed household refers to a household where the household reference person is a resident (i.e. Singapore citizen or permanent resident), and with at least one employed person. Household employment income refers to the sum of income received by employed members of the household from employment and business, excluding the income of live-in domestic workers. Monthly household employment income includes employer Central Provident Fund (CPF) contributions and one-twelfth of annual bonus. Data on household employment income refers to household employment income before accounting for Government transfers and taxes, unless stated otherwise.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M810361_ace929ea782b332d.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>64b079f81758a381e25fe6bc001bf4ee5057f00f4d86c542b8fbbfa85313b231</pre>

</details>

<details><summary>年末就业总人数（M183111:7）</summary>

<p><strong>选择理由来源</strong></p><pre>系统补充说明（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>System exclusion: eligible candidate was not selected in the model&#x27;s submitted subset; the model did not provide an individual exclusion reason.</pre>

<p><strong>来源定义原文</strong></p><pre>Total persons in employment as at year-end, expressed in thousands; includes migrant domestic workers and excludes persons serving two-year full-time national service.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Resident and non-resident employees plus self-employed persons. MOM administrative-record coverage excludes two-year full-time national servicemen; the current MOM summary identifies the matching total as including migrant domestic workers. SingStat row footnote confirms administrative records plus Labour Force Survey estimates for the self-employed.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.</pre>

<p><strong>源行注释</strong></p><pre>Data are compiled primarily from administrative records, wtih the self-employed component estimated from the Labour Force Survey.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M183111_78ebddbf3477131c.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>091816d24a8931e0b39195330d1c3b00fca60057cff5755fadcdbd6ec53487cd</pre>

</details>

<details><summary>HDB 组屋存量（年中）（M400751:1.1）</summary>

<p><strong>选择理由来源</strong></p><pre>系统补充说明（非模型理由）</pre>

<p><strong>选择理由原文</strong></p><pre>System exclusion: eligible candidate was not selected in the model&#x27;s submitted subset; the model did not provide an individual exclusion reason.</pre>

<p><strong>来源定义原文</strong></p><pre>Total HDB flats as at end-June of each year, including non-privatised Housing and Urban Development Corporation flats.</pre>

<p><strong>来源覆盖范围</strong></p><pre>Public-housing dwelling stock; not annual completions, BTO launches, resale transactions or flats available for rent.</pre>

<p><strong>数据门槛原因原文</strong></p><pre>未提供</pre>

<p><strong>数据警告原文</strong></p><pre>Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.
Used source-backed observation dates within the period for 27 observations; other observations use period-end cutoffs.</pre>

<p><strong>源文件注释</strong></p><pre>Data as at end June of each year.</pre>

<p><strong>源行注释</strong></p><pre>Includes non-privatised Housing and Urban Development Corporation flats.</pre>

<p><strong>原始文件</strong></p><pre>raw/tabledata_M400751_c10997a05cec390f.json</pre>

<p><strong>原始文件 SHA-256</strong></p><pre>ae44af016d20a58cd79503fe3d95d1e18e17f10218aae45b76afe211b8c363bf</pre>

</details>

中文说明来源：housing\_agent/data/indicator\_notes.json

说明内容 SHA-256：`d2247a803329a79cfe178b9cbcfe9b2579d71078178d950268f3bef4afd993b2`。完整说明随 JSON 保存。

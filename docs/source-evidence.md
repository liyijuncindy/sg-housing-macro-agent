# Verified source evidence

The initial candidate catalogue was checked against live official SingStat responses on **1 October 2026, Singapore time**. Exact-row downloads and metadata were captured at approximately **00:31 SGT** (30 September 16:31 UTC). These are observed source facts, not invented fixtures. A normal application run records its own URLs, retrieval times, raw response files and SHA-256 hashes.

The current catalogue contains **16 candidates**. Four additions were verified against live official responses at **19:23–19:26 SGT on 1 October 2026**. The [candidate expansion record](new-indicators.md) distinguishes the six series examined, four admitted and two deferred, with their definitions, reference dates, actual quality results and saved source evidence. Admission establishes reviewed scope and data usability, not predictive performance.

## Official interfaces and exact identifiers

The [SingStat API directory](https://tablebuilder.singstat.gov.sg/view-api/find-apis) supplies public statistics. The implementation uses three endpoints under `https://tablebuilder.singstat.gov.sg/api/table/`:

- `resourceid?keyword=...&searchOption=all` returns matching table identifiers and titles.
- `metadata/{table_id}` returns one metadata object in `Data.records`, including frequency, source institution, notes, coverage and row identifiers.
- `tabledata/{table_id}?seriesNoORrowNo={row_id}&limit=5000` returns an exact series with period and value strings.

Candidates cover multiple economic channels. Related rows are alternatives or complementary measurements; the registry does not prescribe a fixed set of five indicators.

| Official table | Verified series IDs | Interpretation |
|---|---|---|
| [M810001](https://tablebuilder.singstat.gov.sg/table/TS/M810001) | `2`, `5` | Resident and non-resident population |
| [M015661](https://tablebuilder.singstat.gov.sg/table/TS/M015661) | `1` | GDP in chained 2015 dollars |
| [M182342](https://tablebuilder.singstat.gov.sg/table/TS/M182342) | `2` | Seasonally adjusted resident unemployment rate |
| [M184101](https://tablebuilder.singstat.gov.sg/table/TS/M184101) | `1` | Mean monthly employment income of employed residents |
| [M016081](https://tablebuilder.singstat.gov.sg/table/TS/M016081) | `1` | Nominal personal disposable income |
| [M700071](https://tablebuilder.singstat.gov.sg/table/TS/M700071) | `23` | Three-month compounded SORA |
| [M701091](https://tablebuilder.singstat.gov.sg/table/TS/M701091) | `1.2.1` | Housing and bridging loan balances |
| [M400841](https://tablebuilder.singstat.gov.sg/table/TS/M400841) | `1`, `2` | Completed private housing stock and vacant units |
| [M400391](https://tablebuilder.singstat.gov.sg/table/TS/M400391) | `2` | Non-landed private housing pipeline |
| [M213751](https://tablebuilder.singstat.gov.sg/table/TS/M213751) | `1` | All-items CPI, 2024 base |
| [M810371](https://tablebuilder.singstat.gov.sg/table/TS/M810371) | `1` | Resident households, annual stock |
| [M810361](https://tablebuilder.singstat.gov.sg/table/TS/M810361) | `5` | Median monthly household employment income among resident employed households |
| [M183111](https://tablebuilder.singstat.gov.sg/table/TS/M183111) | `7` | Total persons employed at year-end, in thousands |
| [M400751](https://tablebuilder.singstat.gov.sg/table/TS/M400751) | `1.1` | Total HDB flats at end-June, including non-privatised HUDC flats |

## Definitions that affect calculations

**Population reference date.** Both selected [population metadata](https://tablebuilder.singstat.gov.sg/api/table/metadata/M810001) rows explicitly refer to end-June. Annual observations therefore use June 30, not December 31. The downloaded table contained 2026 observations and showed `dataLastUpdated: 25/09/2026`. This is the current table's update date; it does not establish each observation's first publication date. The source also records changes in population coverage. Early historical gaps must not be treated as contiguous annual observations.

**Interest-rate timing.** [M700071 metadata](https://tablebuilder.singstat.gov.sg/api/table/metadata/M700071) states that end-period rates are observed at month-end. SORA is expressed as an annual percentage rate. Its change is calculated in basis points. It is a benchmark, not a mortgage offer or monthly average.

**Income and seasonality.** [Employment-income metadata](https://tablebuilder.singstat.gov.sg/api/table/metadata/M184101) includes employer CPF and excludes bonus, describes mean-income skew, and recommends comparing the same quarter across years. The chosen GDP, employment-income and disposable-income tables are not labelled seasonally adjusted; year-on-year comparisons avoid presenting their raw quarter-on-quarter change as an underlying trend.

**Housing quantities.** URA's completed housing stock includes occupied and vacant units; “available” does not mean actively marketed. The vacant row measures units, not a vacancy rate. Both need matching-period context. Pipeline row `2` covers non-landed housing across development stages, not imminent completions. These private-sector tables exclude HDB flats and Executive Condominiums, among other stated exclusions.

**New household, employment and public-housing measures.** Household income is a median per employed household, not per household member or per worker, and includes employer CPF and one-twelfth of annual bonus. Total employment includes migrant domestic workers and excludes two-year full-time national servicemen; these coverage details were checked against additional official MOM evidence rather than inferred from SingStat's shorter row note. Employment uses December 31 and HDB stock uses June 30. The household-count table combines census and survey sources without establishing one exact reference day for every year, so its year-end cutoff is conservative, not a claimed measurement date. See [new-indicators.md](new-indicators.md) for the source-backed distinctions and limits.

## Data limits and selection

An unfiltered CPI request was observed to stop at exactly **5,000 observation cells**, partway through a row. Exact-row requests avoid this current truncation; the client must reject or paginate any longer series. Real quarterly period labels use `YYYY nQ`, monthly labels use `YYYY Mon`, and values are strings.

The metadata supplies observation frequency, but not a guaranteed release schedule, individual publication timestamps or historical vintages. Consequently, this version filters the latest captured vintage by observation reference date and explicitly does not reconstruct what was known historically. Quality scores establish data usability, not causality or predictive performance.

Completed private stock, vacancies, pipeline and HDB stock all belong to the broad **housing supply** selection family. Household counts share the population-demand family, median household income shares the income family, and employment levels share the labour-market family. These complementary measurements share first-pass diversity slots. This limits redundant selection without imposing a fixed number of families or preventing complementary measures when capacity permits.

## SingStat-first routing and request evidence

The default `auto` policy first attempts **every candidate through SingStat**. Each primary request permits at most three attempts under the workflow's default configuration: the initial request and two retries for temporary transport failures or recognised current-maintenance responses. Permanent HTTP, schema and definition errors stop that request without blind retries. Failure of a discovery query or one candidate does not stop other independent candidates.

After all first-pass candidates have been attempted, candidates still failing with a retryable error receive a second SingStat pass, with the same per-request retry bound. Only after that pass does `auto` try the three reviewed MOM/MAS backups below for their still-failed matching candidates. A successful SingStat download is not replaced merely because a backup exists. The `singstat` policy performs the same primary retries, independent-candidate continuation and second pass, but never uses a backup. The other **13 candidates have no implemented independent backup**; persistent failures are reported as unavailable, with no silent reuse of an older snapshot.

`source_routes.json` records each candidate's primary, recheck and any fallback stages, their outcomes and the source actually used. `retrievals.json` records request attempts, timestamps, status and allowed response headers. When an error response body is available, its first **16 KiB** are saved with byte count, truncation flag and SHA-256 hash. This is a bounded prefix, not necessarily the full response. These raw evidence files are included in run integrity checks.

The [earlier maintenance diagnosis](evidence/singstat-maintenance-diagnosis.json) records Table Builder requests returning a standalone maintenance page at **16:50:23–24 SGT on 1 October 2026**, while the main SingStat homepage returned HTTP 200. A later saved run recorded another affected request at **17:19:06 SGT**. These observations establish what those requests received at those times; they do not establish a persistent site-wide outage or justify abandoning other endpoints. The current recogniser requires the known standalone, present-tense visible maintenance page. A historical or scheduled notice quoted in a normal page is not treated as current service status, and a recognised maintenance response is subject to bounded retry rather than a global stop flag.

## Independent official downloads

The `auto` workflow has three reviewed publisher backups that do not depend on Table Builder. They are used only after the matching candidate's SingStat attempts have failed under the routing policy above:

| Catalogue identity | Direct source | Mapping and checks |
|---|---|---|
| `M182342:2` | [MOM unemployment CSV](https://stats.mom.gov.sg/iMAS_Tables1/CSV/mrsd_11_Resident_unemployment_rate_n_number.csv) | Keep `quarter_annual=quarter`, `residential_status=resident`, and `seasonally_adjusted_unemployment_rate`. Do not include annual averages or substitute extra precision from another file. |
| `M184101:1` | [MOM quarterly mean-income XLSX](https://stats.mom.gov.sg/iMAS_Tables1/Time-Series-Table/mrsd_72_Mean_GMI_Emp_Res_Quarterly.xlsx) | Verify the official title, Dollars unit, quarterly columns, source attribution and definition notes. Preserve the employer/platform-operator CPF scope, bonus exclusion and preliminary markers. It is a mean per employed resident, not median income or aggregate disposable income. |
| `M700071:23` | [MAS public domestic-interest-rate export](https://eservices.mas.gov.sg/statistics/dir/DomesticInterestRates.aspx) | Submit the public download form for three-month compounded SORA. Sample the final **SORA Value Date** in each verified closed month. Publication-date grouping is incorrect; no monthly average or further compounding is used. |

The independent routes retain original CSV/XLSX bytes, form-response bytes, retrieval timestamps, SHA-256 hashes and exact row/cell locators. Adapter-generated metadata is clearly marked as local interpretation of the official file. A changed label, unit, workbook layout or unsupported response fails explicitly. HTTP partial-content responses are not accepted as complete histories.

MOM data overlapped the original SingStat snapshot exactly across 138 unemployment quarters and 21 income quarters. MAS value-date month-end sampling matched all 251 available overlapping months. These are observed cross-source checks of the captured vintages, not a promise that future revisions or definitions will remain identical. Current workflow results and precise validation evidence are recorded in [validation.md](validation.md).

The MAS CSV's publication/index date is retained separately. It does not establish when back-calculated historical compounded rates were first available. Months whose final daily record lacks a publication/index date crossing month-end are conservatively omitted. Missing terminal values remain missing; an earlier valid quote is not substituted.

The main SingStat GDP page supplies current/previous observations but has not been connected as a replacement historical series. The other 13 candidates still require SingStat in a fresh run. Earlier direct-source and saved-source runs retain their original routes, values and timestamps; current planned routing does not rewrite those historical records.

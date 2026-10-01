# Verified source evidence

The initial candidate catalogue was checked against live official SingStat responses on **1 October 2026, Singapore time**. Exact-row downloads and metadata were captured at approximately **00:31 SGT** (30 September 16:31 UTC). These are observed source facts, not invented fixtures. A normal application run records its own URLs, retrieval times, raw response files and SHA-256 hashes.

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

## Definitions that affect calculations

**Population reference date.** Both selected [population metadata](https://tablebuilder.singstat.gov.sg/api/table/metadata/M810001) rows explicitly refer to end-June. Annual observations therefore use June 30, not December 31. The downloaded table contained 2026 observations and showed `dataLastUpdated: 25/09/2026`. This is the current table's update date; it does not establish each observation's first publication date. The source also records changes in population coverage. Early historical gaps must not be treated as contiguous annual observations.

**Interest-rate timing.** [M700071 metadata](https://tablebuilder.singstat.gov.sg/api/table/metadata/M700071) states that end-period rates are observed at month-end. SORA is expressed as an annual percentage rate. Its change is calculated in basis points. It is a benchmark, not a mortgage offer or monthly average.

**Income and seasonality.** [Employment-income metadata](https://tablebuilder.singstat.gov.sg/api/table/metadata/M184101) includes employer CPF and excludes bonus, describes mean-income skew, and recommends comparing the same quarter across years. The chosen GDP, employment-income and disposable-income tables are not labelled seasonally adjusted; year-on-year comparisons avoid presenting their raw quarter-on-quarter change as an underlying trend.

**Housing quantities.** URA's completed housing stock includes occupied and vacant units; “available” does not mean actively marketed. The vacant row measures units, not a vacancy rate. Both need matching-period context. Pipeline row `2` covers non-landed housing across development stages, not imminent completions. These private-sector tables exclude HDB flats and Executive Condominiums, among other stated exclusions.

## Data limits and selection

An unfiltered CPI request was observed to stop at exactly **5,000 observation cells**, partway through a row. Exact-row requests avoid this current truncation; the client must reject or paginate any longer series. Real quarterly period labels use `YYYY nQ`, monthly labels use `YYYY Mon`, and values are strings.

The metadata supplies observation frequency, but not a guaranteed release schedule, individual publication timestamps or historical vintages. Consequently, this version filters the latest captured vintage by observation reference date and explicitly does not reconstruct what was known historically. Quality scores establish data usability, not causality or predictive performance.

Completed stock, vacancies and pipeline all belong to the broad **housing supply** selection family. They describe different aspects of supply but should share a first-pass diversity slot. This limits redundant selection without imposing a fixed number of families or preventing complementary supply measures when capacity permits.

## Independent official downloads

The default workflow uses three reviewed publisher routes that do not depend on Table Builder:

| Catalogue identity | Direct source | Mapping and checks |
|---|---|---|
| `M182342:2` | [MOM unemployment CSV](https://stats.mom.gov.sg/iMAS_Tables1/CSV/mrsd_11_Resident_unemployment_rate_n_number.csv) | Keep `quarter_annual=quarter`, `residential_status=resident`, and `seasonally_adjusted_unemployment_rate`. Do not include annual averages or substitute extra precision from another file. |
| `M184101:1` | [MOM quarterly mean-income XLSX](https://stats.mom.gov.sg/iMAS_Tables1/Time-Series-Table/mrsd_72_Mean_GMI_Emp_Res_Quarterly.xlsx) | Verify the official title, Dollars unit, quarterly columns, source attribution and definition notes. Preserve the employer/platform-operator CPF scope, bonus exclusion and preliminary markers. It is a mean per employed resident, not median income or aggregate disposable income. |
| `M700071:23` | [MAS public domestic-interest-rate export](https://eservices.mas.gov.sg/statistics/dir/DomesticInterestRates.aspx) | Submit the public download form for three-month compounded SORA. Sample the final **SORA Value Date** in each verified closed month. Publication-date grouping is incorrect; no monthly average or further compounding is used. |

The independent routes retain original CSV/XLSX bytes, form-response bytes, retrieval timestamps, SHA-256 hashes and exact row/cell locators. Adapter-generated metadata is clearly marked as local interpretation of the official file. A changed label, unit, workbook layout or unsupported response fails explicitly. HTTP partial-content responses are not accepted as complete histories.

MOM data overlapped the original SingStat snapshot exactly across 138 unemployment quarters and 21 income quarters. MAS value-date month-end sampling matched all 251 available overlapping months. These are observed cross-source checks of the captured vintages, not a promise that future revisions or definitions will remain identical. Current workflow results and precise validation evidence are recorded in [validation.md](validation.md).

The MAS CSV's publication/index date is retained separately. It does not establish when back-calculated historical compounded rates were first available. Months whose final daily record lacks a publication/index date crossing month-end are conservatively omitted. Missing terminal values remain missing; an earlier valid quote is not substituted.

The main SingStat GDP page supplies current/previous observations but has not been connected as a replacement historical series. The other nine candidates still require SingStat in a fresh run; unavailable candidates are reported rather than silently filled from an older snapshot.

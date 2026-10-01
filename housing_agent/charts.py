"""Export report charts with explicit periods and auditable input values."""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path


def require_chart_dependencies():
    try:
        import matplotlib
    except ImportError:
        raise RuntimeError("Report v2 needs chart dependencies: install the project with the charts extra, e.g. pip install -e '.[llm,charts]'.") from None
    return matplotlib


def _date(period):
    if "-Q" in period:
        year, quarter = period.split("-Q")
        return date(int(year), (int(quarter)-1)*3+1, 1)
    if len(period) == 7:
        return date.fromisoformat(period+"-01")
    return date(int(period), 1, 1)


def write_charts(output: Path, research: dict, evaluations: list[dict], selection: dict) -> list[dict]:
    matplotlib = require_chart_dependencies()
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    output = Path(output)
    chart_dir = output / "charts"
    chart_dir.mkdir(parents=True, exist_ok=False)
    charts, inputs = [], []
    colors = ["#176b91", "#df8b27", "#39845d"]
    style = {"font.family":"DejaVu Sans", "font.size":10, "axes.spines.top":False,
             "axes.spines.right":False, "axes.titleweight":"bold", "svg.fonttype":"none",
             "svg.hashsalt":"sg-housing-report-v2", "figure.facecolor":"white"}

    def save(filename, title, caption, series, ylabel):
        if not any(points for _,points in series):
            return
        with plt.rc_context(style):
            fig, ax = plt.subplots(figsize=(11, 4.8), layout="constrained")
            for n,(label,points) in enumerate(series):
                points = [p for p in points if p.get("value") is not None]
                if not points:
                    continue
                ax.plot([_date(p["period"]) for p in points], [p["value"] for p in points],
                        label=label, color=colors[n%len(colors)], linewidth=1.9)
            ax.set(title=title, ylabel=ylabel, xlabel="Observation period")
            ax.grid(axis="y", color="#dce4eb", linewidth=.7)
            ax.xaxis.set_major_locator(mdates.YearLocator(2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
            if len(series)>1:
                ax.legend(loc="best", frameon=False)
            fig.savefig(chart_dir/(filename+".svg"), metadata={"Date":None})
            fig.savefig(chart_dir/(filename+".png"), dpi=150)
            plt.close(fig)
        charts.append({"path":"charts/"+filename+".svg", "png_path":"charts/"+filename+".png", "title":title,"caption":caption})
        inputs.append({"chart":filename,"series":series,"ylabel":ylabel})

    outcomes = [item for item in research["outcomes"] if item["status"]=="available"]
    # All three official indices have the same published base, but describe
    # different transactions; retain the base and explain coverage explicitly.
    series = []
    for item in outcomes:
        points=[{"period":p["period"],"value":p["index_value"]} for p in item["quarterly_changes"] if p["period"] >= "2015-Q1"]
        series.append((item["name"],points))
    save("housing_indices", "Housing price and rent indices", "Official index base: 2009 Q1 = 100. Different market coverage; index levels are not currency prices. Display starts after the major methodology changes.", series, "Index (2009 Q1 = 100)")
    save("housing_quarterly_growth", "Quarterly housing price and rent changes", "Exact previous-quarter percentage changes; no seasonally adjusted growth is implied. The statistical window uses both comparison endpoints from 2015 Q1 onward.",
         [(i["name"],[p for p in i["quarterly_changes"] if p["period"] >= "2015-Q2"]) for i in outcomes], "Quarter-on-quarter change (%)")
    vacancy=research["derived_private_vacancy_rate"]
    save("private_vacancy_rate", "Completed private residential vacancy rate", "Calculated from matching-quarter vacant units divided by completed private stock. Vacant units are not necessarily listed for sale or rent.",
         [("Derived vacancy rate", [p for p in vacancy["observations"] if p["period"] >= "2015-Q1"])], "Vacant / completed units (%)")
    by_id={e["id"]:e for e in evaluations}
    for key in selection["selected_ids"]:
        item=by_id[key]
        points=[p for p in item["observations"] if p["value"] is not None and p["period"][:4]>="2015"]
        save("indicator_"+key.replace(":","_").replace(".","_"), item["metadata"]["name"],
             "Source observations at their original frequency. Annual data are not interpolated into quarters or months.",
             [(item["metadata"]["name"],points)], item["metadata"]["unit"])
    (chart_dir/"chart_inputs.json").write_text(json.dumps(inputs,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return charts

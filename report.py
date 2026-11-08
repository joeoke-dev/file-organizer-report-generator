"""Turn the cleaned sales data into charts and a self-contained HTML report."""

import base64
import html
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw charts to files, no screen needed
import matplotlib.pyplot as plt

BAR_COLOR = "#3b6ea5"


def compute_metrics(df):
    """Headline numbers for the report."""
    by_month = df.groupby(df["date"].dt.to_period("M"))["total"].sum()
    by_category = df.groupby("product_category")["total"].sum().sort_values(ascending=False)
    by_region = df.groupby("region")["total"].sum().sort_values(ascending=False)
    return {
        "orders": len(df),
        "units": int(df["quantity"].sum()),
        "revenue": float(df["total"].sum()),
        "avg_order": float(df["total"].mean()),
        "date_from": df["date"].min().date().isoformat(),
        "date_to": df["date"].max().date().isoformat(),
        "top_category": (by_category.index[0], float(by_category.iloc[0])),
        "top_region": (by_region.index[0], float(by_region.iloc[0])),
        "best_month": (str(by_month.idxmax()), float(by_month.max())),
        "by_month": by_month,
        "by_category": by_category,
        "by_region": by_region,
    }


def _save_bar_chart(labels, values, title, path, horizontal=False):
    fig, ax = plt.subplots(figsize=(7, 4))
    if horizontal:
        ax.barh(labels[::-1], values[::-1], color=BAR_COLOR)
        ax.set_xlabel("Revenue")
    else:
        ax.bar(labels, values, color=BAR_COLOR)
        ax.set_ylabel("Revenue")
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.ticklabel_format(axis="x" if horizontal else "y", style="plain")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def make_charts(metrics, folder):
    """Save three PNG charts and return their paths."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    month_labels = [p.strftime("%b %Y") for p in metrics["by_month"].index]
    paths = {
        "monthly": folder / "chart_monthly_revenue.png",
        "category": folder / "chart_revenue_by_category.png",
        "region": folder / "chart_revenue_by_region.png",
    }
    _save_bar_chart(month_labels, metrics["by_month"].values, "Revenue by month", paths["monthly"])
    _save_bar_chart(list(metrics["by_category"].index), metrics["by_category"].values,
                    "Revenue by product category", paths["category"], horizontal=True)
    _save_bar_chart(list(metrics["by_region"].index), metrics["by_region"].values,
                    "Revenue by region", paths["region"], horizontal=True)
    return paths


def _embed(path):
    data = base64.b64encode(Path(path).read_bytes()).decode()
    return f"data:image/png;base64,{data}"


def _card(label, value):
    return f'<div class="card"><div class="label">{html.escape(label)}</div><div class="value">{html.escape(value)}</div></div>'


def render_html(metrics, summary, charts):
    cards = "".join([
        _card("Revenue", f"{metrics['revenue']:,.0f}"),
        _card("Orders", f"{metrics['orders']:,}"),
        _card("Average order", f"{metrics['avg_order']:,.0f}"),
        _card("Units sold", f"{metrics['units']:,}"),
    ])
    highlights = [
        f"Top category: <b>{html.escape(metrics['top_category'][0])}</b> ({metrics['top_category'][1]:,.0f} revenue)",
        f"Top region: <b>{html.escape(metrics['top_region'][0])}</b> ({metrics['top_region'][1]:,.0f} revenue)",
        f"Best month: <b>{html.escape(metrics['best_month'][0])}</b> ({metrics['best_month'][1]:,.0f} revenue)",
    ]
    highlight_items = "".join(f"<li>{h}</li>" for h in highlights)

    cleaning_rows = "".join(
        f"<tr><td>{html.escape(k.replace('_', ' ').capitalize())}</td><td class='num'>{v:,}</td></tr>"
        for k, v in summary.items()
    )
    images = "".join(
        f'<img src="{_embed(path)}" alt="{name} chart">' for name, path in charts.items()
    )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Sales Report</title>
<style>
 :root {{ color-scheme: light; }}
 body {{ margin: 0; background: #ffffff; color: #222222; font-family: Arial, sans-serif; }}
 .page {{ max-width: 900px; margin: 0 auto; padding: 30px 24px; background: #ffffff; color: #222222; }}
 h1, h2 {{ color: #222222; }}
 h1 {{ margin-bottom: 4px; }} .sub {{ color: #666666; margin-top: 0; }}
 .cards {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 20px 0; }}
 .card {{ flex: 1; min-width: 150px; background: #f3f6fa; border-radius: 8px; padding: 14px; }}
 .label {{ color: #666; font-size: 13px; }} .value {{ font-size: 26px; font-weight: bold; margin-top: 4px; }}
 img {{ max-width: 100%; margin: 10px 0; }}
 table {{ border-collapse: collapse; width: 100%; max-width: 520px; }}
 td {{ border-bottom: 1px solid #dddddd; padding: 6px 8px; color: #222222; }} td.num {{ text-align: right; }}
</style></head><body><div class="page">
<h1>Sales Report</h1>
<p class="sub">{metrics['date_from']} to {metrics['date_to']} &middot; generated {datetime.now():%d %b %Y}</p>
<div class="cards">{cards}</div>
<h2>Highlights</h2><ul>{highlight_items}</ul>
<h2>Charts</h2>{images}
<h2>Data cleaning summary</h2>
<p>What the pipeline fixed or removed before analysis:</p>
<table>{cleaning_rows}</table>
</div></body></html>"""


def build_report(df, summary, output_folder):
    """Create the charts and the HTML report. Returns the report path."""
    output_folder = Path(output_folder)
    metrics = compute_metrics(df)
    charts = make_charts(metrics, output_folder)
    report_path = output_folder / "report.html"
    report_path.write_text(render_html(metrics, summary, charts), encoding="utf-8")
    return report_path

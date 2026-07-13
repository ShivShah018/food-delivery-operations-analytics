"""
Generate EDA visualizations and export as PNG screenshots.
"""

import sys
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import CLEAN_DIR, PROC_DIR, SCREENSHOTS, LOG_FILE, LOG_FORMAT, LOG_DATE_FORMAT

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger("viz")

sns.set_style("whitegrid")
plt.rcParams.update({"figure.figsize": (12, 6), "font.size": 12})


def _load(name):
    path = CLEAN_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}")
    return pd.read_csv(path)


def plot_monthly_revenue(delivered):
    monthly = delivered.set_index("order_date").resample("ME")["total_amount"].sum()
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.fill_between(monthly.index, monthly.values, alpha=0.3, color="#3498db")
    ax.plot(monthly.index, monthly.values, color="#2980b9", linewidth=2, marker="o", markersize=4)
    ax.set_title("Monthly Revenue Trend", fontsize=16, fontweight="bold")
    ax.set_ylabel("Revenue (INR)")
    fig.tight_layout()
    fig.savefig(SCREENSHOTS / "monthly_revenue_trend.png", dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("Saved monthly_revenue_trend.png")


def plot_customer_segmentation():
    cf = pd.read_csv(PROC_DIR / "customer_features.csv")
    seg_counts = cf["customer_segment"].value_counts()
    colors = {"Platinum": "#2c3e50", "Gold": "#f39c12", "Silver": "#3498db",
              "At Risk": "#e67e22", "Churned": "#e74c3c"}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    ax1.pie(seg_counts.values, labels=seg_counts.index, autopct="%1.1f%%",
            colors=[colors.get(s, "#95a5a6") for s in seg_counts.index], startangle=90)
    ax1.set_title("Customer Segments", fontsize=14, fontweight="bold")
    seg_rev = cf.groupby("customer_segment")["monetary"].sum()
    bars = ax2.bar(seg_rev.index, seg_rev.values / 1e6,
                   color=[colors.get(s, "#95a5a6") for s in seg_rev.index])
    ax2.set_title("Revenue by Segment", fontsize=14, fontweight="bold")
    ax2.set_ylabel("Revenue (Millions INR)")
    for bar, val in zip(bars, seg_rev.values):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                 f"INR {val / 1e6:.1f}M", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(SCREENSHOTS / "customer_segmentation.png", dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("Saved customer_segmentation.png")


def plot_top_cuisines(delivered, restaurants):
    merged = delivered.merge(restaurants[["restaurant_id", "cuisine_type"]], on="restaurant_id")
    cuisines = merged.groupby("cuisine_type").agg(revenue=("total_amount", "sum")).sort_values("revenue", ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(range(len(cuisines)), cuisines["revenue"].values / 1e6, color="#2ecc71")
    ax.set_yticks(range(len(cuisines)))
    ax.set_yticklabels(cuisines.index)
    ax.set_xlabel("Revenue (Millions INR)")
    ax.set_title("Top 10 Cuisines by Revenue", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    for bar, val in zip(bars, cuisines["revenue"].values):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                f"INR {val / 1e6:.1f}M", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(SCREENSHOTS / "top_cuisines.png", dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("Saved top_cuisines.png")


def plot_delivery_performance(delivery_logs):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].hist(delivery_logs["travel_time_mins"], bins=35, color="#3498db", edgecolor="white")
    axes[0].axvline(delivery_logs["travel_time_mins"].median(), color="red",
                    linestyle="--", label=f"Median: {delivery_logs['travel_time_mins'].median():.0f} min")
    axes[0].set_title("Delivery Travel Time", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Minutes")
    axes[0].set_ylabel("Deliveries")
    axes[0].legend()
    traffic_rate = delivery_logs.groupby("traffic_condition")["is_on_time"].mean() * 100
    t_colors = {"Low": "#2ecc71", "Moderate": "#3498db", "High": "#f39c12", "Gridlock": "#e74c3c"}
    axes[1].bar(traffic_rate.index, traffic_rate.values,
                color=[t_colors.get(t, "#95a5a6") for t in traffic_rate.index])
    axes[1].set_title("On-Time Rate by Traffic", fontsize=13, fontweight="bold")
    axes[1].set_ylabel("On-Time Rate (%)")
    for i, v in enumerate(traffic_rate.values):
        axes[1].text(i, v + 1, f"{v:.1f}%", ha="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(SCREENSHOTS / "delivery_performance.png", dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("Saved delivery_performance.png")


def plot_time_patterns(delivered):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    hourly = delivered.groupby("order_hour").size()
    axes[0].bar(hourly.index, hourly.values, color="#9b59b6", width=0.8)
    axes[0].set_title("Orders by Hour", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Hour")
    axes[0].set_ylabel("Orders")
    axes[0].set_xticks(range(0, 24, 2))
    wd = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekly = delivered["weekday"].value_counts().reindex(wd)
    axes[1].bar(weekly.index, weekly.values, color=["#3498db"] * 5 + ["#e74c3c"] * 2, width=0.6)
    axes[1].set_title("Orders by Day of Week", fontsize=13, fontweight="bold")
    axes[1].tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(SCREENSHOTS / "time_patterns.png", dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("Saved time_patterns.png")


def plot_city_revenue(delivered):
    city_rev = delivered.groupby("restaurant_city")["total_amount"].sum().sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(city_rev.index, city_rev.values / 1e6, color="#e74c3c", width=0.6)
    ax.set_title("Top 10 Cities by Revenue", fontsize=14, fontweight="bold")
    ax.set_ylabel("Revenue (Millions INR)")
    ax.tick_params(axis="x", rotation=30)
    for bar, val in zip(bars, city_rev.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f"INR {val / 1e6:.1f}M", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(SCREENSHOTS / "city_revenue.png", dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("Saved city_revenue.png")


def plot_kpi_summary(delivered, orders, delivery_logs):
    fig, axes = plt.subplots(2, 3, figsize=(14, 5))
    fig.suptitle("SwiftDash — Key Performance Indicators", fontsize=16, fontweight="bold", y=1.02)
    kpis = [
        ("Total Revenue", f"INR {delivered['total_amount'].sum():,.0f}", "#2c3e50"),
        ("Total Orders", f"{delivered['order_id'].nunique():,}", "#3498db"),
        ("Avg Order Value", f"INR {delivered['total_amount'].mean():,.0f}", "#2ecc71"),
        ("On-Time Delivery", f"{delivery_logs['is_on_time'].mean() * 100:.1f}%", "#27ae60"),
        ("Cancellation Rate", f"{(orders['order_status'] == 'Cancelled').mean() * 100:.1f}%", "#e74c3c"),
        ("Avg Rating", f"{orders['customer_rating'].mean():.1f}/5", "#f39c12"),
    ]
    for ax, (title, value, color) in zip(axes.flat, kpis):
        ax.set_facecolor("#f8f9fa")
        ax.text(0.5, 0.6, value, ha="center", va="center", fontsize=22, fontweight="bold", color=color)
        ax.text(0.5, 0.2, title, ha="center", va="center", fontsize=12, color="#7f8c8d")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(SCREENSHOTS / "kpi_summary.png", dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("Saved kpi_summary.png")


def main():
    logger.info("=" * 50)
    logger.info("START: Visualization export")
    logger.info("=" * 50)

    try:
        orders = _load("orders_clean.csv")
        restaurants = _load("restaurants_clean.csv")
        delivery_logs = _load("delivery_logs_clean.csv")

        orders["order_date"] = pd.to_datetime(orders["order_date"])
        delivered = orders[orders["order_status"].isin(["Delivered", "Refunded"])].copy()

        plot_monthly_revenue(delivered)
        plot_customer_segmentation()
        plot_top_cuisines(delivered, restaurants)
        plot_delivery_performance(delivery_logs)
        plot_time_patterns(delivered)
        plot_city_revenue(delivered)
        plot_kpi_summary(delivered, orders, delivery_logs)

        logger.info("All visualizations exported to %s", SCREENSHOTS)
        logger.info("=" * 50)
        logger.info("Visualization export complete.")
        logger.info("=" * 50)
    except Exception as exc:
        logger.critical("Visualization export failed: %s", exc, exc_info=True)
        raise


if __name__ == "__main__":
    main()

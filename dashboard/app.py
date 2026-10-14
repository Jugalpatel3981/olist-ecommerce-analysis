"""Olist E-Commerce interactive dashboard.

Run locally:
    streamlit run dashboard/app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"
BLUE, ORANGE, LIGHT_BLUE = "#2a78d6", "#eb6834", "#9ec5f4"
INK_2, MUTED, GRID = "#52514e", "#898781", "#e1e0d9"
DIVERGING = ["#1c5cab", "#6da7ec", "#c3c2b7", "#f0a3a2", "#e66767", "#b82d2d"]
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

st.set_page_config(page_title="Olist E-Commerce Analytics", page_icon="📦", layout="wide")


@st.cache_data
def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    orders = pd.read_parquet(DATA / "orders.parquet")
    items = pd.read_parquet(DATA / "items.parquet")
    orders["order_month"] = pd.to_datetime(orders["order_month"])
    orders["is_late"] = orders["is_late"].astype("boolean")  # NULL for undelivered orders
    return orders, items


def style(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=40, b=10),
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=INK_2),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="white", font_size=12), legend_title_text="",
    )
    fig.update_xaxes(showgrid=False, linecolor=MUTED)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


orders, items = load()

# ---------------------------------------------------------------- filters
st.title("📦 Olist E-Commerce Analytics")
st.caption("~98K orders from a Brazilian marketplace · Jan 2017 – Aug 2018 · values in R$")

months = sorted(orders["order_month"].dt.date.unique())
f1, f2, f3 = st.columns([2, 2, 2])
start, end = f1.select_slider("Period", options=months, value=(months[0], months[-1]),
                              format_func=lambda d: d.strftime("%b %Y"))
states = f2.multiselect("Customer state", sorted(orders["state"].unique()), placeholder="All states")
categories = f3.multiselect("Product category", sorted(items["category"].unique()),
                            placeholder="All categories")

mask = orders["order_month"].dt.date.between(start, end)
if states:
    mask &= orders["state"].isin(states)
if categories:
    mask &= orders["order_id"].isin(items.loc[items["category"].isin(categories), "order_id"])
o = orders[mask]
it = items[items["order_id"].isin(o["order_id"])]
if categories:
    it = it[it["category"].isin(categories)]
delivered = o[o["order_status"] == "delivered"]

if o.empty:
    st.warning("No orders match these filters.")
    st.stop()

# ---------------------------------------------------------------- KPIs
k = st.columns(6)
k[0].metric("Revenue", f"R${o['payment_value'].sum() / 1e6:,.2f}M")
k[1].metric("Orders", f"{len(o):,}")
k[2].metric("Avg order value", f"R${o['payment_value'].mean():,.0f}")
k[3].metric("Avg review", f"{o['review_score'].mean():.2f} ★")
k[4].metric("Late deliveries", f"{delivered['is_late'].mean():.1%}")
repeat = o.groupby("customer_unique_id").size()
k[5].metric("Repeat customers", f"{(repeat > 1).mean():.1%}")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Sales", "🚚 Delivery & satisfaction", "👥 Customers", "🏪 Sellers & categories"])

# ---------------------------------------------------------------- sales
with tab1:
    monthly = o.groupby("order_month").agg(revenue=("payment_value", "sum"),
                                           orders=("order_id", "count")).reset_index()
    fig = px.area(monthly, x="order_month", y="revenue", markers=True,
                  title="Monthly revenue", labels={"order_month": "", "revenue": "Revenue (R$)"})
    fig.update_traces(line_color=BLUE, fillcolor="rgba(42,120,214,0.08)",
                      hovertemplate="%{x|%b %Y}<br>R$%{y:,.0f}<extra></extra>")
    st.plotly_chart(style(fig), use_container_width=True)

    c1, c2 = st.columns(2)
    by_state = (o.groupby("state")["payment_value"].sum().nlargest(12).sort_values().reset_index())
    fig = px.bar(by_state, x="payment_value", y="state", orientation="h", title="Revenue by state (top 12)",
                 labels={"payment_value": "Revenue (R$)", "state": ""})
    fig.update_traces(marker_color=BLUE, hovertemplate="%{y}: R$%{x:,.0f}<extra></extra>")
    c1.plotly_chart(style(fig, 420), use_container_width=True)

    pay = o.groupby("main_payment_type")["payment_value"].sum().sort_values().reset_index()
    fig = px.bar(pay, x="payment_value", y="main_payment_type", orientation="h", title="Revenue by payment method",
                 labels={"payment_value": "Revenue (R$)", "main_payment_type": ""})
    fig.update_traces(marker_color=BLUE, hovertemplate="%{y}: R$%{x:,.0f}<extra></extra>")
    c2.plotly_chart(style(fig, 420), use_container_width=True)

# ---------------------------------------------------------------- delivery
with tab2:
    d = delivered.dropna(subset=["review_score", "days_vs_estimate"])
    bins = [-1e9, -10, -1, 0, 5, 10, 1e9]
    labels = ["10+ days early", "1-9 days early", "On time", "1-5 days late", "6-10 days late", "10+ days late"]
    d = d.assign(bucket=pd.cut(d["days_vs_estimate"], bins=bins, labels=labels))
    dvr = d.groupby("bucket", observed=False).agg(avg_review=("review_score", "mean"),
                                                  orders=("order_id", "count")).reset_index()
    fig = px.bar(dvr, x="bucket", y="avg_review", color="bucket", color_discrete_sequence=DIVERGING,
                 title="Average review vs. delivery timing", text=dvr["avg_review"].map("{:.2f}★".format),
                 custom_data=["orders"], labels={"bucket": "", "avg_review": "Avg review"})
    fig.update_traces(textposition="outside", showlegend=False,
                      hovertemplate="%{x}<br>%{y:.2f}★ across %{customdata[0]:,} orders<extra></extra>")
    fig.update_yaxes(range=[0, 5])
    st.plotly_chart(style(fig), use_container_width=True)

    is_late = d["is_late"].astype(bool)  # d only holds delivered orders, so no NULLs
    late, on_time = d[is_late], d[~is_late]
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg review — late", f"{late['review_score'].mean():.2f} ★")
    c2.metric("Avg review — on time", f"{on_time['review_score'].mean():.2f} ★")
    c3.metric("1-star share — late vs on time",
              f"{(late['review_score'] == 1).mean():.0%} vs {(on_time['review_score'] == 1).mean():.0%}")

    st_late = (delivered.groupby("state").agg(late_pct=("is_late", "mean"), orders=("order_id", "count"),
                                              avg_days=("delivery_days", "mean"))
               .query("orders >= 100").sort_values("late_pct").reset_index())
    fig = px.bar(st_late, x="late_pct", y="state", orientation="h", title="Late-delivery rate by state (100+ orders)",
                 custom_data=["orders", "avg_days"], labels={"late_pct": "", "state": ""})
    fig.update_traces(marker_color=ORANGE, hovertemplate="%{y}: %{x:.1%} late<br>%{customdata[0]:,} orders · "
                                                         "%{customdata[1]:.1f} days avg<extra></extra>")
    fig.update_xaxes(tickformat=".0%")
    st.plotly_chart(style(fig, 600), use_container_width=True)

# ---------------------------------------------------------------- customers
with tab3:
    ref = o["purchased_at"].max()
    rfm = o.groupby("customer_unique_id").agg(last=("purchased_at", "max"), frequency=("order_id", "count"),
                                              monetary=("payment_value", "sum"))
    rfm["recency"] = (ref - rfm["last"]).dt.days
    rfm["r"] = 6 - pd.qcut(rfm["recency"].rank(method="first"), 5, labels=False) - 1
    rfm["m"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=False) + 1

    def segment(row) -> str:
        if row.frequency >= 2 and row.r >= 4:
            return "Champions"
        if row.frequency >= 2:
            return "Loyal - slipping"
        if row.r >= 4:
            return "New big spenders" if row.m >= 4 else "Recent customers"
        if row.r == 3:
            return "Needs attention"
        return "At risk - high value" if row.m >= 4 else "Lost / hibernating"

    rfm["segment"] = rfm.apply(segment, axis=1)
    seg = rfm.groupby("segment").agg(customers=("monetary", "size"), revenue=("monetary", "sum"),
                                     avg_spend=("monetary", "mean"))
    seg["% of customers"] = seg["customers"] / seg["customers"].sum() * 100
    seg["% of revenue"] = seg["revenue"] / seg["revenue"].sum() * 100
    seg = seg.sort_values("% of revenue").reset_index()
    long = seg.melt(id_vars="segment", value_vars=["% of customers", "% of revenue"])
    fig = px.bar(long, x="value", y="segment", color="variable", barmode="group", orientation="h",
                 title="RFM segments: share of customers vs share of revenue",
                 color_discrete_map={"% of customers": LIGHT_BLUE, "% of revenue": BLUE},
                 labels={"value": "%", "segment": ""})
    fig.update_traces(hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
    fig.update_layout(legend=dict(orientation="h", y=1.08, x=1, xanchor="right"))
    st.plotly_chart(style(fig, 420), use_container_width=True)
    st.dataframe(seg[["segment", "customers", "avg_spend", "% of customers", "% of revenue"]]
                 .sort_values("% of revenue", ascending=False).round(1),
                 hide_index=True, use_container_width=True)

    first = o.groupby("customer_unique_id")["order_month"].min().rename("cohort")
    act = o[["customer_unique_id", "order_month"]].drop_duplicates().join(first, on="customer_unique_id")
    act["n"] = ((act["order_month"].dt.year - act["cohort"].dt.year) * 12
                + act["order_month"].dt.month - act["cohort"].dt.month)
    size = act[act["n"] == 0].groupby("cohort").size()
    ret = (act[act["n"].between(1, 12)].groupby(["cohort", "n"]).size().unstack(fill_value=0)
           .div(size, axis=0) * 100)
    ret.index = ret.index.strftime("%Y-%m")
    fig = px.imshow(ret, color_continuous_scale=SEQ_BLUE, aspect="auto", text_auto=".1f",
                    title="Cohort retention: % of customers buying again N months later",
                    labels=dict(x="Months since first purchase", y="Cohort", color="%"))
    st.plotly_chart(style(fig, 560), use_container_width=True)

# ---------------------------------------------------------------- sellers & categories
with tab4:
    cat = (it.groupby("category").agg(revenue=("price", "sum"), items=("price", "size"),
                                      freight=("freight_value", "sum")).reset_index())
    rev_by_order = o.set_index("order_id")["review_score"]
    cat_review = (it.drop_duplicates(["order_id", "category"]).assign(review=lambda x: x["order_id"].map(rev_by_order))
                  .groupby("category")["review"].mean())
    cat["avg_review"] = cat["category"].map(cat_review)
    top = cat.nlargest(15, "revenue").sort_values("revenue")
    fig = px.bar(top, x="revenue", y="category", orientation="h", title="Top 15 categories by revenue",
                 custom_data=["items", "avg_review"], labels={"revenue": "Revenue (R$)", "category": ""})
    fig.update_traces(marker_color=BLUE, hovertemplate="%{y}<br>R$%{x:,.0f} · %{customdata[0]:,} items · "
                                                       "%{customdata[1]:.2f}★<extra></extra>")
    st.plotly_chart(style(fig, 520), use_container_width=True)

    sellers = it.groupby("seller_id")["price"].sum().sort_values(ascending=False)
    cum = (sellers.cumsum() / sellers.sum() * 100).reset_index(drop=True)
    pct = (cum.index + 1) / len(cum) * 100
    top10 = cum.iloc[max(int(len(cum) * 0.1) - 1, 0)]
    fig = go.Figure()
    fig.add_scatter(x=pct, y=cum, mode="lines", line=dict(color=BLUE, width=2), name="Sellers",
                    hovertemplate="Top %{x:.1f}% of sellers → %{y:.1f}% of revenue<extra></extra>")
    fig.add_scatter(x=[0, 100], y=[0, 100], mode="lines", line=dict(color=MUTED, dash="dash", width=1),
                    hoverinfo="skip", showlegend=False)
    fig.update_layout(title=f"Seller concentration — top 10% of {len(sellers):,} sellers = {top10:.0f}% of revenue",
                      xaxis_title="% of sellers (ranked)", yaxis_title="Cumulative % of revenue", showlegend=False)
    st.plotly_chart(style(fig, 420), use_container_width=True)

st.caption("Data: Olist Brazilian E-Commerce Public Dataset (CC BY-NC-SA 4.0). Built with DuckDB, pandas, Plotly & Streamlit.")

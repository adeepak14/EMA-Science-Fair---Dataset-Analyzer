#EMA Science fair project - Abhinav Deepak
import io
import time
import warnings

import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

COUNT = "Number of rows"
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def to_dates(series):
    """Turn a column into dates; anything that isn't a date becomes missing."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pd.to_datetime(series, errors="coerce")


def find_date_columns(df, threshold=0.8):
    """Columns where at least 80% of the filled values read as dates."""
    found = df.select_dtypes("datetime").columns.tolist()
    for col in df.select_dtypes(exclude=["number", "datetime"]).columns:
        values = df[col].dropna().astype(str)
        if not values.empty and to_dates(values).notna().mean() >= threshold:
            found.append(col)
    return found

st.set_page_config(page_title="Universal CSV Data Analytics Engine - Abhinav D", page_icon="📊", layout="wide")
st.title("Universal CSV Data Analytics Engine")
st.header("For the EMA 2026 Science Fair - By: Abhinav Deepak")
st.divider()
st.write("What the app does is it takes a dataset YOU input, and returns a few graphs, helping you analyze it.")
st.caption("Data is NOT saved by the website - upload anything you need")
st.divider()
st.header("1. Upload and Health Check")
uploaded = st.file_uploader("File opener", type = "csv")
if uploaded is None:
    st.info("Please upload a file")
    st.stop()
def load_csv(raw_bytes):
    try:
        return pd.read_csv(io.BytesIO(raw_bytes), encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(io.BytesIO(raw_bytes), encoding="latin-1")
try:
    df = load_csv(uploaded.getvalue())
except (pd.errors.EmptyDataError, pd.errors.ParserError) as err:
    st.error(f"An Error Occurred, please reupload: {err}")
    st.stop()
if df.empty:
    st.error("This file has headers but no data rows. Please upload another file.")
    st.stop()

card1, card2, card3, card4 = st.columns(4)
card1.metric("Rows", f"{len(df):,}")
card2.metric("Columns", df.shape[1])
card3.metric("Missing values", f"{int(df.isna().sum().sum()):,}")
card4.metric("Duplicate rows", f"{int(df.duplicated().sum()):,}")

health = pd.DataFrame({
    "Type": df.dtypes.astype(str),
    "Missing": df.isna().sum(),
    "Missing %": (df.isna().mean() * 100).round(1),
    "Unique values": df.nunique(),
})
st.dataframe(health)

mostly_empty = health[health["Missing %"] > 50].index.tolist()
if mostly_empty:
    st.warning(f"These columns are more than 50% empty: {', '.join(mostly_empty)}")
#st.write(df.shape)
st.dataframe(df.head(20))
correctDataset = st.checkbox("Is this your dataset?")
if not correctDataset:
    st.info("Please check the box to continue, or upload a different file above.")

if correctDataset == True:
    st.header("2. Data Cleaning")
    numeric_cols = df.select_dtypes("number").columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    st.caption("Missing numbers were replaced with 0. Missing text was left blank.")
    numeric = df.select_dtypes("number").columns.tolist()
    text = df.select_dtypes(exclude=["number", "datetime"]).columns.tolist()
    dates = df.select_dtypes("datetime").columns.tolist()
    plot_df = df.sample(5000, random_state=1) if len(df) > 5000 else df
    date_cols = find_date_columns(df)

    st.header("3. Statistical Insights")
    if numeric:
        chosen = st.multiselect("Numeric columns", numeric, default=numeric)
        if chosen:
            stats = df[chosen].describe().T
            stats["median"] = df[chosen].median()
            st.dataframe(stats.round(3))
    else:
        st.info("No numeric columns found.")

    if text:
        cat = st.selectbox("Category counts for", text)
        st.dataframe(df[cat].value_counts().head(20))

    st.header("4. Interactive Visuals")
   #graph checklist
    st.subheader("Choose your graphs: Tick the box to generate")
    st.subheader("Choose based on your dataset")
    show_heatmap = st.checkbox("Correlation heatmap", value=True)
    show_hist = st.checkbox("Histogram")
    show_scatterplot = st.checkbox("Scatter Plot")
    show_scattermatrix = st.checkbox("Scatter Matrix")
    show_bar = st.checkbox("Bar Graph")
    show_share = st.checkbox("Share of total (percent)")
    #graph generation
    if show_heatmap:
        heat_type = st.radio("Heatmap type", ["Correlation matrix", "Activity calendar"],
                             horizontal=True, key="heat_type")

        if heat_type == "Correlation matrix":
            if len(numeric) >= 2:
                corr = df[numeric].corr()
                fig = px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1,
                                color_continuous_scale="RdBu_r")
                st.plotly_chart(fig)
            else:
                st.info("A heatmap needs at least 2 numeric columns")

        else:
            if date_cols:
                c1, c2, c3 = st.columns(3)
                dcol = c1.selectbox("Date column", date_cols, key="cal_date")
                val = c2.selectbox("Measure", [COUNT] + numeric, key="cal_val")
                dates_only = df.assign(_date=to_dates(df[dcol]).dt.normalize()).dropna(subset=["_date"])
                years = sorted(dates_only["_date"].dt.year.unique())
                if not years:
                    st.info("No valid dates found in that column.")
                else:
                    year = c3.selectbox("Year", years, index=len(years) - 1, key="cal_year")
                    one_year = dates_only[dates_only["_date"].dt.year == year]

                    # total per day, with 0 for days that have no rows
                    if val == COUNT:
                        per_day = one_year.groupby("_date").size()
                    else:
                        per_day = one_year.groupby("_date")[val].sum()
                    days = pd.date_range(f"{year}-01-01", f"{year}-12-31")
                    per_day = per_day.reindex(days, fill_value=0)

                    # rows = weekday, columns = the Monday that starts each week
                    cal = pd.DataFrame({
                        "value": per_day.values,
                        "weekday": days.dayofweek,
                        "week": days - pd.to_timedelta(days.dayofweek, unit="D"),
                    })
                    grid = cal.pivot(index="weekday", columns="week", values="value")
                    grid.index = WEEKDAYS
                    grid.columns = [w.strftime("%b %d") for w in grid.columns]

                    fig = px.imshow(grid, color_continuous_scale="Greens", aspect="auto",
                                    labels={"x": "Week starting", "y": "", "color": val},
                                    title=f"{val} per day in {year}")
                    fig.update_traces(xgap=2, ygap=2)
                    st.plotly_chart(fig)
                    st.caption("Darker squares mean more on that day. Blank squares are outside the year.")
            else:
                st.info("The activity calendar needs a date column.")
    
    if show_hist:
        if numeric:
            hist_col = st.selectbox("Histogram of", numeric)
            fig = px.histogram(df, x=hist_col)
            st.plotly_chart(fig)    
        else:
            st.info("A Histogram needs at least 1 numeric column")
            
    if show_scatterplot:
        if len(numeric) >= 2:
            x = st.selectbox("Scatter X", numeric, index=0)
            y = st.selectbox("Scatter Y", numeric, index=1)
            fig = px.scatter(plot_df, x=x, y=y)
            st.plotly_chart(fig)
        else:
            st.info("A scatter plot needs at least 2 numeric columns.")
    
    if show_scattermatrix:
        if len(numeric) >= 3:
            matrix_cols = st.multiselect("Matrix columns", numeric, default=numeric[:4])
            if matrix_cols:
                fig = px.scatter_matrix(plot_df, dimensions=matrix_cols)
                st.plotly_chart(fig)
        else:
            st.info("A scatter matrix needs at least 3 numeric columns.")
    
    if show_bar:
        bar_mode = st.radio(
            "Bar chart type",
            ["Count per category", "Numeric value per category", "Numeric value in ranges"],
            horizontal=True,
        )

        if bar_mode == "Count per category":
            if text:
                cat_col = st.selectbox("Category (x-axis)", text)
                counts = df[cat_col].value_counts().head(20).reset_index()
                fig = px.bar(counts, x=cat_col, y="count",
                             title=f"Most common values in {cat_col}")
                st.plotly_chart(fig)
            else:
                st.info("This chart needs at least 1 text column.")

        elif bar_mode == "Numeric value per category":
            if text and numeric:
                cat_col = st.selectbox("Category (x-axis)", text)
                val_col = st.selectbox("Value (y-axis)", numeric)
                how = st.selectbox("Combine values using", ["sum", "mean", "median", "max", "min"])
                grouped = (df.groupby(cat_col)[val_col].agg(how)
                           .sort_values(ascending=False).head(20).reset_index())
                fig = px.bar(grouped, x=cat_col, y=val_col,
                             title=f"{how.title()} of {val_col} by {cat_col}")
                st.plotly_chart(fig)
            else:
                st.info("This chart needs at least 1 text column and 1 numeric column.")

        else:
            if numeric:
                num_col = st.selectbox("Numeric column", numeric)
                bins = st.slider("Number of bars", 5, 50, 10)
                ranges = pd.cut(df[num_col], bins=bins).value_counts(sort=False).reset_index()
                ranges[num_col] = ranges[num_col].astype(str)
                fig = px.bar(ranges, x=num_col, y="count",
                             title=f"How many rows fall in each range of {num_col}")
                st.plotly_chart(fig)
            else:
                st.info("This chart needs at least 1 numeric column.")
        if show_share:
            if text:
                c1, c2, c3 = st.columns(3)
                cat = c1.selectbox("Group by", text, key="share_cat")
                val = c2.selectbox("Measure", [COUNT] + numeric, key="share_val")
                style = c3.radio("Style", ["Bar", "Donut"], horizontal=True, key="share_style")

                if val == COUNT:
                    share = df.groupby(cat).size().reset_index(name=COUNT)
                else:
                    share = df.groupby(cat)[val].sum().reset_index()
                total = share[val].sum()
    
                if total > 0:
                    share["Percent"] = (share[val] / total * 100).round(1)
                    share = share.sort_values("Percent", ascending=False).head(15)
                    if style == "Donut":
                        fig = px.pie(share, names=cat, values=val, hole=0.5,
                                     title=f"Share of {val} by {cat}")
                    else:
                        share = share.sort_values("Percent")
                        fig = px.bar(share, x="Percent", y=cat, orientation="h",
                                     text=share["Percent"].astype(str) + "%",
                                     title=f"Share of {val} by {cat}",
                                     labels={"Percent": "Percent of total"})
                    st.plotly_chart(fig)
                    st.dataframe(share.sort_values("Percent", ascending=False))
                else:
                    st.info("The total is 0, so percentages can't be calculated.")
            else:
                st.info("This chart needs at least 1 text column.")
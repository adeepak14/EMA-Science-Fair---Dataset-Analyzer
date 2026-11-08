#EMA Science fair project - Abhinav Deepak
import io
import time
import warnings

import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

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
    show_timeseries = st.checkbox("Time Series")
    #graph generation
    if show_heatmap:
        if len(numeric) >= 2:
            corr = df[numeric].corr()
            fig = px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1,
                        color_continuous_scale="RdBu_r")
            st.plotly_chart(fig)
        else:
            st.info("A heatmap needs at least 2 numeric columns")
    
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
        if text:
            cat_col = st.selectbox("Category", text)
            counts = df[cat_col].value_counts().head(20).reset_index()
            fig = px.bar(counts, x=cat_col, y="count", title=f"Most common values in {cat_col}")
            st.plotly_chart(fig)
        else:
            st.info("A bar chart needs at least 1 text column.")
    if show_timeseries:
        if dates and numeric:
            date_col = st.selectbox("Date column", dates)
            value_col = st.selectbox("Value over time", numeric)
            line_df = df.sort_values(date_col)
            fig = px.line(line_df, date_col, value_col)
            st.plotly_chart(fig)
        else:
            st.info("A Time Series needs a date and at least 1 numeric column")


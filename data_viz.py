from matplotlib.figure import Figure
import pandas as pd
from typing import List, Optional

def fig_histogram(df: pd.DataFrame, col: str, bins: int = 30) -> Figure:
    fig = Figure(figsize=(6,4))
    ax = fig.subplots()
    series = df[col].dropna()
    if series.empty:
        ax.text(0.5, 0.5, 'No numeric data', ha='center')
        return fig
    ax.hist(series, bins=bins)
    ax.set_title(f'Histogram: {col}')
    ax.set_xlabel(col)
    ax.set_ylabel('count')
    fig.tight_layout()
    return fig

def fig_top_categories(df: pd.DataFrame, col: str, top_k: int = 10) -> Figure:
    fig = Figure(figsize=(6,4))
    ax = fig.subplots()
    counts = df[col].value_counts().nlargest(top_k)
    if counts.empty:
        ax.text(0.5, 0.5, 'No categories', ha='center')
        return fig
    counts.plot(kind='bar', ax=ax)
    ax.set_title(f'Top {top_k} categories: {col}')
    ax.set_ylabel('count')
    fig.tight_layout()
    return fig

def fig_corr_heatmap(df: pd.DataFrame, numeric_cols: List[str]) -> Figure:
    fig = Figure(figsize=(6,6))
    ax = fig.subplots()
    if len(numeric_cols) < 2:
        ax.text(0.5, 0.5, 'Not enough numeric columns for correlation', ha='center')
        return fig
    corr = df[numeric_cols].corr()
    im = ax.imshow(corr, aspect='auto', vmin=-1, vmax=1)
    ax.set_xticks(range(len(numeric_cols)))
    ax.set_yticks(range(len(numeric_cols)))
    ax.set_xticklabels(numeric_cols, rotation=90, fontsize=8)
    ax.set_yticklabels(numeric_cols, fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title('Correlation matrix')
    fig.tight_layout()
    return fig

def fig_time_series(df: pd.DataFrame, date_col: str, numeric_cols: List[str], resample: Optional[str] = 'D') -> Figure:
    fig = Figure(figsize=(8,4))
    ax = fig.subplots()
    try:
        s = df.copy()
        s[date_col] = pd.to_datetime(s[date_col], errors='coerce')
        s = s.set_index(date_col)
        s = s.sort_index()
    except Exception:
        ax.text(0.5, 0.5, 'Failed to parse dates', ha='center')
        return fig
    if not numeric_cols:
        ax.text(0.5, 0.5, 'No numeric columns', ha='center')
        return fig
    var_scores = s[numeric_cols].var().sort_values(ascending=False)
    top = var_scores.index[:3].tolist()
    if resample:
        try:
            s_res = s[top].resample(resample).mean()
            s_res.plot(ax=ax)
        except Exception:
            s[top].plot(ax=ax)
    else:
        s[top].plot(ax=ax)
    ax.set_title('Time series')
    ax.set_xlabel('date')
    ax.set_ylabel('value')
    fig.tight_layout()
    return fig

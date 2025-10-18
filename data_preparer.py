import pandas as pd
from typing import Optional, List, Tuple

def load_data(path_or_url: str, nrows: Optional[int] = None) -> pd.DataFrame:
    try:
        df = pd.read_csv(path_or_url, nrows=nrows)
        return df
    except Exception:
        pass
    try:
        df = pd.read_csv(path_or_url, sep=';', nrows=nrows)
        return df
    except Exception:
        pass
    df = pd.read_csv(path_or_url, engine='python', nrows=nrows)
    return df


def _try_numeric_variants(series: pd.Series) -> Tuple[pd.Series, int]:
    s = series.astype(str).copy()
    s = s.replace('nan', pd.NA)
    try0 = pd.to_numeric(series, errors='coerce')
    s1 = series.astype(str).str.replace(r"[,\s']+", "", regex=True)
    try1 = pd.to_numeric(s1.replace({'nan': pd.NA}), errors='coerce')
    s2 = series.astype(str).str.replace(',', '.', regex=False).str.replace(r"\s+", "", regex=True)
    try2 = pd.to_numeric(s2.replace({'nan': pd.NA}), errors='coerce')
    s3 = series.astype(str).str.replace(r"\s+", "", regex=True)
    try3 = pd.to_numeric(s3.replace({'nan': pd.NA}), errors='coerce')
    candidates = [try0, try1, try2, try3]
    counts = [c.notna().sum() for c in candidates]
    best_idx = max(range(len(candidates)), key=lambda i: counts[i])
    return candidates[best_idx], counts[best_idx]


def _cleanse_numeric_columns(df: pd.DataFrame, min_ratio: float = 0.6) -> pd.DataFrame:
    df = df.copy()
    obj_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    nrows = len(df)
    for col in obj_cols:
        series = df[col]
        non_empty = series.dropna().shape[0]
        if non_empty == 0:
            continue
        converted, count_non_na = _try_numeric_variants(series)
        if (count_non_na / max(1, nrows)) >= min_ratio:
            df[col] = converted
    return df


def basic_clean(df: pd.DataFrame, drop_threshold: float = 0.5) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().replace(' ', '_') for c in df.columns]
    df = df.drop_duplicates()
    df = df.replace(r'^\s*$', pd.NA, regex=True)
    df = _cleanse_numeric_columns(df, min_ratio=0.6)
    df = df.dropna(how='all')
    if 0.0 < drop_threshold < 1.0:
        thresh = int((1.0 - drop_threshold) * df.shape[1])
        if thresh <= 0:
            pass
        else:
            df = df.dropna(axis=0, thresh=thresh)
    return df


def infer_types(df: pd.DataFrame, date_candidates: Optional[List[str]] = None) -> Tuple[List[str], List[str], List[str]]:
    if date_candidates is None:
        date_candidates = ['date', 'datetime', 'time', 'day', 'year']
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
    date_cols = []
    for col in df.columns:
        low = col.lower()
        if any(tok in low for tok in date_candidates):
            try:
                parsed = pd.to_datetime(df[col], errors='coerce')
                if parsed.notna().sum() > 0:
                    date_cols.append(col)
                    if col in categorical_cols:
                        categorical_cols.remove(col)
            except Exception:
                pass
    for col in list(categorical_cols):
        try:
            parsed = pd.to_datetime(df[col], errors='coerce')
            if parsed.notna().sum() / max(1, len(df)) > 0.6:
                date_cols.append(col)
                categorical_cols.remove(col)
        except Exception:
            pass
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    return date_cols, numeric_cols, categorical_cols


def summary_stats(df: pd.DataFrame, numeric_cols: List[str]) -> pd.DataFrame:
    if not numeric_cols:
        return pd.DataFrame()
    stats = df[numeric_cols].describe().T
    stats['median'] = df[numeric_cols].median()
    stats['missing'] = df[numeric_cols].isna().sum()
    keep = [c for c in ['count','mean','median','std','min','25%','50%','75%','max','missing'] if c in stats.columns]
    return stats[keep]

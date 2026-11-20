"""거리 계산 / 최근접 매칭 유틸."""
import numpy as np
import pandas as pd
from scipy.spatial import KDTree

EARTH_RADIUS_KM = 6371.0


def haversine(lat1, lon1, lat2, lon2):
    """두 위경도 좌표 사이의 대원거리(km)."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def nearest_join(left: pd.DataFrame, right: pd.DataFrame, value_cols, distance_col=None,
                 lat="latitude", lon="longitude") -> pd.DataFrame:
    """left 각 행에 대해 가장 가까운 right 행의 value_cols 값을 붙여 반환한다."""
    out = left.copy()
    tree = KDTree(right[[lat, lon]].to_numpy())
    _, idx = tree.query(out[[lat, lon]].to_numpy(), k=1)
    matched = right.iloc[idx].reset_index(drop=True)
    for col, new_name in (value_cols.items() if isinstance(value_cols, dict)
                          else ((c, c) for c in value_cols)):
        out[new_name] = matched[col].to_numpy()
    if distance_col:
        out[distance_col] = haversine(out[lat].to_numpy(), out[lon].to_numpy(),
                                      matched[lat].to_numpy(), matched[lon].to_numpy())
    return out

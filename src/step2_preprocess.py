"""2단계: 침수흔적도 전처리 + 지형·강수 변수 결합.

  - 2023·2024 서울시 침수흔적도(SHP) → 침수 폴리곤 중심점 위경도
  - 등고선(N3L_F001.shp) 중 가장 가까운 선의 높이  → height, distance_km
  - 가장 가까운 기상관측소의 노장해발고도            → 해발고도, 해발고도_distance_km
  - 같은 날짜, 가장 가까운 AWS 관측소의 일강수량      → 일강수량 (mm)
  - 결과: data/interim/tidy.csv

실행: python -m src.step2_preprocess
"""
import geopandas as gpd
import pandas as pd

from .config import (CONTOUR_SHP, FLOOD_SHP, SEOUL_DAILY_RAIN_CSV, STATION_META_CSV,
                     TIDY_CSV)
from .geo_utils import nearest_join

FLOOD_COLS = ["latitude", "longitude", "F_AREA", "F_AVR_HGT", "F_ZONE_NM",
              "F_SAT_YMD", "F_SAT_TM", "F_YR"]


def add_centroid_latlon(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """중심점은 원래의 투영좌표계(m 단위)에서 구한 뒤 WGS84로 변환한다."""
    centroids = gdf.geometry.centroid.to_crs(epsg=4326)
    gdf = gdf.copy()
    gdf["latitude"] = centroids.y
    gdf["longitude"] = centroids.x
    return gdf


def load_flood_points() -> pd.DataFrame:
    frames = []
    for year, path in FLOOD_SHP.items():
        gdf = gpd.read_file(path)
        gdf = gdf[gdf.geometry.notna()]
        frames.append(pd.DataFrame(add_centroid_latlon(gdf))[FLOOD_COLS])
    df = pd.concat(frames, ignore_index=True).dropna(subset=["F_SAT_YMD"])
    df["F_SAT_YMD"] = df["F_SAT_YMD"].astype(int)
    return df


def load_contours() -> pd.DataFrame:
    contour = add_centroid_latlon(gpd.read_file(CONTOUR_SHP))
    return pd.DataFrame(contour)[["HEIGHT", "latitude", "longitude"]]


def load_station_elevation() -> pd.DataFrame:
    dt = pd.read_csv(STATION_META_CSV, encoding="cp949")
    dt = dt.rename(columns={"위도": "latitude", "경도": "longitude"})
    return dt[["latitude", "longitude", "노장해발고도(m)"]].dropna()


def attach_daily_rain(points: pd.DataFrame) -> pd.DataFrame:
    """침수일과 같은 날짜의 관측값 중에서만 최근접 관측소를 찾는다."""
    rain = (pd.read_csv(SEOUL_DAILY_RAIN_CSV)
              .rename(columns={"위도": "latitude", "경도": "longitude", "날짜": "F_SAT_YMD"})
              .dropna(subset=["latitude", "longitude"]))
    rain["일강수량 (mm)"] = pd.to_numeric(rain["일강수량 (mm)"], errors="coerce")

    parts = []
    for ymd, grp in points.groupby("F_SAT_YMD"):
        same_day = rain[rain["F_SAT_YMD"] == ymd]
        if same_day.empty:
            print(f"[{ymd}] 해당 날짜 일강수량 없음 → NaN")
            parts.append(grp.assign(**{"일강수량 (mm)": float("nan")}))
            continue
        parts.append(nearest_join(grp, same_day, ["일강수량 (mm)"]))
    return pd.concat(parts).sort_index()


def main():
    points = load_flood_points()
    points = nearest_join(points, load_contours(), {"HEIGHT": "height"}, "distance_km")
    points = nearest_join(points, load_station_elevation(),
                          {"노장해발고도(m)": "해발고도"}, "해발고도_distance_km")
    points = attach_daily_rain(points)

    TIDY_CSV.parent.mkdir(parents=True, exist_ok=True)
    points.to_csv(TIDY_CSV, index=False, encoding="utf-8-sig")
    print(f"저장 완료: {TIDY_CSV} ({len(points)}행)")


if __name__ == "__main__":
    main()

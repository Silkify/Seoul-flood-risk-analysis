"""3단계: 침수 발생 (자치구, 날짜)별 시간당 최대 강수량·습도 수집.

  - tidy.csv 의 (자치구, 날짜) 조합마다 해당 구 AWS의 '관측:60분간격' 표 크롤링
  - 하루 24시간 중 1시간 강수량이 가장 큰 시각의 강수량·습도 추출
  - 결과: data/interim/hourly_max_rain.csv

실행: python -m src.step3_hourly_rain  [--skip-crawl]
"""
import argparse
import difflib
from io import StringIO

import pandas as pd

from .aws_crawler import AwsPage, fetch, make_driver
from .config import AWS_HOURLY_HTML_DIR, HOURLY_MAX_CSV, SEOUL_STATIONS, TIDY_CSV

RAIN_COL = "1시간강수 (mm)"
HUMID_COL = "습도 (%)"


def gu_of(zone_name: str) -> str:
    """'강동구 명일동 352-12' → '강동구'"""
    return zone_name.split()[0]


def match_station(gu: str, stations=SEOUL_STATIONS):
    """자치구 이름 → AWS 관측소 이름. ('강동구'→'강동', '영등포구'→'영등포 *')"""
    key = gu.removesuffix("구") if len(gu) > 2 else gu
    for s in stations:
        if s.rstrip(" *") == key:
            return s
    hit = difflib.get_close_matches(key, stations, n=1, cutoff=0.6)
    return hit[0] if hit else None


def targets() -> pd.DataFrame:
    tidy = pd.read_csv(TIDY_CSV)
    t = pd.DataFrame({"gu": tidy["F_ZONE_NM"].map(gu_of), "F_SAT_YMD": tidy["F_SAT_YMD"]})
    t = t.drop_duplicates().reset_index(drop=True)
    t["station"] = t["gu"].map(match_station)
    return t


def html_path(gu: str, ymd):
    return AWS_HOURLY_HTML_DIR / f"{gu}_{ymd}_60분.html"


def crawl(t: pd.DataFrame):
    driver = make_driver()
    page = AwsPage(driver)
    try:
        for row in t.itertuples():
            path = html_path(row.gu, row.F_SAT_YMD)
            if path.exists():
                continue
            if row.station is None:
                print(f"[{row.gu}] 관측소 매칭 실패 → 건너뜀")
                continue
            ymd = str(row.F_SAT_YMD)
            try:
                fetch(page, "관측:60분간격", f"{ymd[:4]}.{ymd[4:6]}.{ymd[6:]} 23:59",
                      path, station_name_ko=row.station)
            except Exception as e:
                print(f"[{row.gu} {ymd}] 실패: {e}")
    finally:
        driver.quit()


def max_hour_row(path) -> pd.Series:
    """24시간 표에서 1시간 강수량 최대 행."""
    df = pd.read_html(StringIO(path.read_text(encoding="utf-8")))[0].iloc[:24].copy()
    df[RAIN_COL] = pd.to_numeric(df[RAIN_COL], errors="coerce").fillna(0)  # '-', 'X' → 0
    df[HUMID_COL] = pd.to_numeric(df[HUMID_COL], errors="coerce")
    return df.loc[df[RAIN_COL].idxmax(), ["시:분", RAIN_COL, HUMID_COL]]


def build_table(t: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in t.itertuples():
        path = html_path(row.gu, row.F_SAT_YMD)
        if not path.exists():
            continue
        r = max_hour_row(path)
        rows.append({"gu": row.gu, "F_SAT_YMD": row.F_SAT_YMD, "station": row.station,
                     "max_rain_time": r["시:분"], RAIN_COL: r[RAIN_COL], HUMID_COL: r[HUMID_COL]})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-crawl", action="store_true", help="이미 받은 HTML만 사용")
    args = ap.parse_args()

    t = targets()
    if not args.skip_crawl:
        crawl(t)
    table = build_table(t)
    HOURLY_MAX_CSV.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(HOURLY_MAX_CSV, index=False, encoding="utf-8-sig")
    print(f"저장 완료: {HOURLY_MAX_CSV} ({len(table)}행)")


if __name__ == "__main__":
    main()

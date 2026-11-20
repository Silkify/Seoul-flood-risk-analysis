"""1단계: 침수 발생일의 서울 전체 AWS 일극값(일강수량 등) 수집.

  - 침수 발생일마다 '관측:일극값' 표를 크롤링 → data/interim/aws_daily/*.html
  - 표를 합치고 관측지점 정보(dt.csv)의 위도·경도·해발고도를 붙임
  - 결과: data/interim/서울관측소및강수량.csv

실행: python -m src.step1_daily_rain  [--skip-crawl]
"""
import argparse
from io import StringIO

import pandas as pd

from .aws_crawler import AwsPage, fetch, make_driver
from .config import AWS_DAILY_HTML_DIR, SEOUL_DAILY_RAIN_CSV, STATION_META_CSV

# 2023·2024 침수흔적도에 기록된 침수 시작일(F_SAT_YMD)
FLOOD_DATES = [
    "20240715", "20240717", "20240718", "20240719", "20240722", "20240723", "20240727",
    "20230608", "20230710", "20230711", "20230713", "20230714", "20230716", "20230717",
    "20230718", "20230719", "20230730", "20230809",
]


def crawl(dates):
    driver = make_driver()
    page = AwsPage(driver)
    try:
        for ymd in dates:
            path = AWS_DAILY_HTML_DIR / f"서울전체_{ymd}_일극값.html"
            if path.exists():
                continue
            try:
                fetch(page, "관측:일극값", f"{ymd[:4]}.{ymd[4:6]}.{ymd[6:]} 00:00", path)
            except Exception as e:  # 한 날짜가 실패해도 계속 진행
                print(f"[{ymd}] 실패: {e}")
    finally:
        driver.quit()


def parse_daily_html(path) -> pd.DataFrame:
    df = pd.read_html(StringIO(path.read_text(encoding="utf-8")))[0]
    # 정렬 버튼 텍스트가 붙은 헤더 정리: '번호 내림차순 오름차순' → '지점'
    df = df.rename(columns=lambda c: "지점" if c.startswith("번호")
                   else "지점명" if c.startswith("지점") else c)
    df.insert(0, "날짜", int(path.stem.split("_")[1]))
    return df


def build_table() -> pd.DataFrame:
    files = sorted(AWS_DAILY_HTML_DIR.glob("*.html"))
    if not files:
        raise FileNotFoundError(f"{AWS_DAILY_HTML_DIR} 에 HTML이 없습니다. 크롤링을 먼저 실행하세요.")
    daily = pd.concat([parse_daily_html(f) for f in files], ignore_index=True)

    meta = (pd.read_csv(STATION_META_CSV, encoding="cp949")
              .drop_duplicates(subset="지점", keep="first")
              [["지점", "위도", "경도", "노장해발고도(m)"]])
    return daily.merge(meta, on="지점", how="left")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-crawl", action="store_true", help="이미 받은 HTML만 사용")
    args = ap.parse_args()

    if not args.skip_crawl:
        crawl(FLOOD_DATES)
    table = build_table()
    SEOUL_DAILY_RAIN_CSV.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(SEOUL_DAILY_RAIN_CSV, index=False, encoding="utf-8-sig")
    print(f"저장 완료: {SEOUL_DAILY_RAIN_CSV} ({len(table)}행)")


if __name__ == "__main__":
    main()

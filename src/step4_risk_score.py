"""4단계: 침수 위험도 점수 산정.

  위험점수 = 평균표고 점수 + 습도 가중 시간강수 점수 + 등고선 높이 점수
  등급: 5.5 이상 '상', 3 이상 '중', 그 외 '하'
  결과: data/output/complete.csv

실행: python -m src.step4_risk_score
"""
import pandas as pd

from .config import HOURLY_MAX_CSV, RESULT_CSV, TIDY_CSV
from .step3_hourly_rain import HUMID_COL, RAIN_COL, gu_of


def weighted_rain(rain_mm: float, humidity: float) -> float:
    """습도가 높으면(≥70%) 강수 영향을 키우고, 매우 낮으면(≤20%) 줄인다."""
    h = humidity / 100
    if h >= 0.7:
        return rain_mm * (1 + (1 - h))
    if h <= 0.2:
        return rain_mm * (1 - h)
    return rain_mm


def score_avg_height(x: float) -> float:
    """침수흔적 평균 표고(F_AVR_HGT, m)"""
    if x < 12:
        return 1
    if x < 35:
        return 2
    if x < 60:
        return 3
    return 8


def score_rain(x: float) -> float:
    """습도 가중 시간당 강수량(mm)"""
    if x <= 20:
        return 1
    if x < 30:
        return 1.5
    if x < 52:
        return 2
    if x < 72:
        return 3
    return 8


def score_contour_height(x: float) -> float:
    """최근접 등고선 높이(m) — 낮을수록 물이 모이기 쉬움"""
    if x <= 50:
        return 0.9
    if x < 100:
        return 0.6
    return 0.3


def grade(score: float) -> str:
    if score >= 5.5:
        return "상"
    if score >= 3:
        return "중"
    return "하"


def main():
    tidy = pd.read_csv(TIDY_CSV)
    tidy["gu"] = tidy["F_ZONE_NM"].map(gu_of)
    hourly = pd.read_csv(HOURLY_MAX_CSV)[["gu", "F_SAT_YMD", RAIN_COL, HUMID_COL]]
    df = tidy.merge(hourly, on=["gu", "F_SAT_YMD"], how="inner")

    df["weighted_rain_score"] = [weighted_rain(r, h) for r, h in zip(df[RAIN_COL], df[HUMID_COL])]
    df["risk_score"] = (df["F_AVR_HGT"].map(score_avg_height)
                        + df["weighted_rain_score"].map(score_rain)
                        + df["height"].map(score_contour_height))
    df["위험도"] = df["risk_score"].map(grade)

    RESULT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RESULT_CSV, index=False, encoding="utf-8-sig")
    print(f"저장 완료: {RESULT_CSV} ({len(df)}행)")
    print(df["위험도"].value_counts().to_string())


if __name__ == "__main__":
    main()

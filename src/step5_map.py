"""5단계: 위험도 지도 시각화 (folium).

  침수 지점을 위험도 등급별 색으로, 면적에 비례한 원으로 표시한다.
  결과: data/output/map.html

실행: python -m src.step5_map
"""
import folium
import pandas as pd

from .config import MAP_HTML, RESULT_CSV

SEOUL_CENTER = [37.5665, 126.9780]
GRADE_COLOR = {"상": "red", "중": "orange", "하": "green"}


def main():
    df = pd.read_csv(RESULT_CSV)
    m = folium.Map(location=SEOUL_CENTER, zoom_start=11)
    for row in df.itertuples():
        folium.CircleMarker(
            location=[row.latitude, row.longitude],
            radius=max(row.F_AREA / 10, 3),
            color=GRADE_COLOR.get(row.위험도, "gray"),
            fill=True, fill_opacity=0.4,
            tooltip=f"{row.F_ZONE_NM} · {row.F_SAT_YMD} · 위험도 {row.위험도}",
        ).add_to(m)
    MAP_HTML.parent.mkdir(parents=True, exist_ok=True)
    m.save(MAP_HTML)
    print(f"저장 완료: {MAP_HTML}")


if __name__ == "__main__":
    main()

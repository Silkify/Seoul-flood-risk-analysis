"""경로와 공통 상수."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"            # 직접 내려받는 원본 데이터 (깃에 올리지 않음)
INTERIM = DATA / "interim"    # 크롤링 HTML, 중간 CSV
OUTPUT = DATA / "output"      # 최종 결과

# --- 원본 데이터 파일 (data/raw/ 에 넣어주세요) ---
FLOOD_SHP = {
    2024: RAW / "2024_서울시_침수흔적도.shp",
    2023: RAW / "2023_서울시_침수흔적도.shp",
}
CONTOUR_SHP = RAW / "N3L_F001.shp"          # 수치지형도 등고선
STATION_META_CSV = RAW / "dt.csv"           # 기상청 관측지점 정보 (cp949)

# --- 중간/최종 산출물 ---
AWS_DAILY_HTML_DIR = INTERIM / "aws_daily"
AWS_HOURLY_HTML_DIR = INTERIM / "aws_hourly"
SEOUL_DAILY_RAIN_CSV = INTERIM / "서울관측소및강수량.csv"
TIDY_CSV = INTERIM / "tidy.csv"
HOURLY_MAX_CSV = INTERIM / "hourly_max_rain.csv"
RESULT_CSV = OUTPUT / "complete.csv"
MAP_HTML = OUTPUT / "map.html"

AWS_URL = "https://www.weather.go.kr/w/observation/land/aws-obs.do"

# 크롤링 시점에 사이트에서 수집한 서울 AWS 관측소 목록
SEOUL_STATIONS = [
    "강남", "강동", "강북", "강서", "관악", "광진", "구로", "금천", "기상청",
    "김포(공)", "남현", "노원", "도봉", "동대문", "마포", "서대문", "서울", "서초",
    "성동", "성북", "송파 *", "양천", "영등포 *", "용산", "은평", "중구", "중랑",
    "한강", "현충원",
]

"""기상청 방재기상관측(AWS) 페이지 Selenium 크롤러.

https://www.weather.go.kr/w/observation/land/aws-obs.do 에서
관측 간격 · 날짜 · 지역(· 관측소)을 선택한 뒤 페이지 HTML을 저장한다.
"""
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from .config import AWS_URL

TIME_OPEN_BTN = '//*[@id="aws-panel-wrap"]/div[1]/div[2]/div[1]/a[1]'
TIME_APPLY_BTN = '//*[@id="aws-panel-wrap"]/div[1]/div[2]/div[1]/a[2]'
DATEPICKER_CLOSE_BTN = '//button[contains(@class, "ui-datepicker-close")]'


def make_driver(headless: bool = False):
    """Selenium 4.6+ 는 Selenium Manager가 크롬드라이버를 자동으로 맞춰준다."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


class AwsPage:
    def __init__(self, driver, timeout: int = 10):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def _click(self, xpath: str):
        self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath))).click()

    def open(self):
        self.driver.get(AWS_URL)
        time.sleep(2)

    def select_interval(self, interval_text: str):
        """예: '관측:일극값', '관측:60분간격', '관측:30분간격'"""
        box = Select(self.wait.until(EC.presence_of_element_located((By.ID, "aws-db"))))
        box.select_by_visible_text(interval_text)
        time.sleep(1)

    def set_datetime(self, datetime_str: str):
        """예: '2024.07.17 23:59'"""
        self._click(TIME_OPEN_BTN)
        time.sleep(1)
        date_input = self.wait.until(EC.element_to_be_clickable((By.ID, "aws-tm")))
        date_input.click()
        time.sleep(0.5)
        date_input.clear()
        date_input.send_keys(datetime_str)
        time.sleep(0.5)
        # 달력 팝업이 '적용' 버튼을 가리는 문제(ElementClickInterceptedException) 방지
        try:
            WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, DATEPICKER_CLOSE_BTN))).click()
            time.sleep(0.5)
        except TimeoutException:
            pass
        self._click(TIME_APPLY_BTN)
        time.sleep(2)

    def select_region(self, region_short: str):
        self._click(f'//a[@data-role="aws-sido-group" and @data-short-name="{region_short}"]')
        time.sleep(1)

    def select_station(self, station_name_ko: str):
        self._click(f'//a[@data-role="aws-data-item-select" and @data-name-ko="{station_name_ko}"]')
        time.sleep(2)

    def list_stations(self):
        buttons = self.driver.find_elements(By.CSS_SELECTOR, 'a[data-role="aws-data-item-select"]')
        return [b.get_attribute("data-name-ko") for b in buttons]

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.driver.page_source, encoding="utf-8")


def fetch(page: AwsPage, interval_text: str, datetime_str: str, save_path: Path,
          region_short: str = "서울", station_name_ko: str | None = None):
    """한 번의 조회 → HTML 저장. station_name_ko=None 이면 지역 전체 표."""
    page.open()
    page.select_interval(interval_text)
    page.set_datetime(datetime_str)
    page.select_region(region_short)
    if station_name_ko:
        page.select_station(station_name_ko)
    page.save(save_path)
    print(f"저장 완료: {save_path}")

import sys
sys.path.insert(0, "my_libs")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def crawl_watcha_boxoffice():
    # 웹드라이버 설정
    driver = webdriver.Chrome()
    url = "https://pedia.watcha.com/ko-KR/?domain=movie"
    
    try:
        # 페이지 로드
        driver.get(url)
        
        # 팝업창이 나타날 때까지 대기 (최대 5초)
        wait = WebDriverWait(driver, 2)
        try:
            # 팝업창의 닫기 버튼을 찾아서 클릭
            # 실제 팝업창의 닫기 버튼 클래스나 ID를 확인하여 수정 필요
            close_button = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "button.a3VOQo6v.Fxip6vYZ.bmNDNA_p")
            ))
            close_button.click()
        except TimeoutException:
            # 팝업창이 없는 경우 그냥 진행
            pass
        
        # 박스오피스 항목들이 로드될 때까지 대기
        wait = WebDriverWait(driver, 4)
        movies = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "li.zK9dEEA5.w_exposed_cell")
        ))
        
        boxoffice_list = []
        
        for movie in movies:
            try:
                # 영화 제목과 연도가 포함된 텍스트
                title = movie.find_element(By.CSS_SELECTOR, "div.Rw9JYf2r.MasrfAn6").text
                title_year = movie.find_element(By.CSS_SELECTOR, "div.WWPgNOuc.KYbG4TeN").text
                
                # 예매율과 누적 관객 정보
                stats = movie.find_element(By.CSS_SELECTOR, "div.VWL8zgFg.RiDHrQhO").text
                
                boxoffice_list.append({
                    'title': title,
                    'title_year': title_year, # title_year 대신 title로 변경
                    'stats': stats
                })
            except:
                continue
                
        return boxoffice_list
        
    finally:
        driver.quit()

# 실행
if __name__ == "__main__":
    results = crawl_watcha_boxoffice()
    
    # 결과 출력 (title_year를 title로 변경)
    for idx, movie in enumerate(results, 1):
        print(f"{idx}. {movie['title']}")
        print(f" {movie['title_year']}")
        print(f"   {movie['stats']}")
        print("-" * 50)      
import sys
sys.path.insert(0, "my_libs")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def _convert_audience_to_number(audience_text):
    """
    관객수 텍스트를 숫자로 변환하는 함수
    예: "1.1만명" -> 11000, "1,234명" -> 1234
    """
    # 숫자와 단위 추출
    number_part = ''.join(filter(lambda x: x.isdigit() or x == '.', audience_text))
    number = float(number_part)
    
    # 만 단위 변환
    if '만' in audience_text:
        number = int(number * 10000)
    else:
        number = int(number)
    
    return number

def sort_by_audience(movie_list, ascending=False):
    """
    영화 목록을 누적 관객수 기준으로 정렬하는 함수
    Args:
        movie_list (list): 영화 정보가 담긴 딕셔너리 리스트
        ascending (bool): True면 오름차순, False면 내림차순 (기본값: False)
    Returns:
        list: 정렬된 영화 목록
    """
    return sorted(movie_list, key=lambda x: x['audience_number'], reverse=not ascending)

def crawl_watcha_boxoffice():
    # 웹드라이버 설정 (headless 모드)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  ## 크롬이 headless 모드로 실행되도록함함(창이 안뜨도록록)
    options.add_argument('--disable-gpu')  # GPU 가속 비활성화 (일부 시스템에서 필요)
    options.add_argument('--no-sandbox')  # 샌드박스 비활성화
    options.add_argument('--disable-dev-shm-usage')  # 공유 메모리 제한 비활성화
    
    driver = webdriver.Chrome(options=options)
    url = "https://pedia.watcha.com/ko-KR/?domain=movie"
    
    try:
        print("데이터를 가져오는 중입니다...")
        
        driver.get(url)## 왓챠피디아 페이지에 접근함함
        
        wait = WebDriverWait(driver, 3)## 로딩을 기다림
        try:
        
            close_button = wait.until(EC.presence_of_element_located(## 주석
                (By.CSS_SELECTOR, "button.a3VOQo6v.Fxip6vYZ.bmNDNA_p")## 주석
            ))
            close_button.click()## 주석
        except TimeoutException: ## 주석
            pass
        
        
        wait = WebDriverWait(driver, 5)## 주석
        movies = wait.until(EC.presence_of_all_elements_located(## 주석
            (By.CSS_SELECTOR, "li.zK9dEEA5.w_exposed_cell")## 주석
        ))
        
        boxoffice_list = []
        
        for movie in movies:
            try:
        
                title = movie.find_element(By.CSS_SELECTOR, "div.Rw9JYf2r.MasrfAn6").text    ## 주석
                title_year = movie.find_element(By.CSS_SELECTOR, "div.WWPgNOuc.KYbG4TeN").text## 주석
                
        
                stats = movie.find_element(By.CSS_SELECTOR, "div.VWL8zgFg.RiDHrQhO").text    ## 주석
                
        
                audience_text = stats.split('・')[1].strip()## 주석
                audience_number = _convert_audience_to_number(audience_text)## 주석 
                
                boxoffice_list.append({      ## 주석
                    'title': title,
                    'title_year': title_year,
                    'audience_text': audience_text,
                    'audience_number': audience_number
                })
            except:
                continue
                
        return boxoffice_list
        
    finally:
        driver.quit()

# 실행
if __name__ == "__main__":
    results = crawl_watcha_boxoffice()
    
    # 누적 관객수 기준으로 내림차순 정렬
    sorted_results = sort_by_audience(results)
    
    # 결과 출력
    for idx, movie in enumerate(sorted_results, 1): ## 주석
        print(f"{idx}. {movie['title']}")
        print(f" {movie['title_year']}")
        print(f" 누적 관객 : {movie['audience_number']:,}명")
        print("-" * 50)      
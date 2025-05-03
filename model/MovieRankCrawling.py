from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

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
    options.add_argument('--headless')  ## 크롬이 headless 모드로 실행되도록함(창이 안뜨도록)
    options.add_argument('--disable-gpu')  # GPU 가속 비활성화 (일부 시스템에서 필요)
    options.add_argument('--no-sandbox')  # 샌드박스 비활성화
    options.add_argument('--disable-dev-shm-usage')  # 공유 메모리 제한 비활성화
    
    driver = webdriver.Chrome(options=options)
    url = "https://pedia.watcha.com/ko-KR/?domain=movie"

    try:
        print("데이터를 가져오는 중입니다...")
        
        driver.get(url)## 왓챠피디아 페이지에 접근함
        
        wait = WebDriverWait(driver, 3)## 로딩을 기다림(최대 3초)
        try:
            close_button = wait.until(EC.presence_of_element_located(## 엘리먼트가 나올때까지 기다림
                (By.CSS_SELECTOR, "button.a3VOQo6v.Fxip6vYZ.bmNDNA_p")## 이 버튼이 나올때까지 기다림
            ))
            close_button.click()## 버튼을 클릭함
        except TimeoutException: ## 시간이 초과되면 패스함함
            pass
        
        wait = WebDriverWait(driver, 5)## 로딩을 기다림(최대 5초)
        movies = wait.until(EC.presence_of_all_elements_located(## 엘리먼트가 나올때까지 기다림
            (By.CSS_SELECTOR, "li.zK9dEEA5.w_exposed_cell")## 이 엘리먼트가 나올때까지 기다림
        ))
        
        boxoffice_list = []
        if not movies:
            print("영화 목록을 찾을 수 없습니다.")

        # 먼저 모든 영화의 기본 정보와 링크를 수집
        movie_info_list = []
        for movie in movies:
            try:
                title = movie.find_element(By.CSS_SELECTOR, "div.Rw9JYf2r.eotgxjY4").text    ## 이 엘리먼트의 텍스트를 title에 저장함
                title_year = movie.find_element(By.CSS_SELECTOR, "div.EIFs0yBF.KYbG4TeN").text## 이 엘리먼트의 텍스트를 title_year에 저장함
                
                stats = movie.find_element(By.CSS_SELECTOR, "div.orH2WmrM.RiDHrQhO").text    ## 이 엘리먼트의 텍스트를 stats에 저장함
                
                audience_text = stats.split('・')[1].strip()## stats의 텍스트를 ・를 기준으로 나눈후 audience_text에 저장함
                audience_number = _convert_audience_to_number(audience_text)## audience_text를 숫자로 변환하여 저장함

                # 영화의 모든 링크 가져오기
                movie_links = movie.find_elements(By.CSS_SELECTOR, "a")
                movie_link = None
                
                # 각 링크를 확인하여 영화 상세 페이지 링크 찾기
                for link in movie_links:
                    href = link.get_attribute("href")
                    if href and "/contents/" in href:  # 영화 상세 페이지 링크인지 확인
                        movie_link = href
                        break
                
                if movie_link:
                    movie_info_list.append({
                        'title': title,
                        'title_year': title_year,
                        'audience_number': audience_number,
                        'movie_link': movie_link
                    })
            except:
                continue

        # 각 영화의 상세 페이지에서 코멘트 수 가져오기
        for movie_info in movie_info_list:
            try:
                # 상세 페이지로 이동
                driver.get(movie_info['movie_link'])
                wait = WebDriverWait(driver, 2)  # 대기 시간 증가
                
                # 페이지가 완전히 로드될 때까지 대기
                time.sleep(1)
                
                # 코멘트 개수 가져오기
                try:
                    comment_element = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "span.LYpRbSY5.YBhuyor5")
                    ))
                    comment_count = comment_element.text
                except TimeoutException:
                    comment_count = "코멘트 정보 없음"
                
                boxoffice_list.append({
                    'title': movie_info['title'],
                    'title_year': movie_info['title_year'],
                    'audience_number': movie_info['audience_number'],
                    'comment_count': comment_count
                })
                
            except Exception as e:
                print(f"영화 정보를 가져오는데 실패했습니다. 오류: {e}")
                
        return boxoffice_list
        
    finally:
        driver.quit()

# 실행
if __name__ == "__main__":
    results = crawl_watcha_boxoffice()
    
    # 누적 관객수 기준으로 내림차순 정렬
    sorted_results = sort_by_audience(results)
    
    # 결과 출력
    for idx, movie in enumerate(sorted_results, 1): ## 관객수 기준으로 1위부터 나열하여 출력함
        print(f"{idx}. {movie['title']}")
        print(f" {movie['title_year']}")
        print(f" 누적 관객 : {movie['audience_number']:,}명")
        print(f" 코멘트 수 : {movie['comment_count']}")
        print("-" * 50)
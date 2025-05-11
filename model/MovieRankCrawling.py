from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dataclasses import dataclass
import time
import sys

@dataclass
class CommentInfo:
    comment_count: str
    comment_link: str
    comment_list: list[str]

@dataclass
class MovieInfo:
    title: str
    title_year: str
    audience_number: int
    movie_link: str
    comment_info: CommentInfo

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

def get_movie_info(movie):
    """
    영화 요소에서 영화 정보를 추출하는 함수
    Args:
        movie: Selenium WebElement 객체
    Returns:
        MovieInfo: 영화 정보를 담은 MovieInfo 객체 또는 None (정보 추출 실패 시)
    """
    try:
        # 제목 추출
        title_element = movie.find_element(By.CSS_SELECTOR, "div.Rw9JYf2r.eotgxjY4")
        title = title_element.text if title_element else "제목 없음"
        
        # 개봉년도 추출
        year_element = movie.find_element(By.CSS_SELECTOR, "div.EIFs0yBF.KYbG4TeN")
        title_year = year_element.text if year_element else "연도 정보 없음"
        
        # 관객수 추출
        stats_element = movie.find_element(By.CSS_SELECTOR, "div.orH2WmrM.RiDHrQhO")
        stats = stats_element.text if stats_element else ""
        
        # 관객수 텍스트에서 숫자만 추출
        audience_text = stats.split('・')[1].strip() if '・' in stats else "0명"
        audience_number = _convert_audience_to_number(audience_text)

        movie_links = movie.find_elements(By.CSS_SELECTOR, "a")
        movie_link = next(
            (link.get_attribute("href") for link in movie_links 
             if link.get_attribute("href") and "/contents/" in link.get_attribute("href")),
            None
        )
        
        if not movie_link:
            print(f"영화 '{title}'의 상세 페이지 링크를 찾을 수 없습니다.")
            return None
            
        return MovieInfo(
            title=title,
            title_year=title_year,
            audience_number=audience_number,
            movie_link=movie_link,
            comment_info=CommentInfo(
                comment_count="코멘트 정보 없음",
                comment_link=None,
                comment_list=[]
            )
        )
        
    except Exception as e:
        print(f"영화 정보 추출 중 오류 발생: {str(e)}")
        return None

def get_comment_list(driver, comment_link):
    """
    영화의 상위 10개 코멘트를 가져오는 함수
    Args:
        driver: Selenium WebDriver 객체
        comment_link: 코멘트 페이지 링크
    Returns:
        list[str]: 코멘트 목록
    """
    try:
        print(f"코멘트를 가져오는 중입니다: {comment_link}")
        
        driver.get(comment_link)
        wait = WebDriverWait(driver, 5)
        time.sleep(2)
        
        # 코멘트 article 요소 찾기
        comment_articles = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "ul.M0RC1CZi article.nSrzrW7M")
        ))
        
        comments = []
        for article in comment_articles[:10]:  # 상위 10개 코멘트만 가져오기
            try:
                # 코멘트 텍스트 요소 찾기
                comment_text = article.find_element(By.CSS_SELECTOR, "p.BEKXQlwB.vc3vf0Y6.CommentText").text
                if comment_text:
                    comments.append(comment_text)
            except Exception as e:
                print(f"개별 코멘트 추출 실패: {e}")
                continue
                
        return comments
        
    except Exception as e:
        print(f"코멘트 목록을 가져오는데 실패했습니다. 오류: {e}")
        return []

def create_comment_info(driver, movie_link):
    """
    영화의 코멘트 정보를 수집하는 함수
    Args:
        driver: Selenium WebDriver 객체
        movie_link: 영화 상세 페이지 링크
    Returns:
        CommentInfo: 코멘트 정보를 담은 CommentInfo 객체
    """
    try:
        driver.get(movie_link)
        wait = WebDriverWait(driver, 2)
        time.sleep(1)
        
        try:
            comment_element = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "span.LYpRbSY5.YBhuyor5")
            ))
            comment_count = comment_element.text
            comment_link = movie_link + '/comments'
            
            # 코멘트 목록 가져오기
            comment_list = get_comment_list(driver, comment_link)
            
        except TimeoutException:
            print(f"코멘트 정보를 찾을 수 없습니다: {movie_link}")
            comment_count = "코멘트 정보 없음"
            comment_link = None
            comment_list = []
        
        return CommentInfo(
            comment_count=comment_count,
            comment_link=comment_link,
            comment_list=comment_list
        )
        
    except Exception as e:
        print(f"코멘트 정보를 가져오는데 실패했습니다. 오류: {e}")
        return CommentInfo(
            comment_count="코멘트 정보 없음",
            comment_link=None,
            comment_list=[]
        )

def crawl_watcha_boxoffice():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    url = "https://pedia.watcha.com/ko-KR/?domain=movie"

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 3)
        try:
            close_button = wait.until(EC.presence_of_element_located(## 엘리먼트가 나올때까지 기다림
                (By.CSS_SELECTOR, "button.a3VOQo6v.Fxip6vYZ.bmNDNA_p")## 이 버튼이 나올때까지 기다림
            ))
            close_button.click()## 버튼을 클릭함
        except TimeoutException: ## 시간이 초과되면 패스함함
            pass
        
        # 영화 목록 가져오기
        wait = WebDriverWait(driver, 5)
        movies = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "li.zK9dEEA5.w_exposed_cell")
        ))
        
        if not movies:
            print("영화 목록을 찾을 수 없습니다.")
            return []

        print(f"총 {len(movies)}개의 영화를 찾았습니다.")
        
        # 먼저 모든 영화의 기본 정보를 수집
        movie_info_list = []
        for idx, movie in enumerate(movies, 1):
            print(f"\n{idx}번째 영화 정보 수집 중...")
            movie_info = get_movie_info(movie)
            if movie_info:
                movie_info.comment_info = create_comment_info(driver, movie_info.movie_link)
                movie_info_list.append(movie_info)
                time.sleep(1)
                
        return movie_info_list
        
    finally:
        driver.quit()

# 실행
if __name__ == "__main__":
    results = crawl_watcha_boxoffice()
    sorted_results = sorted(results, key=lambda x: x.audience_number, reverse=True)
    
    for idx, movie in enumerate(sorted_results, 1):
        print(f"\n{idx}. {movie.title} ({movie.title_year})")
        print(f"누적 관객: {movie.audience_number:,}명")
        print(f"코멘트 수: {movie.comment_info.comment_count}")
        print(f"영화 링크: {movie.movie_link}")
        if movie.comment_info.comment_list:
            print("\n상위 10개 코멘트:")
            for i, comment in enumerate(movie.comment_info.comment_list, 1):
                print(f"{i}. {comment}")
        print("-" * 50)


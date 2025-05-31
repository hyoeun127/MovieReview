from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dataclasses import dataclass
from typing import List
import time
import emoji
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 상수 선언
MAX_MOVIES = 1
MAX_WORKERS = 5  # 코멘트 처리 스레드 수

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

class MovieCrawling:
    def start(self, movie_count):
        start_time = datetime.now()
        self.movie_count = movie_count
        movies = self._crawl_watcha_boxoffice()
        sorted_movies = sorted(movies, key=lambda x: x.audience_number, reverse=True)
        sorted_movies:List[MovieInfo]
        
        for idx, movie in enumerate(sorted_movies, 1):
            print(f"\n{idx}. {movie.title} ({movie.title_year})")
            print(f"누적 관객: {movie.audience_number:,}명")
            print(f"코멘트 수: {movie.comment_info.comment_count}")
            print(f"영화 링크: {movie.movie_link}")
            print(f"수집된 코멘트 개수 : {len(movie.comment_info.comment_list)}")
            print("-" * 50)
            
            movie.comment_info.comment_list = self._delete_special_character(movie.comment_info.comment_list)
            print("--- 코멘트 확인 ---")
            
            if len(movie.comment_info.comment_list) == 0:
                print("코멘트 없음")
        
        end_time = datetime.now()
        print(f"처리시간 {end_time - start_time}")
        return sorted_movies

    def _convert_audience_to_number(self, audience_text):
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

    def _sort_by_audience(self, movie_list, ascending=False):
        """
        영화 목록을 누적 관객수 기준으로 정렬하는 함수
        Args:
            movie_list (list): 영화 정보가 담긴 딕셔너리 리스트
            ascending (bool): True면 오름차순, False면 내림차순 (기본값: False)
        Returns:
            list: 정렬된 영화 목록
        """
        return sorted(movie_list, key=lambda x: x['audience_number'], reverse=not ascending)

    def _get_movie_info(self, movie):
        """
        영화 요소에서 영화 정보를 추출하는 함수
        Args:
            movie: Selenium WebElement 객체
        Returns:
            MovieInfo: 영화 정보를 담은 MovieInfo 객체 또는 None (정보 추출 실패 시)
        """
        try:
            time.sleep(0.5)  # 대기 시간 감소
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
            audience_number = self._convert_audience_to_number(audience_text)

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

    def _process_comment(self, article):
        """개별 코멘트 처리"""
        try:
            comment_text = article.find_element(By.CSS_SELECTOR, "p.BEKXQlwB.vc3vf0Y6.CommentText").text
            if comment_text:
                if comment_text == "스포일러가 있어요!!보기":
                    try:
                        spoiler_button = article.find_element(By.XPATH, ".//button[contains(text(), '보기')]")
                        spoiler_button.click()
                        time.sleep(0.2)
                        comment_text = article.find_element(By.CSS_SELECTOR, "p.BEKXQlwB.vc3vf0Y6.CommentText").text
                    except Exception:
                        return None
                return comment_text
        except Exception:
            return None
        return None

    def _get_comment_list(self, driver, comment_link):
        """
        영화의 코멘트를 스크롤을 통해 가져오는 함수
        """
        try:
            driver.get(comment_link)
            wait = WebDriverWait(driver, 1)
            time.sleep(0.5)
            
            comments = []
            last_height = driver.execute_script("return document.body.scrollHeight")
            
            while len(comments) < 100:
                comment_articles = wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "ul.M0RC1CZi article.nSrzrW7M")
                ))
                
                # 새로운 코멘트만 처리
                new_articles = comment_articles[len(comments):]
                
                # 병렬로 코멘트 처리
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = [executor.submit(self._process_comment, article) for article in new_articles]
                    for future in as_completed(futures):
                        comment = future.result()
                        if comment:
                            comments.append(comment)
                
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.2)
                
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                    
                last_height = new_height
            
            return comments
            
        except Exception as e:
            print(f"코멘트 목록을 가져오는데 실패했습니다. 오류: {e}")
            return []

    def _create_comment_info(self, movie_link):
        """
        영화의 코멘트 정보를 수집하는 함수
        Args:
            driver: Selenium WebDriver 객체
            movie_link: 영화 상세 페이지 링크
        Returns:
            CommentInfo: 코멘트 정보를 담은 CommentInfo 객체
        """
        try:
            driver = self._get_driver_by_url(movie_link)
            self._close_popup(driver)
            comment_count = 0
            comment_link = ""
            comment_list = []
            driver.get(movie_link)
            wait = WebDriverWait(driver, 2)
            time.sleep(1)
            
            try:
                comment_element = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "span.LYpRbSY5.YBhuyor5")
                ))
                comment_count = comment_element.text
                comment_link = None
                comment_list = []
                
                comment_link = movie_link + '/comments'
                comment_list = []
                # 코멘트 목록 가져오기
                comment_list = self._get_comment_list(driver, comment_link)

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

    def _crawl_watcha_boxoffice(self):
        
        url = "https://pedia.watcha.com/ko-KR/?domain=movie"
        driver = self._get_driver_by_url(url)
        
        try:
            # 팝업창 닫기
            self._close_popup(driver)
            # 영화 목록 가져오기
            wait = WebDriverWait(driver, 2)
            movies = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "li.zK9dEEA5.w_exposed_cell")
            ))
            
            if not movies:
                print("영화 목록을 찾을 수 없습니다.")
                return []
            
            # 처음 10개의 영화만 처리
            movies = movies[:self.movie_count]
            print(f"처리할 영화 수: {len(movies)}개")
            
            # 먼저 모든 영화의 기본 정보를 수집
            movie_info_list = []
            for idx, movie in enumerate(movies, 1):
                movie_info = self._get_movie_info(movie)
                
                if movie_info:
                    movie_info.comment_info = self._create_comment_info(movie_info.movie_link)
                    movie_info_list.append(movie_info)
                    
            return movie_info_list
            
        finally:
            driver.quit()

    def _close_popup(self, driver):
        try:
            wait = WebDriverWait(driver,2)
            close_buttons = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button.tG3uDBku"))
            )
            for button in close_buttons:
                if button.text.strip() == "닫기":
                    button.click()
                    print("팝업창 닫기 성공")
                    break
        except Exception as e:
            print(f"팝업창 닫기 실패: {e}")

    def _get_driver_by_url(self, url):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # headless 모드 비활성화
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        return driver    

    def _delete_special_character(self, comment_list):
        try:
            for i in range(len(comment_list)):
                comment_list[i] = emoji.replace_emoji(comment_list[i], replace='')
            if not self._has_no_emoji(comment_list):
                raise Exception("이모지 제거 안됨")
            return comment_list
        except Exception as e:
            print(e)
            return []

    def _has_no_emoji(self, comment_list):
        for comment in comment_list:
            if emoji.emoji_count(comment) > 0:
                print("emoji 있음")
                return False
        
        return True

# 실행
if __name__ == "__main__":
    crawler = MovieCrawling()
    _ = crawler.start(10)



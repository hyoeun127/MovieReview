from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class ReviewController:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.base_url = "https://pedia.watcha.com/ko-KR/?domain=movie"
        
    def get_box_office_top5(self):
        try:
            # Chrome 옵션 설정
            self.driver.get(self.base_url)
            
            wait = WebDriverWait(self.driver,5)
            
            close_button = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,"button.a3VOQo6v.Fxip6vYZ.bmNDNA_p")))
            close_button.click()
            
            wait = WebDriverWait(self.driver, 5)
            movie_list = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,"li.zK9dEEA5.w_exposed_cell")))
            # 상위 5개 영화 제목 추출
            movie_titles = []
            for movie in movie_list[:5]:
                try:
                    title = movie.find_element(By.CSS_SELECTOR,"div.WWPgNOuc.KYbG4TeN").text
                    stats = movie.find_element(By.CSS_SELECTOR, "div.VWL8zgFg.RiDHrQhO").text
                    
                    movie_titles.append({'title':title, 'stats':stats})
                except Exception as e:
                    print(f"오류 : {e}")
                
            self.driver.quit()
            return movie_titles
            
        except Exception as e:
            print(f"크롤링 중 오류 발생: {str(e)}")
            return []
        finally:
            self.driver.quit()
        
    
if __name__ == "__main__":
    review_controller = ReviewController()
    top5_movies = review_controller.get_box_office_top5()
    print(top5_movies)

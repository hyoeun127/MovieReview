import requests
from bs4 import BeautifulSoup
import json

class ReviewCrawling:
    def __init__(self):
        self.base_url = "https://pedia.watcha.com/ko-KR/?domain=movie"
        
    def get_box_office_top5(self):
        try:
            # 웹 페이지 요청
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.base_url, headers=headers)
            response.raise_for_status()
            
            # BeautifulSoup 객체 생성
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 박스오피스 순위 영화 찾기
            movies = []
            box_office_items = soup.find_all('div', class_='css-1g3q3h1')
            
            # 상위 5개 영화만 추출
            for item in box_office_items[:5]:
                title = item.find('div', class_='css-1g3q3h1').text.strip()
                movies.append(title)
            
            print(len(movies))
            
            return movies
            
        except Exception as e:
            print(f"크롤링 중 오류 발생: {str(e)}")
            return []
        
    
if __name__ == "__main__":
    ReviewCrawling().get_box_office_top5()

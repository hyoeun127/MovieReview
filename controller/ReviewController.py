from selenium.webdriver.common.by import By

class ReviewController:
    def __init__(self):
        print("ReviewController 초기화")

    def get_box_office_top5(self):
        try:
            # ... 기존 크롤링 코드 ...
            
            movie_titles = []
            for movie in movie_list[:5]:
                try:
                    title = movie.find_element(By.CSS_SELECTOR,"div.WWPgNOuc.KYbG4TeN").text
                    stats = movie.find_element(By.CSS_SELECTOR, "div.VWL8zgFg.RiDHrQhO").text
                    
                    # stats 문자열 분리
                    stats_parts = stats.split('•')
                    audience_count = ''
                    reservation_rate = ''
                    opening_day = ''
                    
                    for part in stats_parts:
                        part = part.strip()
                        if '관객' in part:
                            audience_count = part
                        elif '예매율' in part:
                            reservation_rate = part
                        elif '개봉' in part:
                            opening_day = part
                    
                    movie_titles.append({
                        'title': title,
                        'audience_count': audience_count,
                        'reservation_rate': reservation_rate,
                        'opening_day': opening_day
                    })
                except Exception as e:
                    print(f"오류 : {e}")

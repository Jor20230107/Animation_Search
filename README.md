# Animation 검색 시스템

## 검색 시스템

elastic search 검색 시스템

### 기능
- Watching, Top-rated list 제공
- prefix 검색
  - name, genre[nested]
- Semantic Search
  - prefix 검색 결과가 없거나 2개 이상일 때 -> 검색어 기반
  - prefix 검색 결과가 1개 있을 때 -> 결과 item의 synopsis 기반
- Watched list는 모든 검색, 추천에서 제외

## Simple 개인화 추천
- user의 max rating animation의 synopsis 기반


## Dataset

캐글 **Anime Recommendation Database 2020** 활용  
[Anime Recommendation Database 2020](https://www.kaggle.com/datasets/hernan4444/anime-recommendation-database-2020?resource=download&select=rating_complete.csv)

GitHub repo  
[MyAnimeList-Database](https://github.com/Hernan4444/MyAnimeList-Database)

## 향후 추가 개발 가능 요소
- 띄어쓰기도 반영하는 검색
- 추천 모델링
- html 링크를 통해 검색 결과에 animation 표지 제공
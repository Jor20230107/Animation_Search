# Recommender

### 추천 알고리즘

- 나와 비슷한 사람이 좋아한 작품을 추천한다
  - 개인화 추천
  - 나에 대한 정보가 필요
  - 나와 비슷한 사람을 정의해야 하고
    - 룰 기반이든
    - 클러스터링이든
    - 다른 방법도 있나?
  - 좋아한
    - High rating
    - 오랫동안 즐겼거나
      - 편수 중에 대다수 편수
        - 대다수 기준?
      - 1편이라면 몇 %까지 봤는가
    - (상품이라면) 구매를 했거나
    - (상품 중 소모품이라면) 재구매를 했거나
    - (상품인데 가격이 올랐음에도) 재구매를 했거나
- 그런데 추천이 도움이 되나? → 평가계
  - 구매 전환율
  - 실제 시청 전환율
- 내가 좋아한 작품과 비슷한 작품을 추천한다
  - 개인이 좋아하는 ‘장르’라는 차원이 존재한다
- 인기가 많은 작품을 추천한다
  - 기본적으로는 개인화가 아니지만, 섞을 수는 있다.
  - Top 10
  - 인기순으로 나열 방식으로 표현
    - 구매량 순
    - 추천 순
    - 최신 순
      - 최신일수록 좋은 건가?
      - New이기는 하잖?
    - 이미 시청한 작품은 제외?
      - 완전히 다 봤는지

### 작업 순서

1. Web 화면, 미리보기 서버 설계
    - 메인 화면
        - All-Time/1m
            - Top rated
            - Top watched
            - 장르별 Top
        - 출시 최신 1개월
    - 로그인 (user 선택)
2. 추천 알고리즘? 로직? 후보 List up
3. 데이터 탐색 및 추천 로직 확정
4. 추천 로직 구현

### 검색 시스템

- 타겟 검색
- 검색어 기반 추천

### User 기반 추천

캐글 **Anime Recommendation Database 2020** 활용  
[Anime Recommendation Database 2020](https://www.kaggle.com/datasets/hernan4444/anime-recommendation-database-2020?resource=download&select=rating_complete.csv)

GitHub repo  
[MyAnimeList-Database](https://github.com/Hernan4444/MyAnimeList-Database)

아예 넷플릭스 화면을 만들어야겠는데?

코딩애플에서 봤던 반짝이고 왔다갔다 하는 것도 보고

- DB가 필요할 듯
  - Elasticsearch
    - 실시간 검색어
    - 추천 검색어
    - 오타 교정
- 이건 나중에 하자
- 아직 DB를 활용하는 게 다가오지 않는다

생각보다 자세히 들여다봐야 할 컬럼이 많다.

머엉 해진다.

하나의 컬럼마다 분석이 필요함

다른 사람에게 보여줄 것처럼 작성해야 할 듯

animelist.csv는 1억 행...

user_id는 unique 325770

rating은 5700만

elastic search를 써보기로!
색인에 대해서 제대로 이해는 못했지만 써보자
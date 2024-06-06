### 2024-06-06

- ALS, Pyspark 서칭 및 도입 검토
    - pyspark는 애초에 hivesql을 db로 쓸때 활용도가 높을 것 같은데.. sql 쿼리를 위해 써야하나?
    - 단순히 pyspark를 써서 더 빠른지..? 의문
    - ALS 전에 일단 user*item 행렬을 만드는 것 자체가 문제
        - ALS 확인해보니 gradient descend와 대비되는 개념이었고..
        - 결국 matrix factorization이었
    - colab에서 무료로 12.7GB RAM을 제공하는데, 이걸로 안될까?
    - 로컬은 16GB여도 다른게 많이 잡아먹으니까..
    - 해당 행렬이 필요없는 추천로직이나 모델 검토?
- 행렬 만드는거 colab에서 해보고 안되면 npc 설계로 넘어가
    - 안됨. session이 끊김.
    - 애초에 이정도면 matrix factorization도 구현 불가능할 것으로 보임
    - 현 컴퓨팅 파워 환경에서는 여기서 1차 마감하는 것으로

### 2024-06-02

- 추천 모델
    - matrix factorization을 구현하려고 했는데, 해당 Table을 만드는 것 자체가 쉽지 않음
        - 메모리가 계속해서 터짐
        - 현재까지 dataframe을 이용했는데,
        - 어차피 index를 이용하면 되니, numpy나 tensor를 쓰는게 나을듯
        - 0과 NaN을 분명히 구분해야한다.
        - 메모리 계산을 한번 해보자
        - user가 약 350000이라고 해보고, item이 한 48000 이었으니, 50000이라 해보고
        - 그럼 곱하면, 17500000000인데, 각 element가 int 8bit라 해보면, 140000000000 bit
        - = 17.5GB, 16bit라 하면 35GB, 64bit라 하면 140GB
        - 너무 크긴하다.
        - pc RAM이 16GB.
        - Deeplearning 할때는 보통 32bit이니..
        - 이러면 안되겠는데?
        - numpy로 일단 시도해보고..
        - 그런데 이렇게 큰 행렬이 반드시 필요한가..?
        - 일단 numpy로 저장은 가능
        - np.zeros로 햇는데 이러면 nan과 0점 구분이 안되서 추후 수정 필요
    - modeling 방법론에 대해 좀더 공부할 필요.
        - 응 교수님 강의를 좀더 들어보자
        - matrix factorization은 layer가 한 개인 NN아닌가?
    - 나랑 비슷한 사람이 좋아한 작품 추천 방식
        - 비슷한 사람. clustering
            - user를 index로 한 현 matrix factorization 행렬에서 clustering을 적용
                - 메모리 괜찮을까?
            - 소속 cluster내에서 anime_id별 평점 평균을 구함
            - 평점 평균을 기준으로 descending sorting하고 이미 본 것, 보고 있는 것 제외하고 추천
    - 내가 좋아한 작품과 유사한 작품 추천 방식
        - 이건 쉽게 구현이 가능할 것 같음
        - user 상위 rating 작품 1개를 가져와서
            - 같은 최상위 rating 중 어떤 작품?
            - 이것조차 너무 크긴하다..
            - model 가져오기 전에.. 해야함.
            - mmap_mode로 성공
        - 걔랑 닮은 작품 가져와서 보여주기
            1. synopsis 기준 vector embedding으로
                1. 이걸로 진행함
            2. 장르 값으로 할수도 있고
        - 중복, 이미 본 것 등 제거
            - 함수화하고 적용했는데, 어쩐일인지 검색 엔드포인트에서는 적용이 되고 main 추천에서는 안됨
            - 추후 확인 필요
- 결과
    - 내가 좋아한 작품과 유사한 작품 추천 방식 : 적용
    - html 문구 일부 수정

### 2024-06-01

- 신규 index 생성
    - animelist
    - rating complete
- 추천 모델
    - elastic search를 통한 로직 구현
        - currently watching list
            - animelist에서 뽑아온다
        - Complete list 뽑아와서 추천로직에서 제외
        - 
    - ML
        - Content-based recommendation
        - Collaborative Filtering
            - 기대하는 학습데이터의 형태가 animelist와 rating complete의 combine 형태임
            - 어차피 모델학습이 이뤄지고나면, 주기단위로 관리하면됨
            - 전처리를 통해  학습 테이블을 만들고, 그 코드를 스케쥴링
- 용량과 효율성의 문제를 고려못함
    - 이후 활용을 고려하더라도 현 animelist (1.9GB)를 통으로 index화 할 필요는 없었음
    - 차라리 전처리를 통해서
    - user_id watchinglist watchedlist로 table을 갖고있는게 낫다

- 결과
    - animelist 전처리로 watching, complete list만 별도 추출 → csv로 저장
    - current_user_id에 따른 watching, complete list 생성
    - watchinglist를 보여주고, 추천, 검색 list에서 complete, watchinglist는 제외 로직 적용

### 2024-05-27

- 개발 기획
    - 개인화 추천, 검색을 위한 신규 index 생성
        - animelist
        - rating complete
    - 화면 반영
        - user id 선택 기능
    - 신규 로직 반영
        - currently watching list
            - 시간 정보는 없음 sorting 무슨 순서로?
        - On Hold list
        - Plan to Watch
        - 추천, 검색에서 Completed list 제외
- ML 추천 모델 고민


### 2024-05-26

- 벡터검색을 별도로 작업을 했으나,
- 검색창을 일원화 할 필요가 있음
- 내용으로 검색을 할 수 있다는 점은 분명히 강점이나, 아래와 같이 로직, 화면을 재구성할 필요

- 넷플릭스 기준으로 검색기능은
    1. 이름으로 검색
        1. 대상이 확정되면(1개만 남으면, exact matching?)
        2. 대상과 유사한 애들을 별도로 추천해줌
            1. ex) 검색하신 작품과 유사한 작품
    2. 1개만 남지 않는다면, 이름, 장르검색 기록을 보여주고
    3. 동시에 semantic search로 나온 검색결과를 별도로 ‘추천’작품으로 보여줌
    4. 이름을 통한 검색결과가 없을 경우,
        1. 내용 검색 결과를 보여줌
            1. 관련있는 작품
            2. 이때 내용 검색이 바로 검색어와 벡터검색을 실행하는 것이 아닌,
            3. 해당 플랫폼에서 제공하지 않는 작품일지라도, 일단 검색을 하고,
            4. 제공하지 않는경우 표시를 하지않고, 해당 작품과 유사한 작품을 보여주는것도 하나의 방법(넷플릭스가 그런 것 같은데?)
- 위 로직으로 구현을 바꿔보자
- 결과 : 성공
    - 하지만 원래는 redirection 활용하려 했으나, 추가 벡터검색만 화면에 전시되어,
    - 백엔드에서 로직을 구현하는 방향으로 선회함

- 이후
    - 꾸미기 작업에 돌입해보자
        - 카드 형태로 animation 그림 제공
        - 커서에 따라 반응하는 그림 효과. 코딩 애플에서 본 것.

### 2024-05-25

지난 추가작업으로

- semantic search 검색창 추가
    - 별도 검색창
    - text 임베딩
        - synopsis 전처리
        - model 선정 : e5
            - why?
                - 유명해서,
                - 생각보다 가벼워서
            - input_size : 512
            - vector_size : 768
        - synopsis가 비어있고, score도 없는 animation은 index의 삭제하고자, index를 삭제 후 재생성함.
        - 현 index 약 10000라인
        - index 신규 생성시 약 30분 소요
    - cosine similarity 계산 기능

### 2024-05-19

구글도 신이지만

chatgpt도 신이다

- elastic search 도입에 어려움을 겪고있음
- db가 안켜져

- genre를 위한 nested구조는 포기함
- helpers.bulk로 index 데이터 넣는데 성공함
- 간단 html 템플릿으로 구현 성공
    - 메인페이지 접속시 Top rated animations를 가져와서 보여주고
    - 검색창에서 name 기준으로 검색한 animation을 가져와서 보여줌

- 디자인은 나중에 작업하고
    - 메인사진 가져오기
- 이후 추가작업으로
    - 검색창에 치면 es 검색결과를 보여주고
    - 내용 검색으로 결과를 animation 검색 결과를 보여주자
        - 별도 검색창으로 만들었다가 합치자
        - text 임베딩이 필요함
        - cosine similarity 계산 기능이 필요함
    - 현재 인덱스를 계속 지웠다가 생성하는데 있으면 생성안하도록 바꿔야

2024-05-18

- fastapi 도입을 고민할 필요가 있다

추천 알고리즘

- 나와 비슷한 사람이 좋아한 작품을 추천한다
    - 개인화 추천
    - 나에 대한 정보가 필요
    - 나와 비슷한 사람을 정의해야하고
        - 룰 base던
        - clustering이던
        - 다른 방법도 있나?
    - 좋아한
        - high rating
        - 오랫동안 즐겼거나
            - 편수중에 대다수 편수
                - 대다수 기준?
            - 1편이라면 몇%까지 봤는가
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
    - 인기순으로 나열방식으로 표현
        - 구매량 순
        - 추천 순
        - 최신 순
            - 최신일수록 좋은건가?
            - New이기는 하잖?
        - 이미 시청한 작품은 제외?
            - 완전히 다 봤는지
            

작업순서

- Web 화면, 미리보기 서버 설계
    - 메인화면
        - All-Time/1m
            - Top rated
            - Top watched
            - genre별 top
        - 출시 최신 1month
    - 로그인(user 선택)
- 추천알고리즘?로직? 후보 listup
- 데이터 탐색 및 추천로직 확정
- 추천로직 구현

검색시스템

- target 검색
- 검색어 기반 추천

User기반 추천

캐글 **Anime Recommendation Database 2020 활용**

https://www.kaggle.com/datasets/hernan4444/anime-recommendation-database-2020?resource=download&select=rating_complete.csv

github repo

https://github.com/Hernan4444/MyAnimeList-Database

아예 넷플릭스 화면을 만들어야겠는데?

코딩애플에서봤던 반짝이고 왔다갔다하는것도보고

- DB가 필요할듯
    - elastic search
        - 실시간 검색어
        - 추천 검색어
        - 오타교정
- 이건 나중에 하자
- 아직 DB를 활용하는게 다가오지 않는다

생각보다 자세히 들여다봐야할 칼럼이 많다.

머엉 해진다.

하나의 칼럼마다 분석이 필요함

다른사람에게 보여줄 것처럼 작성해야할듯

animelist.csv는 1억행..

user_id는 unique 325770

rating은 57백만

2024-05-12

애초에 본 기획의 목적은 github에 내가 ml을 웹으로 구현햇다는 것을 보여주는 것이었다.

여기서 어떤 언어, 웹프레임워크를 기반으로 해야할지 이러지도 저러지도 못하고있었는데, 일단은 간단하게 시작하는게 역시 맞는 것 같다. DB고 뭐고 다 복잡하니, 일단은 Flask로 로컬서버실행하는 방식으로 구현해보자(어차피 서비스 다만들고 서버에 올려서 계속 둘 것은 아니잖아?)

chatgpt의 도움을 받아 기초 html 문서와 로컬서버 실행을 위한 app.py를 만들었다.

이제 구체적으로 어떤 모델을 만들지 기획이 필요한 시점

- 데이터 탐색과 모델 고민이 같이 이루어져야한다.
    - 마땅한 샘플 데이터가 없으면 구상한 모델링도 구현이 불가할 것
    - 데이터는 캐글로 하자
    - 내가 원하는 컬럼을 갖고있는지 확인이 필요하다
- 임베딩 모델은 성능이 떨어지더라도 api보다는 돈안드는 small 모델을 가져오자
- 상품 임베딩을 위해 최대한 큰 상품정보 데이터가 필요하겠다.
- ms단위의 속도 측정이 필요하다
    - 다른 사람들은 어떻게 하나?
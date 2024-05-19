from fastapi import FastAPI, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from elasticsearch import Elasticsearch, helpers
import pandas as pd
import json

app = FastAPI()

# 템플릿 디렉토리 설정
templates = Jinja2Templates(directory="templates")

# 정적 파일 설정 (CSS, JS 등)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Elasticsearch 연결
es = Elasticsearch([{'host': 'localhost', 'port': 9200,'scheme' : 'http' }],
                   http_auth=('elastic','sRLpWutPELlL2mg23CAx'),
                   verify_certs=False)

# 애니메이션 데이터
animations  = pd.read_csv('D:/WebML/Recommender/data/anime_smpl.csv')

# ElasticSearch 인덱스 이름
index_name = 'your_index_name'

# 인덱스가 존재하는지 확인하고 존재하지 않으면 생성
if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)
    es.indices.create(index=index_name)

    # 데이터를 ElasticSearch에 인덱싱할 형식으로 변환
    def generate_elastic_data(df):
        for index, row in df.iterrows():
            # 각 row를 JSON 형식으로 변환
            doc = row.to_dict()
            # yield를 사용하여 데이터를 한 번에 메모리에 적재하지 않도록 함
            yield {
                "_index": index_name,
                "_source": doc
            }

    # ElasticSearch에 데이터 로드
    helpers.bulk(es, generate_elastic_data(animations))

# 메인 페이지
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # 추천 애니메이션 가져오기
    es_result = es.search(index=index_name, body={"query": {"match_all": {}}})
    hits = es_result["hits"]["hits"]
    animations = [{"Name": hit["_source"]["Name"],"Genres": hit["_source"]["Genres"], "Score": hit["_source"]["Score"]} for hit in hits]
    recommended = sorted(animations, key=lambda x: x['Score'], reverse=True)[:5]
    return templates.TemplateResponse("index.html", {"request": request, "recommended": recommended})

# 애니메이션 검색 엔드포인트
@app.get("/search", response_class=HTMLResponse)
async def search_animation(request: Request, query: str = Query(None, min_length=1)):
    if query:
        # Elasticsearch 쿼리
        es_query = {
            "query": {
                "match": {                
                    "Name": query
                }
            }
        }
        # Elasticsearch로 검색
        es_result = es.search(index=index_name, body=es_query)
        hits = es_result["hits"]["hits"]
        results = [{"Name": hit["_source"]["Name"],"Genres": hit["_source"]["Genres"], "Score": hit["_source"]["Score"]} for hit in hits]
    else:
        results = []
    return templates.TemplateResponse("search_results.html", {"request": request, "results": results})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
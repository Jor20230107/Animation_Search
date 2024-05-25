from fastapi import FastAPI, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from elasticsearch import Elasticsearch, helpers
import pandas as pd
import numpy as np
import json
from transformers import AutoModel, AutoTokenizer
import torch
import time

app = FastAPI()

# 템플릿 디렉토리 설정
templates = Jinja2Templates(directory="templates")

# 정적 파일 설정 (CSS, JS 등)
app.mount("/static", StaticFiles(directory="static"), name="static")

from dotenv import load_dotenv
import os

# .env 파일로부터 환경 변수 로드
load_dotenv()

# Elasticsearch 연결
es_host = 'localhost'
es_port = 9200
es_scheme = 'http'
es_username = os.getenv('ELASTIC_USERNAME')
es_password = os.getenv('ELASTIC_PASSWORD')

es = Elasticsearch(
    [{'host': es_host, 'port': es_port, 'scheme': es_scheme}],
    http_auth=(es_username, es_password),
    verify_certs=False
)

# 애니메이션 데이터
animations  = pd.read_csv('D:/WebML/Recommender/data/anime_synopsys.csv')

index_name = 'animations_index'
# es.indices.delete(index=index_name)
# E5 모델 및 토크나이저 로드
model_name = "intfloat/e5-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

def get_text_embedding(text):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

# Elasticsearch에 애니메이션 인덱스 생성 및 데이터 색인화
# 인덱스가 존재하는지 확인하고 존재하지 않으면 생성

if es.indices.exists(index=index_name):
    print(f'# {index_name} index 정상 확인' )
else:
    print(f'# {index_name} index 미확인. index 재생성 시작' )
    # es.indices.delete(index=index_name)
    es.indices.create(index=index_name, body={
        "mappings": {
            "properties": {
                "Name": {"type": "text"},
                "Genres": {"type": "nested", "properties": {"name": {"type": "text"}}},
                "Score": {"type": "float"},
                "Embeddings": {
                "type": "dense_vector",
                "dims": 768 
            }
            }
        }
    })
    
    print(model)

    # memory 폭파 우려로 for문 처리
    print('index용 embedding 작업 시작')
    print(f'# {len(animations)}개의 synopsis 작업중..')
    start_time = time.time()
    iterations = []
    for i in animations['synopsis']:
        embeds = get_text_embedding(i)
        iterations.append(embeds)
    animations['text_vector'] = iterations
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution Time (PyTorch): {execution_time:.4f} seconds")

    # 데이터를 ElasticSearch에 인덱싱할 형식으로 변환
    def generate_elastic_data(df):
        for index, row in df.iterrows():
            # 각 row를 JSON 형식으로 변환
            doc = row.to_dict()
            Genres = [{"name": genre.strip()} for genre in row['Genres'].split(",")]
            doc = {
                "Name" : row['Name'],
                "Genres" : Genres,
                "Score" : row['Score'],
                "Embeddings" : row['text_vector']
            }
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
                "bool": {
                    "should": [
                        {"prefix": {"Name": query}},
                        {"nested": {
                            "path": "Genres",
                            "query": {
                                "bool": {
                                    "should": [
                                        {"prefix": {"Genres.name": query}}
                                    ]
                                }
                            }
                        }}
                    ]
                }
            }
        }
        # Elasticsearch로 검색
        es_result = es.search(index=index_name, body=es_query)
        hits = es_result["hits"]["hits"]
        results = [{"Name": hit["_source"]["Name"],"Genres": hit["_source"]["Genres"], "Score": hit["_source"]["Score"]} for hit in hits]
        results = sorted(results, key=lambda x: x['Score'], reverse=True)[:5]
    else:
        results = []
    return templates.TemplateResponse("search_results.html", {"request": request, "results": results})

# Elasticsearch 벡터 검색을 위한 엔드포인트
@app.get("/vector_search", response_class=HTMLResponse)
async def vector_search_animation(request: Request, query: str = Query(None, min_length=1)):
    if query:
        # 입력된 쿼리에 대한 벡터 생성
        query_embedding = get_text_embedding(query)
        # Elasticsearch 벡터 검색 쿼리 생성
        es_vector_query = {
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'Embeddings') + 1.0",
                        "params": {"query_vector": query_embedding.tolist()}
                    }
                }
            }
        }
        # Elasticsearch로 검색
        es_result = es.search(index=index_name, body=es_vector_query)
        hits = es_result["hits"]["hits"]
        results = [{"Name": hit["_source"]["Name"], "Score": hit["_source"]["Score"]} for hit in hits]
    else:
        results = []
    return templates.TemplateResponse("vector_search_results.html", {"request": request, "results": results})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
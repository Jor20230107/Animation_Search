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

# current user 기준 get top anime, watchinglist, completelist 
# rating_matrix의 용량이 커서 embedding model load 전에 실행
current_user_id = 0

def get_top_anime(this_user_id):
    # print("터질지도 모릅니다.")
    import numpy as np
    ratings_matrix = np.load('D:/WebML/Recommender/data/ratings_matrix.npy', mmap_mode='r')    
    top_anime = np.argmax(ratings_matrix[this_user_id])
    # print("다행히 안터졌습니다.")
    
    return top_anime    
    
    

current_user_top_anime = get_top_anime(current_user_id)
# print(current_user_top_anime)

""" watching_status
1   Currently Watching
2   Completed
3   On Hold
4   Dropped
5   Plan to Watch
"""

def search_status(this_user_id):    
    animelist = pd.read_csv('D:/WebML/Recommender/data/wc_list.csv')    
    Myanimelist = animelist[animelist['user_id']==this_user_id]
    watching = Myanimelist['watching'].iloc[0].split(',')
    watched = Myanimelist['completed'].iloc[0].split(',')
    return watching, watched

current_user_watching_list, current_user_complete_list = search_status(current_user_id)
all_list = list(set(current_user_complete_list + current_user_watching_list))

# embedding model load 및 animations_index 생성
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
                "anime_id": {"type": "integer"},
                "Name": {"type": "text"},
                "Genres": {"type": "nested", "properties": {"name": {"type": "text"}}},
                "Score": {"type": "float"},
                "Synopsis" : {"type": "text"},
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
    # 애니메이션 데이터
    animations  = pd.read_csv('D:/WebML/Recommender/data/anime_synopsys.csv')
    print(f'# {len(animations)}개의 synopsis 작업중..')
    start_time = time.time()
    iterations = []
    for count, i in enumerate(animations['synopsis']):
        embeds = get_text_embedding(i)
        iterations.append(embeds)
        if(len(animations)/4 == count):
            print('--1/4 done--')
        elif(len(animations)/2 == count):
            print('--half done--')
        elif(3*len(animations)/2 == count):
            print('--3/4 done--')
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
                "anime_id" : row['anime_id'],
                "Name" : row['Name'],
                "Genres" : Genres,
                "Score" : row['Score'],
                "Synopsis" : row['synopsis'],
                "Embeddings" : row['text_vector']
            }
            # yield를 사용하여 데이터를 한 번에 메모리에 적재하지 않도록 함
            yield {
                "_index": index_name,
                "_source": doc
            }
    
    # ElasticSearch에 데이터 로드
    helpers.bulk(es, generate_elastic_data(animations), chunk_size=100, request_timeout=200)


def vector_search(embeddings):
    query_embedding = embeddings
    # Elasticsearch 벡터 검색 쿼리 생성
    es_vector_query = {
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'Embeddings') + 1.0",
                            "params": {"query_vector": query_embedding}
                        }
                    }
                }
            }
            # Elasticsearch로 검색
    vector_es_result = es.search(index=index_name, body=es_vector_query)
    v_hits = vector_es_result["hits"]["hits"]
    v_results = [{"Name": hit["_source"]["Name"],"Genres": hit["_source"]["Genres"], "Score": hit["_source"]["Score"]} for hit in v_hits]
    v_results = v_results[:5]
    return v_results

def del_watching(results):
    filtered = []
    for result in results:
        if str(result.get('anime_id')) not in all_list:
            filtered.append(result)
    mylist = sorted(filtered, key=lambda x: x['Score'], reverse=True)[:5]
    return mylist
    


# 메인 페이지
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    
    # show top rated
    print(index_name)
    es_result = es.search(index=index_name, body={"query": {"match_all": {}}})
    hits = es_result["hits"]["hits"]
    animations = [{"anime_id": hit["_source"]["anime_id"],"Name": hit["_source"]["Name"],"Genres": hit["_source"]["Genres"], "Score": hit["_source"]["Score"]} for hit in hits]    
    # 이미 본것 제거
    recommended = del_watching(animations)
    
    # show watching list 
    es_query = {
        "query":{
            "bool":{
                "must":{
                    "terms":{
                        "anime_id":current_user_watching_list
                    }
                }
            }
        }
    }
    watching_result = es.search(index=index_name, body=es_query)
    w_hits = watching_result["hits"]["hits"]    
    watching = [{"anime_id": hit["_source"]["anime_id"],"Name": hit["_source"]["Name"],"Genres": hit["_source"]["Genres"], "Score": hit["_source"]["Score"]} for hit in w_hits]
    watching = sorted(watching, key=lambda x: x['Score'], reverse=True)[:5]

    # show like my top anime
    # 1. get my top anime name, vector
    name_query = {
        "query":{
            "bool":{
                "must":{
                    "terms":{
                        "anime_id": [current_user_top_anime]
                    }
                }
            }
        }
    }
    top_result = es.search(index=index_name, body=name_query)    
    t_hits = top_result["hits"]["hits"]
    top_anime_name = t_hits[0]["_source"]["Name"]
    top_embeddings = t_hits[0]["_source"]["Embeddings"]

    # 2. get top-like animes : vector search
    searched = vector_search(top_embeddings)
    # 이미 본것 제거
    top_likes = del_watching(searched)

    return templates.TemplateResponse("index.html", {"request": request, 
                                                     "recommended": recommended, 
                                                     "watching": watching, 
                                                     "user_id":current_user_id,
                                                     "top_anime" : top_anime_name,
                                                     "top_likes" : top_likes
                                                     })

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
        results = [{"anime_id": hit["_source"]["anime_id"],"Name": hit["_source"]["Name"],"Genres": hit["_source"]["Genres"], "Score": hit["_source"]["Score"], "Embeddings": hit["_source"]["Embeddings"] } for hit in hits]
        # 이미 본 것 제거
        filtered = del_watching(results)
        
        if len(filtered)==1:            
            query_embedding = results[0]['Embeddings']
            v_results = vector_search(query_embedding)
            my_title = '검색하신 작품과 유사한 작품 (Semantic Search)'
        else:
            query_embedding = get_text_embedding(query)
            v_results = vector_search(query_embedding)
            my_title = '검색어와 유사한 작품 (Semantic Search)'                    
    else:
        results = []
    return templates.TemplateResponse("search_results.html", {"request": request, "results": filtered, "v_results":v_results, "my_title" : my_title})


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
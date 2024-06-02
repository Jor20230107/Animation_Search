import numpy as np
import pandas as pd

# CSV 파일을 청크 단위로 읽어서 처리
chunk_size = 10**6  # 1백만 행 단위로 청크 읽기
filename = 'D:/WebML/Recommender/data/animelist.csv' 

# 최대 user_id와 anime_id 찾기
max_user_id = 0
max_anime_id = 0

# 파일의 모든 청크를 읽으면서 최대값 찾기
for chunk in pd.read_csv(filename, chunksize=chunk_size):
    max_user_id = max(max_user_id, chunk['user_id'].max())
    max_anime_id = max(max_anime_id, chunk['anime_id'].max())

# 최대값에 맞추어 행렬 초기화
ratings_matrix = np.zeros((max_user_id + 1, max_anime_id + 1), dtype=np.int8)

# 파일의 모든 청크를 다시 읽으면서 행렬 채우기
for chunk in pd.read_csv(filename, chunksize=chunk_size):
    for row in chunk.itertuples(index=False):
        ratings_matrix[row.user_id, row.anime_id] = row.rating

# 행렬을 파일로 저장 (예: .npy 형식으로 저장)
np.save('D:/WebML/Recommender/data/ratings_matrix.npy', ratings_matrix)

print("2차원 행렬 저장 완료.")

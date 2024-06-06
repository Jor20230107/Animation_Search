import numpy as np
import pandas as pd
import csv

max_user_id = 0
max_anime_id = 0

df = pd.read_csv('D:/WebML/Recommender/data/animelist.csv')
max_user_id = max(df['user_id'])
print(max_user_id)
max_anime_id = max(df['anime_id'])
print(max_anime_id)

# f = open("D:/WebML/Recommender/data/animelist.csv","r")
# reader = csv.reader(f)

# # 최대값에 맞추어 행렬 초기화
# ratings_matrix = np.full((max_user_id + 1, max_anime_id + 1), -1,dtype=np.int8)

# for row in reader:
#     if(row[0]!=int):
#        pass
#     x = row[0]
#     y = row[1]
#     value = row[2]
#     ratings_matrix[x][y] = value

# np.save('D:/WebML/Recommender/data/ratings_matrix.npy', ratings_matrix)

# print("2차원 행렬 저장 완료.")
# numpy.core._exceptions.MemoryError: Unable to allocate 833. MiB for an array with shape (109224747,) and data type int64
from flask import Flask, render_template, request

app = Flask(__name__)

# 사용자 ID 목록
users = ['person01', 'person02']

# 홈페이지 라우트
@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        # 폼에서 선택된 사용자 ID를 가져옵니다.
        selected_user = request.form.get('user')

        # 선택된 사용자 ID를 이용하여 작업을 수행합니다.
        # 추천 서비스를 여기에 구현

        return render_template('search_results.html', user=selected_user)
    
    return render_template('index.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)

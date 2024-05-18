from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

app = FastAPI()

# 사용자 ID 목록
users = ['person01', 'person02']

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "users": users})

@app.post("/", response_class=HTMLResponse)
async def handle_form(request: Request, user: str = Form(...), search_text: str = Form(...)):
    return templates.TemplateResponse("search_results.html", {"request": request, "user": user, "search_text": search_text})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
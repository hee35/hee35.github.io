from fastapi import FastAPI, Form, Request, Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import boto3
import json

def invoke_model(model_id: str, user_text: str, prompt_type: str, chat_history_str: str) -> str:
    # Prompt를 prompt_type에 따라 정의
    global system_prompt
    if prompt_type == "friend":
      system_prompt = """대화 지침: 국민대학교 경영정보학과 선배 역할을 시작하라. 사용자는 경영정보학과 재학중인 후배이다. 친근하게 반말을 사용하여 대화하라. 모르는 것을 알기 쉽게 풀어서 설명해주고 고민이 있다면 들어주어라."""
      user_prompt = f"""사용자: {user_text}"""

    else:
      system_prompt = """대화 지침: 국민대학교 학사 전문가 역할을 시작하라. 확인되지 않거나 모호한 부분은 모른다고 대답하라. 답변은 출처의 링크와 함께 전달하고 기준일자를 기재하여라. 확인이 필요한 부분이 있다면 물어보고 반영하여 답하라. 존댓말을 유지하라."""
      user_prompt = f"""사용자: {user_text}"""

    payload = {
      "anthropic_version": "bedrock-2023-05-31",
      "max_tokens": 1000,
      "messages": [
        {
          "role": "user",
          "content": system_prompt + user_prompt + chat_history_str
        }
      ]
    }

    try:
      # Bedrock API 호출
      response = bedrock_client.invoke_model(
          modelId=model_id,
          contentType='application/json',
          accept='application/json',
          body=json.dumps(payload)
      )
      # 응답 처리
      response_body = json.loads(response['body'].read())
      return response_body['content'][0]['text']  # 최종 응답 반환
    except Exception as e:
      print(f"[Error] {str(e)}")  # 로그 출력
      return "죄송합니다. 서버에서 오류가 발생했습니다. 나중에 다시 시도해 주세요."

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
chat_history = []  # 채팅 기록을 저장하는 리스트

# Bedrock 클라이언트 설정
bedrock_client = boto3.client(
  'bedrock-runtime',
  region_name='us-east-1'
)

#첫 화면
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
  return templates.TemplateResponse("index.html", {"request": request})

#모드 선택 화면
@app.get("/mode_select", response_class=HTMLResponse)
async def mode_select(request: Request):
  return templates.TemplateResponse("mode_select.html", {"request": request})

#채팅 화면
@app.get("/{prompt_type}", response_class=HTMLResponse)
async def prompt_type(request: Request, prompt_type: str):
  if prompt_type == "friend":
    return templates.TemplateResponse("friend.html", {"request": request, "prompt_type": prompt_type})
  elif prompt_type == "professional":
    return templates.TemplateResponse("professional.html", {"request": request, "prompt_type": prompt_type})
  else:
    return HTMLResponse("Invalid prompt_type", status_code=400)

@app.post("/{prompt_type}/chat", response_class=HTMLResponse)
async def chat(request: Request, user_input: str = Form(...), prompt_type: str = Path(...)):
  model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

  # 채팅 기록 딕셔너리를 문자열로 변환
  global chat_history_str
  chat_history_str = "\n".join(
      [f"{entry['type'].capitalize()}: {entry['content']}" for entry in chat_history]
  )

  response = invoke_model(model_id, user_input, prompt_type, chat_history_str)

  # 채팅 기록에 사용자 입력과 챗봇 응답 추가
  chat_history.append({"type": "user", "content": user_input})
  chat_history.append({"type": "chatbot", "content": response})

  return templates.TemplateResponse(f"{prompt_type}.html", {
      "request": request,
      "response": response,
      "user_input": user_input,
      "prompt_type": prompt_type,
      "chat_history": chat_history  # 갱신된 채팅 기록을 전달
  })

@app.post("/reset", response_class=HTMLResponse)
async def reset_chat(request: Request, prompt_type: str = Form(...)):
  chat_history.clear()  # 채팅 기록 초기화

  # 현재 prompt_type으로 리다이렉트
  redirect_url = f"/{prompt_type}"
  return RedirectResponse(url=redirect_url, status_code=303)  # 303 상태 코드로 리다이렉트

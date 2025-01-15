from fastapi import FastAPI, Form, Request, Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse 
import boto3
import json

def invoke_model(model_id: str, user_text: str, prompt_type: str) -> str:
    # Prompt를 prompt_type에 따라 정의
    global chef_prompt
    if prompt_type == "food":
        chef_prompt = """지금부터 저는 당신의 상황과 기호에 맞는 요리를 추천드리는 요리사입니다. 말씀을 듣고 연관되는 음식을 추천드리겠습니다. 노란색의 별점으로 추천도를 표현해 드릴게요."""
        user_prompt = f"""사용자: {user_text}"""

    elif prompt_type == "good":
        chef_prompt = """지금부터 저는 당신만을 위한 영양사입니다. 칼로리와 영양성분을 고려하여 균형 잡힌 식단을 추천드리겠습니다. 해당 식단을 추천하는 이유와 칼로리를 알려드리겠습니다. 노란색의 별점으로 추천도를 표현해 드릴게요. 추천은 다음과 같은 형식으로 드릴게요.
추천음식명(칼로리) 노란색별점 추천이유설명
총칼로리
식단 조정을 원하시면 반영하여 변경해드릴게요."""
        user_prompt = f"""사용자: {user_text}"""

    else:
        chef_prompt = """지금부터 저는 세계 각국의 다양한 음식을 모두 알고 있는 푸드 투어 가이드입니다. 생각해보지 못한 도전적인 음식을 추천해드리겠습니다. 추천 이유를 상세히 말씀드릴게요. 노란색의 별점으로 추천도를 표현해드릴게요. 추천은 다음과 같은 형식으로 드릴게요.
추천음식명(원어명) 노란색별점 추천이유설명
맘에 들지 않는 이유를 말씀해주시면 반영하여 다른 음식을 추천드릴게요"""
        user_prompt = f"""사용자: {user_text}"""

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": chef_prompt + "\n사용자 정보: " + user_data_str + "\n" + user_prompt + "\n사용자 이전 질문: " + user_chat_str + "\n이전 답변" + chatbot_responses_str
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
        return "죄송합니다. 음식 추천 중 오류가 발생했습니다. 다시 시도해 주세요."

app = FastAPI()
templates = Jinja2Templates(directory=".")
chat_history = []  # 채팅 기록을 저장하는 리스트
user_data = {} #사용자 정보
user_data_str = ""
chatbot_responses = [] #챗봇의 응답 저장
chatbot_responses_str = ""
user_chat = [] #유저의 응답 저장
user_chat_str = ""
chef_prompt = ""

# Bedrock 클라이언트 설정
bedrock_client = boto3.client(
    'bedrock-runtime',
    region_name='us-east-1'
)

#시작화면
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

#시작하기 누르고 정보입력 화면
@app.get("/info", response_class=HTMLResponse)
async def info(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})

@app.get("/start", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("start.html", {"request": request})

@app.get("/{prompt_type}", response_class=HTMLResponse)
async def index(request: Request, prompt_type: str):
    if prompt_type == "food":
        return templates.TemplateResponse("food.html", {"request": request, "prompt_type": prompt_type})
    elif prompt_type == "good":
        return templates.TemplateResponse("good.html", {"request": request, "prompt_type": prompt_type})
    elif prompt_type == "new":
        return templates.TemplateResponse("new.html", {"request": request, "prompt_type": prompt_type})
    else:
        return HTMLResponse("Invalid prompt_type", status_code=400)
    
@app.post("/{prompt_type}/chat", response_class=HTMLResponse)
async def chat(request: Request, user_input: str = Form(...), prompt_type: str = Path(...)):
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    # 채팅 기록을 문자열로 변환
    global user_chat_str
    user_chat_str = "\n".join(
        [f"{entry['type'].capitalize()}: {entry['content']}" for entry in chat_history]
    )
    global chatbot_responses_str
    chatbot_responses_str = "\n".join(
        [f"{entry['type'].capitalize()}: {entry['content']}" for entry in chat_history]
    )

    response = invoke_model(model_id, user_input, prompt_type)
    
    # 채팅 기록에 사용자 입력과 챗봇 응답 추가
    user_chat.append({"type": "user", "content": user_input})
    chatbot_responses.append({"type": "chatbot", "content": response})
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
    global chat_history
    chat_history.clear()  # 채팅 기록 초기화
    global chatbot_responses
    chatbot_responses.clear()
    global user_chat
    user_chat.clear()

    # 현재 prompt_type으로 리다이렉트
    redirect_url = f"/{prompt_type}"
    return RedirectResponse(url=redirect_url, status_code=303)  # 303 상태 코드로 리다이렉트

@app.post("/data", response_class=HTMLResponse)
async def reset_chat(request: Request, 
    name: str = Form(None),  # 기본값 None 설정
    age: str = Form(None), 
    gender: str = Form(None), 
    taste: str = Form(None), 
    mood: str = Form(None), 
    weather: str = Form(None), 
    temperature: str = Form(None)):

    global chat_history
    chat_history.clear()  # 새로운 사용자를 위한 채팅 기록 초기화
    global chatbot_responses
    chatbot_responses.clear()
    global user_chat
    user_chat.clear()

    global user_data
    user_data = {
        "name": name,
        "age": age,
        "gender": gender,
        "taste": taste,
        "mood": mood,
        "weather": weather,
        "temperature": temperature,
    }

    # user_data를 문자열로 변환
    global user_data_str
    user_data_str = ", ".join([f"{key}: {value}" for key, value in user_data.items()])
    
    # 사용자 데이터를 저장한 후, 저장된 데이터를 HTML 페이지로 표시
    return templates.TemplateResponse("data.html", {"request": request, "user_data": user_data})

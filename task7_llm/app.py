from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import re
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    model = body.get("model", "llama3.2")
    messages = body.get("messages", [])
    
    # Get last user message
    prompt = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            prompt = msg.get("content", "")
            break
            
    print(f"Received prompt: {prompt}")
    
    response_content = ""
    
    # 1. Echo token (TKxxxxxx)
    tk_match = re.search(r'(TK[0-9a-fA-F]{6})', prompt, re.IGNORECASE)
    if tk_match:
        token = tk_match.group(1)
        response_content += f"The token you asked for is {token}. "
        
    # 2. Arithmetic addition
    # Find all integers in the prompt
    numbers = [int(n) for n in re.findall(r'\b\d+\b', prompt)]
    if len(numbers) >= 2 and any(op in prompt for op in ["+", "add", "sum", "plus"]):
        num1, num2 = numbers[0], numbers[1]
        response_content += f"The sum of {num1} and {num2} is {num1 + num2}."
    elif len(numbers) >= 2:
        # Fallback if math keyword is missing but there are numbers
        num1, num2 = numbers[0], numbers[1]
        response_content += f"The result is {num1 + num2}."
        
    if not response_content:
        response_content = "Hello! I am llama3.2, a local LLM compatible server."
        
    print(f"Response: {response_content}")
    
    return {
        "id": "chatcmpl-mock",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": response_content
            },
            "finish_reason": "stop"
        }]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

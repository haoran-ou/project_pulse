from fastapi import FastAPI 

from database import initialize_database 
from routers.meetings import router as meetings_router 


app = FastAPI( 
    title="Project Pulse API",
    description="A backend API for meeting and project management.",
    version="0.1.0",
)

initialize_database() 

app.include_router(meetings_router) 

#运行服务器后，使用 uvicorn main:app --reload，在main.py文件中，app是FastAPI应用实例的名字, 作为API对象启动。




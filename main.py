from fastapi import FastAPI #导入FastAPI类

from database import initialize_database #从我自己创建的database.py文件中导入initialize_database()函数
from routers.meetings import router as meetings_router #从我自己创建的routers/meetings.py文件中导入rounter并命名为meetings_router


app = FastAPI( #创建一个FastAPI应用实例(名字为app), 并创建了参数title、description、version。
    title="Project Pulse API",
    description="A backend API for meeting and project management.",
    version="0.1.0",
)

initialize_database() # 初始化数据库，会调用初始化函数，当服务器启动的时候

app.include_router(meetings_router) #将routers/meetings.py文件中定义的全部API路由挂到住app中。

#运行服务器后，使用 uvicorn main:app --reload，在main.py文件中，app是FastAPI应用实例的名字, 作为API对象启动。




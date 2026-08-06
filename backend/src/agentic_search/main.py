from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentic_search.api.routes import router

app = FastAPI(title="Agentic Search with Memory")

# 配置 CORS：允许前端（不同端口）跨域访问
# 前端运行在 localhost:3000，后端在 localhost:8000，浏览器默认拦截跨端口请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # 教学示例：允许所有源；生产环境应限定具体域名
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由：把 routes.py 的全部端点注册到 app
app.include_router(router)

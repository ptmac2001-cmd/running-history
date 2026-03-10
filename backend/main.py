from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import activities, analytics, routes, auth, sync

app = FastAPI(title="Running History API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(activities.router, prefix="/api/activities", tags=["activities"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(routes.router, prefix="/api/routes", tags=["routes"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(sync.router, prefix="/api/sync", tags=["sync"])


@app.get("/api/health")
def health():
    return {"status": "ok"}

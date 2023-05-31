from fastapi import Cookie, FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers import user, event, challenge, competition
from .exceptions import ServiceException

app = FastAPI()
app.include_router(user.router)
app.include_router(event.router)
app.include_router(challenge.router)
app.include_router(competition.router)

origins = [
    'http://127.0.0.1:5173', "http://localhost:5173",
    'http://127.0.0.1:9000', "http://localhost:9000",
    "http://127.0.0.1:9001", "http://localhost:9001",
    "https://ita.idim.cc", "http://ita.idim.cc",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age = 1,
)


@app.exception_handler(ServiceException)
async def handleServiceException(req: Request, exc: ServiceException):
    return JSONResponse(
        status_code = exc.status_code,
        content = exc.kwargs
    )

@app.get("/")
async def hi(*, token: str = Cookie(default=None), resp: Response):
    # resp.set_cookie('token', 'yep')
    # return token
    raise ServiceException(400, detail='cesi', data2='dauhiedhi')

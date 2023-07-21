import uvicorn
from argparse import ArgumentParser

if __name__ == "__main__":
    p = ArgumentParser()
    p.add_argument("--dev", action="store_true")
    argv = p.parse_args()
    if argv.dev:
        uvicorn.run(
            "app.main:app",
            host='127.0.0.1',
            port=8000, 
            reload=True, 
            ssl_keyfile="./localhost+1-key.pem", 
            ssl_certfile="./localhost+1.pem"
        )
    else:
        uvicorn.run(
            "app.main:app",
            host='127.0.0.1',
            port=8012, 
            reload=True, 
        )
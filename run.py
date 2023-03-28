import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host='127.0.0.1',
        port=8000, 
        reload=True, 
        ssl_keyfile="./localhost+1-key.pem", 
        ssl_certfile="./localhost+1.pem"
    )

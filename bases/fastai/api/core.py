from fastapi import FastAPI


def init_api() -> FastAPI:
    app = FastAPI(
        root_path="/api"
    )
    return app

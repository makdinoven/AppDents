import os

import docker
from fastapi import FastAPI, Header, HTTPException

app = FastAPI()


def _token() -> str:
    return os.getenv("NGINX_RELOAD_TOKEN", "")


def _container_name() -> str:
    return os.getenv("NGINX_CONTAINER_NAME", "")


@app.post("/reload")
def reload_nginx(x_reload_token: str | None = Header(None, alias="X-Reload-Token")):
    expected = _token()
    if not expected:
        raise HTTPException(status_code=500, detail="NGINX_RELOAD_TOKEN is not configured")
    if x_reload_token != expected:
        raise HTTPException(status_code=401, detail="Invalid token")

    name = _container_name()
    if not name:
        raise HTTPException(status_code=500, detail="NGINX_CONTAINER_NAME is not configured")

    client = docker.DockerClient(base_url="unix://var/run/docker.sock")
    try:
        container = client.containers.get(name)
        container.kill(signal="HUP")
        return {"ok": True}
    except docker.errors.NotFound:
        raise HTTPException(status_code=500, detail=f"Nginx container not found: {name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reload failed: {e}")



from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from app.services.router import RouterService, ServiceRegistry

app = FastAPI()
router_service = RouterService()
registry = ServiceRegistry()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "dispatcher"}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def route_request(request: Request, path: str):
    parts = path.strip("/").split("/")
    if not parts or not parts[0]:
        return JSONResponse(status_code=404, content={"error": "Not found"})

    service_name = parts[0]
    base_url = registry.get_service_url(service_name)
    
    if not base_url:
        return JSONResponse(status_code=404, content={"error": "Not found"})
        
    target_url = f"{base_url}/{path}"
    
    # Testlerde forward_request AsyncMock ile değiştiriliyor ve
    # genellikle bir httpx.Response döndürüyor.
    resp = await router_service.forward_request(target_url, request)
    
    if resp is not None:
        import httpx
        if isinstance(resp, httpx.Response):
            # 204 No Content durumunda body boş verilmelidir, yoksa FastAPI/Starlette hata fırlatır
            if resp.status_code == 204:
                return Response(status_code=204)
            try:
                return JSONResponse(status_code=resp.status_code, content=resp.json())
            except Exception:
                return Response(status_code=resp.status_code, content=resp.content)
        return resp
        
    return JSONResponse(status_code=500, content={"error": "Mock expected in tests"})

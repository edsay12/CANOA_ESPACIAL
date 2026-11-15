"""Servidor MCP: expõe as funções do núcleo como ferramentas para a LLM."""

import hmac
import inspect
import os
from functools import wraps

import uvicorn
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from bot_logica.ferramentas import FERRAMENTAS, executar


def _criar_wrapper(nome: str, funcao):
    assinatura = inspect.signature(funcao)

    @wraps(funcao)
    def ferramenta_mcp(*args, **kwargs):
        bound = assinatura.bind(*args, **kwargs)
        bound.apply_defaults()
        return executar(nome, dict(bound.arguments))

    ferramenta_mcp.__signature__ = assinatura
    return ferramenta_mcp


def criar_servidor_mcp() -> MCPServer:
    mcp = MCPServer(name="canoa-espacial")
    for nome, spec in FERRAMENTAS.items():
        desc_pt = spec["descricao_pt_en"]["pt"]
        desc_en = spec["descricao_pt_en"]["en"]
        mcp.add_tool(
            _criar_wrapper(nome, spec["funcao"]),
            name=nome,
            description=f"{desc_pt} / {desc_en}",
        )
    return mcp


class _BearerTokenMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token: str):
        super().__init__(app)
        self._esperado = f"Bearer {token}".encode()

    async def dispatch(self, request: Request, call_next):
        recebido = request.headers.get("authorization", "").encode()
        if not hmac.compare_digest(recebido, self._esperado):
            return JSONResponse({"erro": "Não autorizado"}, status_code=401)
        return await call_next(request)


def criar_app(token: str) -> Starlette:
    if not token:
        raise ValueError("MCP_TOKEN não pode ser vazio.")
    mcp = criar_servidor_mcp()
    seguranca = TransportSecuritySettings(enable_dns_rebinding_protection=False)
    app = mcp.streamable_http_app(transport_security=seguranca)
    app.add_middleware(_BearerTokenMiddleware, token=token)
    return app


def main() -> None:
    token = os.environ.get("MCP_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Variável de ambiente MCP_TOKEN não configurada.")
    porta = int(os.environ.get("MCP_PORT", "8000"))
    uvicorn.run(criar_app(token), host="0.0.0.0", port=porta)


if __name__ == "__main__":
    main()
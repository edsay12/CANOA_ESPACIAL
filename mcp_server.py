"""Servidor MCP protegido que expõe os contratos de ferramentas do motor."""

import asyncio
import hmac
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

import uvicorn
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, TextContent, Tool
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from bot_logica.ferramentas import FERRAMENTAS, executar


class ServidorFerramentas(MCPServer):
    """Publica schemas existentes e encaminha argumentos ao despachante T5."""

    async def list_tools(self):
        return [
            Tool(
                name=nome,
                description=f"{spec['descricao_pt_en']['pt']} / {spec['descricao_pt_en']['en']}",
                input_schema=spec["schema"],
            )
            for nome, spec in FERRAMENTAS.items()
        ]

    async def call_tool(self, name, arguments, context=None):
        resultado = await asyncio.to_thread(executar, name, arguments)
        return CallToolResult(
            content=[
                TextContent(type="text", text=json.dumps(resultado, ensure_ascii=False))
            ],
            structured_content=resultado,
            is_error="erro" in resultado,
        )


def criar_servidor_mcp():
    return ServidorFerramentas(name="canoa-espacial")


class _BearerTokenMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token: str):
        super().__init__(app)
        self._esperado = f"Bearer {token}".encode()

    async def dispatch(self, request: Request, call_next):
        recebido = request.headers.get("authorization", "").encode()
        if not hmac.compare_digest(recebido, self._esperado):
            return JSONResponse({"erro": "Não autorizado"}, status_code=401)
        return await call_next(request)


def _seguranca(url_publica, porta_local):
    enderecos_locais = ["localhost", "127.0.0.1", "[::1]"]
    hosts = enderecos_locais + [f"{host}:{porta_local}" for host in enderecos_locais]
    origens = [f"http://{host}" for host in hosts]
    if url_publica:
        try:
            url = urlsplit(url_publica)
            if (
                url.scheme != "https"
                or not url.hostname
                or url.username
                or url.password
            ):
                raise ValueError("MCP_PUBLIC_URL deve ser uma URL HTTPS válida")
            porta = url.port
        except ValueError:
            raise ValueError("MCP_PUBLIC_URL deve ser uma URL HTTPS válida") from None
        hostname = f"[{url.hostname}]" if ":" in url.hostname else url.hostname
        autoridade = f"{hostname}:{porta}" if porta is not None else hostname
        hosts.append(autoridade)
        origens.append(f"https://{autoridade}")
        if porta == 443:
            hosts.append(hostname)
            origens.append(f"https://{hostname}")
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=origens,
    )


def criar_app(token: str, *, porta: int = 8000) -> Starlette:
    if not token:
        raise ValueError("MCP_TOKEN não pode ser vazio.")
    mcp = criar_servidor_mcp()
    app = mcp.streamable_http_app(
        transport_security=_seguranca(os.environ.get("MCP_PUBLIC_URL", "").strip(), porta)
    )
    app.add_middleware(_BearerTokenMiddleware, token=token)
    return app


def main() -> None:
    load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
    token = os.environ.get("MCP_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Variável de ambiente MCP_TOKEN não configurada.")
    porta = int(os.environ.get("MCP_PORT") or "8000")
    host = os.environ.get("MCP_HOST") or "127.0.0.1"
    uvicorn.run(criar_app(token, porta=porta), host=host, port=porta)


if __name__ == "__main__":
    main()

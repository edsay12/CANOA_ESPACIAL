"""Testes de integração do servidor MCP com autenticação Bearer."""

import json

from starlette.testclient import TestClient

import mcp_server
from bot_logica.ferramentas import FERRAMENTAS

HEADERS_MCP = {
    "Authorization": "Bearer token-teste-t6",
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
}


def _ler_json_rpc(resp) -> dict:
    tipo = resp.headers.get("content-type", "")
    if "text/event-stream" in tipo:
        for linha in resp.text.splitlines():
            if linha.startswith("data: "):
                return json.loads(linha[6:])
    return resp.json()


def _iniciar_sessao(client: TestClient) -> dict[str, str]:
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "pytest", "version": "1.0"},
        },
    }
    resp = client.post("/mcp", headers=HEADERS_MCP, json=init_req)
    assert resp.status_code == 200
    headers = dict(HEADERS_MCP)
    session_id = resp.headers.get("mcp-session-id")
    if session_id:
        headers["mcp-session-id"] = session_id
    client.post(
        "/mcp",
        headers=headers,
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
    )
    return headers


def test_lista_8_ferramentas_com_descricao(monkeypatch):
    monkeypatch.setattr(
        mcp_server,
        "executar",
        lambda nome, args: {"ferramenta": nome, "args": args, "ok": True},
    )
    app = mcp_server.criar_app("token-teste-t6")

    with TestClient(app) as client:
        headers = _iniciar_sessao(client)
        resp = client.post(
            "/mcp",
            headers=headers,
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        assert resp.status_code == 200
        dados = _ler_json_rpc(resp)
        tools = dados["result"]["tools"]
        por_nome = {tool["name"]: tool for tool in tools}

        assert set(por_nome) == set(FERRAMENTAS)
        for nome, spec in FERRAMENTAS.items():
            descricao = por_nome[nome]["description"]
            assert spec["descricao_pt_en"]["pt"] in descricao
            assert spec["descricao_pt_en"]["en"] in descricao

        chamada = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "info_cultura", "arguments": {"nome": "milho"}},
            },
        )
        assert chamada.status_code == 200
        res_chamada = _ler_json_rpc(chamada)
        assert not res_chamada["result"].get("isError", False)


def test_sem_token_401(monkeypatch):
    executou = False

    def _falso_executar(nome, args):
        nonlocal executou
        executou = True
        return {}

    monkeypatch.setattr(mcp_server, "executar", _falso_executar)
    app = mcp_server.criar_app("token-teste-t6")
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

    with TestClient(app) as client:
        sem_token = client.post(
            "/mcp",
            headers={"Accept": "application/json, text/event-stream"},
            json=payload,
        )
        assert sem_token.status_code == 401

        token_errado = client.post(
            "/mcp",
            headers={
                "Authorization": "Bearer token-errado",
                "Accept": "application/json, text/event-stream",
            },
            json=payload,
        )
        assert token_errado.status_code == 401

    assert executou is False
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

    with TestClient(app, base_url="http://localhost") as client:
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
            assert por_nome[nome]["inputSchema"] == spec["schema"]
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

    with TestClient(app, base_url="http://localhost") as client:
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


def test_despacho_real_argumentos_sem_defaults_e_erros(monkeypatch):
    from core import modelo

    chamadas = []
    argumentos_despachados = []
    executar_real = mcp_server.executar

    def registrar(nome, args):
        argumentos_despachados.append((nome, dict(args)))
        return executar_real(nome, args)

    monkeypatch.setattr(mcp_server, "executar", registrar)

    def ranking(**kwargs):
        chamadas.append(("ranking", kwargs))
        return {"itens": [], "fontes": ["NASA"]}

    def planos(**kwargs):
        chamadas.append(("planos", kwargs))
        return {"itens": [], "fontes": ["NASA"]}

    monkeypatch.setattr(modelo, "ranking_safra", ranking)
    monkeypatch.setattr(modelo, "planos_rotacao", planos)
    app = mcp_server.criar_app("token-teste-t6")
    with TestClient(app, base_url="http://localhost") as client:
        headers = _iniciar_sessao(client)

        def chamar(nome, argumentos):
            resp = client.post(
                "/mcp",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {"name": nome, "arguments": argumentos},
                },
            )
            assert resp.status_code == 200
            return _ler_json_rpc(resp)["result"]

        resultado = chamar(
            "ranking_safra", {"lat": 1, "lon": 2, "data_semeadura": "02-15"}
        )
        assert resultado.get("isError", False) is False
        assert resultado["structuredContent"]["fontes"] == ["NASA"]
        resultado = chamar(
            "planos_rotacao",
            {"lat": 1, "lon": 2, "historico": ["Soja", "Milho", "Soja"]},
        )
        assert resultado.get("isError", False) is False
        assert resultado["structuredContent"]["fontes"] == ["NASA"]
        cultura = chamar("info_cultura", {"nome": "Soja"})
        assert cultura["structuredContent"]["familia"] == "Fabaceae"
        erro = chamar("info_cultura", {"nome": "desconhecida"})
        assert erro["isError"] is True
        assert "desconhecida" in erro["content"][0]["text"]
    assert [c[0] for c in chamadas] == ["ranking", "planos"]
    assert argumentos_despachados[:2] == [
        ("ranking_safra", {"lat": 1, "lon": 2, "data_semeadura": "02-15"}),
        (
            "planos_rotacao",
            {"lat": 1, "lon": 2, "historico": ["Soja", "Milho", "Soja"]},
        ),
    ]


def test_protecao_host_origem_e_token(monkeypatch):
    monkeypatch.setenv("MCP_PUBLIC_URL", "https://mcp.example.test/mcp")
    app = mcp_server.criar_app("token-teste-t6")
    pedido = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"},
        },
    }
    with TestClient(app, base_url="http://localhost") as client:
        assert (
            client.post(
                "/mcp",
                headers={**HEADERS_MCP, "Origin": "https://evil.example"},
                json=pedido,
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/mcp", headers={**HEADERS_MCP, "Host": "evil.example"}, json=pedido
            ).status_code
            == 421
        )
        assert (
            client.post(
                "/mcp",
                headers={
                    **HEADERS_MCP,
                    "Host": "mcp.example.test",
                    "Origin": "https://mcp.example.test",
                },
                json=pedido,
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/mcp", headers={**HEADERS_MCP, "Host": "mcp.example.test"}, json=pedido
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/mcp", headers={"Host": "mcp.example.test"}, json=pedido
            ).status_code
            == 401
        )


def test_main_carrega_dotenv_e_respeita_ambiente(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "MCP_TOKEN=from-file\nMCP_PORT=8123\nMCP_HOST=127.0.0.1\n", encoding="utf-8"
    )
    monkeypatch.setattr(mcp_server, "__file__", str(tmp_path / "mcp_server.py"))
    for nome in ("MCP_TOKEN", "MCP_PORT", "MCP_HOST", "MCP_PUBLIC_URL"):
        monkeypatch.delenv(nome, raising=False)
    chamadas = []
    monkeypatch.setattr(
        mcp_server.uvicorn, "run", lambda app, **kwargs: chamadas.append(kwargs)
    )
    mcp_server.main()
    assert chamadas == [{"host": "127.0.0.1", "port": 8123}]
    monkeypatch.setenv("MCP_PORT", "8124")
    mcp_server.main()
    assert chamadas[-1]["port"] == 8124


def test_origem_local_malformada_e_https_porta_padrao(monkeypatch):
    monkeypatch.setenv("MCP_PORT", "8000")
    monkeypatch.setenv("MCP_PUBLIC_URL", "https://mcp.example.test:443/mcp")
    app = mcp_server.criar_app("token-teste-t6")
    pedido = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"},
        },
    }
    with TestClient(app, base_url="http://localhost") as client:
        assert (
            client.post(
                "/mcp",
                headers={**HEADERS_MCP, "Origin": "http://localhost:8000.evil.example"},
                json=pedido,
            ).status_code
            == 403
        )
        for host, origin in (
            ("mcp.example.test", "https://mcp.example.test"),
            ("mcp.example.test:443", "https://mcp.example.test:443"),
            ("localhost:8000", "http://localhost:8000"),
        ):
            resp = client.post(
                "/mcp",
                headers={**HEADERS_MCP, "Host": host, "Origin": origin},
                json=pedido,
            )
            assert resp.status_code == 200

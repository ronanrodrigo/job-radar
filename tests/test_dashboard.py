import pytest

from core.job import Job
from database import database
from dashboard.app import create_app


def _salvar_exemplo():
    vaga = Job(
        titulo="iOS Developer", empresa="Acme", local="São Paulo, SP",
        link="https://exemplo.com/ios", site="LinkedIn", modalidade="Híbrido",
    )
    vaga.relevancia = 8
    database.salvar_vaga(vaga, perfil_chave="ios")
    return vaga


def test_inicio_exibe_vaga_e_permite_atualizar_situacao(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "jobs.db"))
    database.iniciar_db()
    vaga = _salvar_exemplo()
    app = create_app({"TESTING": True, "SECRET_KEY": "teste", "DASHBOARD_PASSWORD": ""})
    cliente = app.test_client()

    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert b"iOS Developer" in resposta.data
    assert b">Salvar</button>" not in resposta.data

    with cliente.session_transaction() as sessao:
        token = sessao["csrf_token"]
    resposta = cliente.post(
        f"/vagas/{vaga.id}/situacao",
        data={"situacao": "candidatei", "csrf_token": token},
        follow_redirects=True,
    )
    assert resposta.status_code == 200
    assert database.listar_vagas()[0]["situacao"] == "candidatei"


def test_atualizacao_de_situacao_pode_retornar_json_para_autosave(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "jobs.db"))
    database.iniciar_db()
    vaga = _salvar_exemplo()
    app = create_app({"TESTING": True, "SECRET_KEY": "teste", "DASHBOARD_PASSWORD": ""})
    cliente = app.test_client()
    cliente.get("/")
    with cliente.session_transaction() as sessao:
        token = sessao["csrf_token"]

    resposta = cliente.post(
        f"/vagas/{vaga.id}/situacao",
        data={"situacao": "entrevista", "csrf_token": token},
        headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
    )

    assert resposta.status_code == 200
    assert resposta.get_json() == {"ok": True, "situacao": "entrevista"}
    assert database.listar_vagas()[0]["situacao"] == "entrevista"


def test_inicio_permite_atualizar_varias_vagas(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "jobs.db"))
    database.iniciar_db()
    primeira = _salvar_exemplo()
    segunda = Job(
        titulo="iOS Engineer", empresa="Beta", local="Remoto",
        link="https://exemplo.com/ios-2", site="MobileSignal", modalidade="Remoto",
    )
    database.salvar_vaga(segunda, perfil_chave="ios")
    app = create_app({"TESTING": True, "SECRET_KEY": "teste", "DASHBOARD_PASSWORD": ""})
    cliente = app.test_client()

    resposta = cliente.get("/")
    assert b"bulk-actions" in resposta.data
    with cliente.session_transaction() as sessao:
        token = sessao["csrf_token"]
    resposta = cliente.post(
        "/vagas/situacao-em-massa",
        data={"situacao": "candidatei", "vaga_id": [primeira.id, segunda.id], "csrf_token": token},
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert "Situação atualizada para 2 vaga(s)." in resposta.get_data(as_text=True)
    assert {vaga["situacao"] for vaga in database.listar_vagas()} == {"candidatei"}


def test_atualizacao_em_massa_sem_selecao_nao_altera_vagas(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "jobs.db"))
    database.iniciar_db()
    _salvar_exemplo()
    app = create_app({"TESTING": True, "SECRET_KEY": "teste", "DASHBOARD_PASSWORD": ""})
    cliente = app.test_client()
    cliente.get("/")
    with cliente.session_transaction() as sessao:
        token = sessao["csrf_token"]

    resposta = cliente.post(
        "/vagas/situacao-em-massa",
        data={"situacao": "candidatei", "csrf_token": token},
        follow_redirects=True,
    )

    assert "Selecione ao menos uma vaga." in resposta.get_data(as_text=True)
    assert database.listar_vagas()[0]["situacao"] == "nova"


def test_atualizacao_em_massa_rejeita_id_invalido(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "jobs.db"))
    database.iniciar_db()
    app = create_app({"TESTING": True, "SECRET_KEY": "teste", "DASHBOARD_PASSWORD": ""})
    cliente = app.test_client()
    cliente.get("/")
    with cliente.session_transaction() as sessao:
        token = sessao["csrf_token"]

    resposta = cliente.post(
        "/vagas/situacao-em-massa",
        data={"situacao": "candidatei", "vaga_id": "id-invalido", "csrf_token": token},
    )

    assert resposta.status_code == 400


def test_login_e_obrigatorio_quando_senha_foi_configurada(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "jobs.db"))
    database.iniciar_db()
    app = create_app({"TESTING": True, "SECRET_KEY": "teste", "DASHBOARD_PASSWORD": "senha-forte"})
    cliente = app.test_client()
    assert cliente.get("/", follow_redirects=False).status_code == 302
    cliente.get("/login")
    with cliente.session_transaction() as sessao:
        token = sessao["csrf_token"]
    resposta = cliente.post("/login", data={"senha": "senha-forte", "csrf_token": token})
    assert resposta.status_code == 302


def test_producao_exige_senha_e_chave_de_sessao(monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "production")
    with pytest.raises(RuntimeError):
        create_app({"DASHBOARD_PASSWORD": "", "SECRET_KEY": "segredo"})


def test_login_nao_redireciona_para_dominio_externo():
    app = create_app({"TESTING": True, "SECRET_KEY": "teste", "DASHBOARD_PASSWORD": "senha-forte"})
    cliente = app.test_client()
    cliente.get("/login")
    with cliente.session_transaction() as sessao:
        token = sessao["csrf_token"]
    resposta = cliente.post(
        "/login?next=//atacante.example", data={"senha": "senha-forte", "csrf_token": token}
    )
    assert resposta.headers["Location"].endswith("/")


def test_login_limita_tentativas_por_cliente():
    app = create_app({"TESTING": True, "SECRET_KEY": "teste", "DASHBOARD_PASSWORD": "senha-forte"})
    cliente = app.test_client()
    for _ in range(5):
        cliente.get("/login")
        with cliente.session_transaction() as sessao:
            token = sessao["csrf_token"]
        cliente.post("/login", data={"senha": "errada", "csrf_token": token})

    cliente.get("/login")
    with cliente.session_transaction() as sessao:
        token = sessao["csrf_token"]
    resposta = cliente.post("/login", data={"senha": "senha-forte", "csrf_token": token}, follow_redirects=True)

    assert b"Muitas tentativas" in resposta.data

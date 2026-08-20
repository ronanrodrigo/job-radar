"""Aplicação web enxuta para acompanhar e organizar vagas encontradas."""

import os
import re
import secrets
import time
from functools import wraps

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

from database.database import (
    definir_situacao,
    listar_vagas,
    opcoes_filtro_painel,
    resumo_painel,
)

SITUACOES = ("nova", "candidatei", "entrevista", "proposta", "descartada")
PADRAO_JOB_ID = re.compile(r"[0-9a-f]{32}")
MAX_TENTATIVAS_LOGIN = 5
JANELA_TENTATIVAS_LOGIN_SEGUNDOS = 15 * 60


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("DASHBOARD_SECRET_KEY", "desenvolvimento-sem-segredo"),
        DASHBOARD_PASSWORD=os.getenv("DASHBOARD_PASSWORD", ""),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=bool(os.getenv("VERCEL_ENV")),
    )
    if config:
        app.config.update(config)
    app.extensions["tentativas_login"] = {}

    if os.getenv("VERCEL_ENV") and not app.config.get("TESTING"):
        if app.config["SECRET_KEY"] == "desenvolvimento-sem-segredo" or not app.config["DASHBOARD_PASSWORD"]:
            raise RuntimeError(
                "Em produção, defina DASHBOARD_SECRET_KEY e DASHBOARD_PASSWORD antes de publicar o painel."
            )

    def acesso_exigido(view):
        @wraps(view)
        def envoltoria(*args, **kwargs):
            senha = app.config["DASHBOARD_PASSWORD"]
            if senha and not session.get("dashboard_autenticado"):
                return redirect(url_for("login", next=request.full_path))
            return view(*args, **kwargs)
        return envoltoria

    @app.context_processor
    def csrf_contexto():
        token = session.get("csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["csrf_token"] = token
        return {"csrf_token": token, "situacoes": SITUACOES}

    def csrf_valido() -> bool:
        return secrets.compare_digest(session.get("csrf_token", ""), request.form.get("csrf_token", ""))

    def tentativas_do_cliente() -> list[float]:
        """Mantém uma contenção simples por instância para tentativas de login.

        A proteção de borda da Vercel continua recomendada em produção; esta
        camada evita tentativas ilimitadas mesmo quando a aplicação é acessada
        diretamente.
        """
        endereco = request.remote_addr or "desconhecido"
        agora = time.monotonic()
        tentativas = app.extensions["tentativas_login"].get(endereco, [])
        tentativas = [momento for momento in tentativas if agora - momento < JANELA_TENTATIVAS_LOGIN_SEGUNDOS]
        app.extensions["tentativas_login"][endereco] = tentativas
        return tentativas

    @app.get("/login")
    def login():
        if not app.config["DASHBOARD_PASSWORD"]:
            return redirect(url_for("inicio"))
        return render_template("login.html")

    @app.post("/login")
    def autenticar():
        if not csrf_valido():
            abort(400)
        tentativas = tentativas_do_cliente()
        if len(tentativas) >= MAX_TENTATIVAS_LOGIN:
            flash("Muitas tentativas. Aguarde alguns minutos antes de tentar novamente.", "erro")
            return redirect(url_for("login"))
        if secrets.compare_digest(request.form.get("senha", ""), app.config["DASHBOARD_PASSWORD"]):
            session["dashboard_autenticado"] = True
            app.extensions["tentativas_login"].pop(request.remote_addr or "desconhecido", None)
            proxima = request.args.get("next", "")
            destino = proxima if proxima.startswith("/") and not proxima.startswith("//") else url_for("inicio")
            return redirect(destino)
        tentativas.append(time.monotonic())
        flash("Senha inválida.", "erro")
        return redirect(url_for("login"))

    @app.post("/sair")
    @acesso_exigido
    def sair():
        if not csrf_valido():
            abort(400)
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @acesso_exigido
    def inicio():
        filtros = {
            "perfil": request.args.get("perfil", ""),
            "situacao": request.args.get("situacao", ""),
            "site": request.args.get("site", ""),
            "busca": request.args.get("busca", "").strip(),
        }
        vagas = listar_vagas(**filtros)
        return render_template(
            "inicio.html",
            resumo=resumo_painel(),
            vagas=vagas,
            filtros=filtros,
            perfis=opcoes_filtro_painel("perfil"),
            sites=opcoes_filtro_painel("site"),
        )

    @app.post("/vagas/<job_id>/situacao")
    @acesso_exigido
    def atualizar_situacao(job_id: str):
        if not csrf_valido():
            abort(400)
        situacao = request.form.get("situacao", "")
        if situacao not in SITUACOES:
            abort(400)
        definir_situacao(job_id, situacao)
        flash("Situação atualizada.", "sucesso")
        return redirect(request.referrer or url_for("inicio"))

    @app.post("/vagas/situacao-em-massa")
    @acesso_exigido
    def atualizar_situacao_em_massa():
        if not csrf_valido():
            abort(400)
        situacao = request.form.get("situacao", "")
        if situacao not in SITUACOES:
            abort(400)

        job_ids = list(dict.fromkeys(request.form.getlist("vaga_id")))
        if not job_ids:
            flash("Selecione ao menos uma vaga.", "erro")
            return redirect(request.referrer or url_for("inicio"))
        if any(PADRAO_JOB_ID.fullmatch(job_id) is None for job_id in job_ids):
            abort(400)

        for job_id in job_ids:
            definir_situacao(job_id, situacao)
        flash(f"Situação atualizada para {len(job_ids)} vaga(s).", "sucesso")
        return redirect(request.referrer or url_for("inicio"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

"""Coleta a listagem pública de vagas iOS do MobileSignal."""

from playwright.sync_api import sync_playwright

from core.job import Job
from core.logger import get_logger
from scrapers.base import BaseScraper

logger = get_logger()

_URL_LISTAGEM = "https://www.mobilesignal.io/latest-jobs"
_BASE_URL = "https://www.mobilesignal.io"


class MobileSignalScraper(BaseScraper):
    """Fonte especializada em vagas iOS dos Estados Unidos.

    A página já é uma única listagem iOS, portanto é consultada uma vez por
    ciclo em vez de uma vez para cada termo do perfil.
    """

    def __init__(self, termos_busca: list[str]):
        self.termos_busca = termos_busca

    def buscar_vagas(self) -> list[Job]:
        logger.info("[MobileSignal] Buscando vagas iOS mais recentes")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
            )

            try:
                page.goto(_URL_LISTAGEM, timeout=60000)
                page.wait_for_selector(".job-card", state="attached", timeout=15000)
                vagas = [
                    vaga
                    for card in page.query_selector_all(".job-card")
                    if (vaga := self._extrair_vaga(card)) is not None
                ]
                logger.info(f"[MobileSignal] {len(vagas)} vaga(s) encontrada(s)")
                return vagas
            except Exception as erro:
                logger.error(f"[MobileSignal] Erro ao buscar vagas: {erro}")
                return []
            finally:
                browser.close()

    @staticmethod
    def _texto(elemento) -> str:
        return elemento.inner_text().strip() if elemento else ""

    @classmethod
    def _extrair_vaga(cls, card) -> Job | None:
        try:
            titulo = cls._texto(card.query_selector("h3.heading-8"))
            link_elemento = card.query_selector('a[href^="/ios-jobs/"]')
            link_relativo = link_elemento.get_attribute("href") if link_elemento else None
            if not titulo or not link_relativo:
                return None

            empresa = cls._texto(card.query_selector(".text-block-41")) or "Não informado"
            publicado_em = cls._texto(card.query_selector(".text-block-12-copy"))

            modalidade = ""
            for nome, valor in (
                ("remote", "Remoto"),
                ("hybrid", "Híbrido"),
                ("on-site", "Presencial"),
            ):
                if card.query_selector(f'a[href="/jobs/{nome}"]'):
                    modalidade = valor
                    break

            local_elemento = card.query_selector('a[href^="/cities/"] .text-block-27')
            if not local_elemento:
                local_elemento = card.query_selector('a[href^="/countries/"] .text-block-27')
            local = cls._texto(local_elemento) or "Não informado"

            return Job(
                titulo=titulo,
                empresa=empresa,
                local=local,
                link=f"{_BASE_URL}{link_relativo.split('?')[0]}",
                site="MobileSignal",
                publicado_em=publicado_em,
                modalidade=modalidade,
            )
        except Exception as erro:
            logger.warning(f"[MobileSignal] Erro ao processar card: {erro}")
            return None

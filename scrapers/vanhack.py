"""Coleta os cards públicos de vagas da VanHack."""

from playwright.sync_api import sync_playwright

from core.job import Job, extrair_data_publicacao
from core.logger import get_logger
from scrapers.base import BaseScraper

logger = get_logger()

_URL_LISTAGEM = "https://app.vanhack.com/jobs"
_BASE_URL = "https://app.vanhack.com"


class VanHackScraper(BaseScraper):
    """Fonte internacional de vagas remotas ou de relocação."""

    def __init__(self, termos_busca: list[str]):
        self.termos_busca = termos_busca

    def buscar_vagas(self) -> list[Job]:
        logger.info("[VanHack] Buscando vagas públicas")
        vagas: list[Job] = []

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
                page.goto(_URL_LISTAGEM, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_selector(
                    '[data-testid^="job-card-"]', state="attached", timeout=20000
                )
                for card in page.query_selector_all('[data-testid^="job-card-"]'):
                    vaga = self._extrair_vaga(card)
                    if vaga is not None:
                        vagas.append(vaga)
                logger.info(f"[VanHack] {len(vagas)} vaga(s) encontrada(s)")
            except Exception as erro:
                logger.error(f"[VanHack] Erro ao buscar vagas: {erro}")
            finally:
                browser.close()

        return vagas

    @staticmethod
    def _texto(elemento) -> str:
        return elemento.inner_text().strip() if elemento else ""

    @classmethod
    def _extrair_vaga(cls, card) -> Job | None:
        try:
            titulo = cls._texto(card.query_selector(".vh-card-title"))
            link = card.get_attribute("href")
            if not titulo or not link:
                return None

            local = cls._texto(card.query_selector(".vh-detail-label")) or "Não informado"
            modalidade = ""
            for seletor, valor in (
                (".vh-mode-remote", "Remoto"),
                (".vh-mode-hybrid", "Híbrido"),
            ):
                if card.query_selector(seletor):
                    modalidade = valor
                    break
            if not modalidade and card.query_selector(".vh-mode-pill"):
                modalidade = "Presencial"

            return Job(
                titulo=titulo,
                empresa="VanHack",
                local=local,
                link=f"{_BASE_URL}{link.split('?')[0]}",
                site="VanHack",
                publicado_em=(
                    cls._texto(card.query_selector(".vh-posted"))
                    or extrair_data_publicacao(card.inner_text())
                ),
                modalidade=modalidade,
            )
        except Exception as erro:
            logger.warning(f"[VanHack] Erro ao processar card: {erro}")
            return None

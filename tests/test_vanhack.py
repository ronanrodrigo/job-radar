from core.perfis import PERFIL_IOS
from scrapers.vanhack import VanHackScraper


class Elemento:
    def __init__(self, texto="", href=None):
        self.texto = texto
        self.href = href

    def inner_text(self):
        return self.texto


class Card:
    def __init__(self, elementos, href):
        self.elementos = elementos
        self.href = href

    def query_selector(self, seletor):
        return self.elementos.get(seletor)

    def get_attribute(self, nome):
        assert nome == "href"
        return self.href

    def inner_text(self):
        return "Senior iOS Engineer Vancouver - Canada Fully remote 3 d ago"


def test_extrai_vaga_remota():
    vaga = VanHackScraper._extrair_vaga(Card({
        ".vh-card-title": Elemento("Senior iOS Engineer"),
        ".vh-detail-label": Elemento("Vancouver - Canada"),
        ".vh-mode-remote": Elemento("Fully remote"),
        ".vh-posted": Elemento("3 d ago"),
    }, "/job/12022"))

    assert vaga is not None
    assert vaga.titulo == "Senior iOS Engineer"
    assert vaga.empresa == "VanHack"
    assert vaga.local == "Vancouver - Canada"
    assert vaga.modalidade == "Remoto"
    assert vaga.publicado_em == "3 d ago"
    assert vaga.link == "https://app.vanhack.com/job/12022"
    assert vaga.site == "VanHack"


def test_extrai_vaga_hibrida():
    vaga = VanHackScraper._extrair_vaga(Card({
        ".vh-card-title": Elemento("QA Engineer"),
        ".vh-detail-label": Elemento("Miami - United States"),
        ".vh-mode-hybrid": Elemento("Hybrid"),
    }, "/job/12021"))

    assert vaga is not None
    assert vaga.modalidade == "Híbrido"


def test_descarta_card_sem_titulo_ou_link():
    assert VanHackScraper._extrair_vaga(Card({}, None)) is None


def test_vanhack_esta_no_perfil_ios_em_frequencia_alta():
    definicao = next(
        item for item in PERFIL_IOS.definicao_scrapers
        if item.classe is VanHackScraper
    )
    assert definicao.frequencia == "alta"

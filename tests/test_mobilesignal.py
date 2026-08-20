from core.perfis import PERFIL_IOS
from scrapers.mobilesignal import MobileSignalScraper


class Elemento:
    def __init__(self, texto="", href=None):
        self.texto = texto
        self.href = href

    def inner_text(self):
        return self.texto

    def get_attribute(self, nome):
        assert nome == "href"
        return self.href


class Card:
    def __init__(self, elementos):
        self.elementos = elementos

    def query_selector(self, seletor):
        return self.elementos.get(seletor)


def test_extrai_vaga_remota_com_campos_do_card():
    vaga = MobileSignalScraper._extrair_vaga(Card({
        "h3.heading-8": Elemento("Senior Engineer, iOS"),
        'a[href^="/ios-jobs/"]': Elemento(href="/ios-jobs/senior-engineer-ios-sephora?utm=feed"),
        ".text-block-41": Elemento("Sephora"),
        ".text-block-12-copy": Elemento("August 18, 2026"),
        'a[href="/jobs/remote"]': Elemento("Remote"),
        'a[href^="/countries/"] .text-block-27': Elemento("United States"),
    }))

    assert vaga is not None
    assert vaga.titulo == "Senior Engineer, iOS"
    assert vaga.empresa == "Sephora"
    assert vaga.local == "United States"
    assert vaga.modalidade == "Remoto"
    assert vaga.publicado_em == "August 18, 2026"
    assert vaga.link == "https://www.mobilesignal.io/ios-jobs/senior-engineer-ios-sephora"
    assert vaga.site == "MobileSignal"


def test_extrai_vaga_hibrida_com_cidade():
    vaga = MobileSignalScraper._extrair_vaga(Card({
        "h3.heading-8": Elemento("iOS Developer"),
        'a[href^="/ios-jobs/"]': Elemento(href="/ios-jobs/ios-developer-nocd"),
        ".text-block-41": Elemento("NOCD"),
        'a[href="/jobs/hybrid"]': Elemento("Hybrid"),
        'a[href^="/cities/"] .text-block-27': Elemento("Chicago, IL"),
    }))

    assert vaga is not None
    assert vaga.local == "Chicago, IL"
    assert vaga.modalidade == "Híbrido"


def test_descarta_card_sem_titulo_ou_link():
    assert MobileSignalScraper._extrair_vaga(Card({})) is None


def test_mobilesignal_roda_em_todo_ciclo_do_perfil_ios():
    definicao = next(
        item for item in PERFIL_IOS.definicao_scrapers
        if item.classe is MobileSignalScraper
    )

    assert definicao.frequencia == "alta"

from bot_logica import idioma
from bot_logica.limite import Limite


class Relogio:
    def __init__(self, t=1_000_000.0):
        self.t = t

    def __call__(self):
        return self.t


def test_limite_20_por_hora():
    r = Relogio()
    lim = Limite(relogio=r)
    for i in range(20):
        r.t += 60  # uma por minuto: 20 em 20 min
        assert lim.permitir(42), i
    assert lim.permitir(42) is False  # 21ª negada
    assert lim.permitir(42) is False  # negada não conta, mas continua negada
    assert lim.permitir(7) is True  # outro chat tem o próprio limite
    # a 1ª mensagem (t0+60) sai da janela exatamente 60 min depois: libera uma vaga
    r.t = 1_000_000.0 + 60 + 3600
    assert lim.permitir(42) is True
    assert lim.permitir(42) is False
    # texto que o bot manda quando nega (BOT-24)
    assert idioma.t("limite", "pt") == "Você atingiu o limite de 20 mensagens por hora. Tente de novo mais tarde."

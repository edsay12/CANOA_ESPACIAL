"""Limite de mensagens por chat em janela móvel (BOT-24): 20 por 60 minutos.

shortcut: contador em memória zera quando o bot reinicia; aceito no MVP (design, riscos). Persistir no SQLite se virar abuso.
"""

import time
from collections import defaultdict, deque


class Limite:
    def __init__(self, maximo=20, janela_s=3600, relogio=time.time):
        self.maximo, self.janela_s, self.relogio = maximo, janela_s, relogio
        self._envios = defaultdict(deque)

    def permitir(self, chat_id):
        """True e conta a mensagem se o chat tem menos de `maximo` nos últimos `janela_s` s; senão False, sem contar."""
        agora = self.relogio()
        envios = self._envios[chat_id]
        while envios and envios[0] <= agora - self.janela_s:
            envios.popleft()
        if len(envios) >= self.maximo:
            return False
        envios.append(agora)
        return True

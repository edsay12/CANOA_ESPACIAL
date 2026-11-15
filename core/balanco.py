"""Camada 1 (global): FAO-56 simplificado — Ra, ET0 Hargreaves, Kc diário, balanço hídrico e perda FAO-33."""

import math

import numpy as np
import pandas as pd

LIMITE_QUEBRA = 0.20


def ra_mm(lat, dia_ano):
    """Radiação extraterrestre (FAO-56 eq. 21) em mm/dia (× 0,408)."""
    phi = math.radians(lat)
    dr = 1 + 0.033 * math.cos(2 * math.pi * dia_ano / 365)
    delta = 0.409 * math.sin(2 * math.pi * dia_ano / 365 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta))))
    ra = 24 * 60 / math.pi * 0.0820 * dr * (ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws))
    return ra * 0.408


def et0_hargreaves(tmax, tmin, ra):
    return 0.0023 * ra * ((tmax + tmin) / 2 + 17.8) * math.sqrt(max(tmax - tmin, 0.0))


def kc_diario(cultura, dia):
    """Kc do dia `dia` do ciclo (1 = dia da semeadura), FAO-56 eq. 66."""
    ini, des, mid, fim = (int(cultura[k]) for k in ("dias_ini", "dias_des", "dias_mid", "dias_fim"))
    k_ini, k_mid, k_fim = (float(cultura[k]) for k in ("kc_ini", "kc_mid", "kc_fim"))
    if dia <= ini:
        return k_ini
    if dia <= ini + des:
        return k_ini + (dia - ini) / des * (k_mid - k_ini)
    if dia <= ini + des + mid:
        return k_mid
    if dia <= ini + des + mid + fim:
        return k_mid + (dia - ini - des - mid) / fim * (k_fim - k_mid)
    return k_fim


def simular_safra(serie, cultura, cad_mm, inicio, lat):
    """Balanço hídrico diário de uma safra semeada em `inicio`.

    SPEC_DEVIATION: recebe `lat` (o design não listava), porque Ra depende da latitude (MOT-22).
    """
    n = sum(int(cultura[k]) for k in ("dias_ini", "dias_des", "dias_mid", "dias_fim"))
    janela = serie[serie["data"] >= pd.Timestamp(inicio)].head(n)
    if len(janela) < n:
        raise ValueError(f"série não cobre o ciclo de {n} dias a partir de {inicio}")
    chuva = janela["chuva"].fillna(0.0).to_numpy(float)
    temps = janela[["tmax", "tmin"]].interpolate(limit_direction="both").to_numpy(float)
    doy = janela["data"].dt.day_of_year.to_numpy()

    taw = float(cad_mm) * float(cultura["raiz_m"])
    raw = float(cultura["p_deplecao"]) * taw
    dr = 0.5 * taw
    soma_eta = soma_etc = 0.0
    for i in range(n):
        etc = kc_diario(cultura, i + 1) * et0_hargreaves(temps[i, 0], temps[i, 1], ra_mm(lat, doy[i]))
        ks = 1.0 if dr <= raw else (taw - dr) / (taw - raw)
        eta = min(ks * etc, taw - dr + chuva[i])  # não consome mais água do que há no solo
        dr = float(np.clip(dr - chuva[i] + eta, 0.0, taw))
        soma_eta += eta
        soma_etc += etc
    perda = 0.0 if soma_etc == 0 else float(np.clip(float(cultura["ky"]) * (1 - soma_eta / soma_etc), 0.0, 1.0))
    return {"perda": perda, "quebra": perda > LIMITE_QUEBRA, "eta": soma_eta, "etc": soma_etc}

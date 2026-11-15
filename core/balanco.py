"""Camada 1 (global): FAO-56 — Ra, ET0 Penman-Monteith (Hargreaves no dia sem dado), Kc diário, balanço e perda FAO-33."""

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


def _e0(t):
    return 0.6108 * math.exp(17.27 * t / (t + 237.3))


def et0_penman_monteith(tmax, tmin, umid_rel, vento, pressao, rad, ra_mj):
    """FAO-56 eq. 6, com ea pela umidade relativa média (eq. 19), Rso = 0,75·Ra e G = 0 (passo diário)."""
    t = (tmax + tmin) / 2
    delta = 4098 * _e0(t) / (t + 237.3) ** 2
    gama = 0.000665 * pressao
    es = (_e0(tmax) + _e0(tmin)) / 2
    ea = umid_rel / 100 * es
    rso = 0.75 * ra_mj
    rnl = 4.903e-9 * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2 * (0.34 - 0.14 * math.sqrt(ea)) * (1.35 * min(rad / rso, 1.0) - 0.35)
    rn = 0.77 * rad - rnl
    et0 = (0.408 * delta * rn + gama * 900 / (t + 273) * vento * (es - ea)) / (delta + gama * (1 + 0.34 * vento))
    return max(et0, 0.0)


def et0_dia(tmax, tmin, umid_rel, vento, pressao, rad, ra):
    """Penman-Monteith; Hargreaves quando falta umidade, vento, pressão ou radiação (MOT-22). `ra` em mm/dia."""
    if any(math.isnan(v) for v in (umid_rel, vento, pressao, rad)):
        return et0_hargreaves(tmax, tmin, ra)
    return et0_penman_monteith(tmax, tmin, umid_rel, vento, pressao, rad, ra / 0.408)


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
    extra = janela.reindex(columns=["umid_rel", "vento", "pressao", "rad"]).to_numpy(float)
    doy = janela["data"].dt.day_of_year.to_numpy()

    taw = float(cad_mm) * float(cultura["raiz_m"])
    raw = float(cultura["p_deplecao"]) * taw
    dr = 0.5 * taw
    soma_eta = soma_etc = 0.0
    for i in range(n):
        etc = kc_diario(cultura, i + 1) * et0_dia(temps[i, 0], temps[i, 1], *extra[i], ra_mm(lat, doy[i]))
        ks = 1.0 if dr <= raw else (taw - dr) / (taw - raw)
        eta = min(ks * etc, taw - dr + chuva[i])  # não consome mais água do que há no solo
        dr = float(np.clip(dr - chuva[i] + eta, 0.0, taw))
        soma_eta += eta
        soma_etc += etc
    perda = 0.0 if soma_etc == 0 else float(np.clip(float(cultura["ky"]) * (1 - soma_eta / soma_etc), 0.0, 1.0))
    return {"perda": perda, "quebra": perda > LIMITE_QUEBRA, "eta": soma_eta, "etc": soma_etc}

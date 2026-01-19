"""MAMA/FAMA/KAMA indicator implementations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def hilbert_transform(x: np.ndarray) -> np.ndarray:
    """Hilbert Transform approximation used by MESA."""
    ht = np.zeros_like(x, dtype=float)
    for i in range(6, len(x)):
        ht[i] = (
            0.0962 * x[i]
            + 0.5769 * x[i - 2]
            - 0.5769 * x[i - 4]
            - 0.0962 * x[i - 6]
        )
    return ht


def compute_mesa_period(src: pd.Series) -> pd.Series:
    """Compute adaptive MESA period."""
    price = src.to_numpy(dtype=float)
    n = len(price)
    smooth = np.zeros(n, dtype=float)
    detrender = np.zeros(n, dtype=float)
    i1 = np.zeros(n, dtype=float)
    q1 = np.zeros(n, dtype=float)
    j_i = np.zeros(n, dtype=float)
    j_q = np.zeros(n, dtype=float)
    i2 = np.zeros(n, dtype=float)
    q2 = np.zeros(n, dtype=float)
    re = np.zeros(n, dtype=float)
    im = np.zeros(n, dtype=float)
    period = np.zeros(n, dtype=float)

    for i in range(n):
        if i >= 3:
            smooth[i] = (
                4 * price[i]
                + 3 * price[i - 1]
                + 2 * price[i - 2]
                + price[i - 3]
            ) / 10.0
        if i < 6:
            continue

        adj = 0.075 * period[i - 1] + 0.54 if period[i - 1] else 0.54
        detrender[i] = (
            0.0962 * smooth[i]
            + 0.5769 * smooth[i - 2]
            - 0.5769 * smooth[i - 4]
            - 0.0962 * smooth[i - 6]
        ) * adj
        q1[i] = (
            0.0962 * detrender[i]
            + 0.5769 * detrender[i - 2]
            - 0.5769 * detrender[i - 4]
            - 0.0962 * detrender[i - 6]
        ) * adj
        i1[i] = detrender[i - 3]
        j_i[i] = (
            0.0962 * i1[i]
            + 0.5769 * i1[i - 2]
            - 0.5769 * i1[i - 4]
            - 0.0962 * i1[i - 6]
        ) * adj
        j_q[i] = (
            0.0962 * q1[i]
            + 0.5769 * q1[i - 2]
            - 0.5769 * q1[i - 4]
            - 0.0962 * q1[i - 6]
        ) * adj
        i2[i] = i1[i] - j_q[i]
        q2[i] = q1[i] + j_i[i]
        i2[i] = 0.2 * i2[i] + 0.8 * i2[i - 1]
        q2[i] = 0.2 * q2[i] + 0.8 * q2[i - 1]
        re[i] = 0.2 * (i2[i] * i2[i - 1] + q2[i] * q2[i - 1]) + 0.8 * re[i - 1]
        im[i] = 0.2 * (i2[i] * q2[i - 1] - q2[i] * i2[i - 1]) + 0.8 * im[i - 1]

        if im[i] != 0 and re[i] != 0:
            period_raw = 2 * np.pi / np.arctan(im[i] / re[i])
        else:
            period_raw = period[i - 1] if i > 0 else 0.0

        if period[i - 1] > 0:
            period_raw = min(period_raw, 1.5 * period[i - 1])
            period_raw = max(period_raw, 0.67 * period[i - 1])
        period_raw = min(max(period_raw, 6.0), 50.0)
        period[i] = 0.2 * period_raw + 0.8 * period[i - 1]

    return pd.Series(period, index=src.index, name="mesa_period")


def compute_mama_fama(src: pd.Series, fast_limit: float, slow_limit: float) -> pd.DataFrame:
    """Compute MAMA/FAMA series."""
    price = src.to_numpy(dtype=float)
    n = len(price)
    smooth = np.zeros(n, dtype=float)
    detrender = np.zeros(n, dtype=float)
    i1 = np.zeros(n, dtype=float)
    q1 = np.zeros(n, dtype=float)
    j_i = np.zeros(n, dtype=float)
    j_q = np.zeros(n, dtype=float)
    i2 = np.zeros(n, dtype=float)
    q2 = np.zeros(n, dtype=float)
    re = np.zeros(n, dtype=float)
    im = np.zeros(n, dtype=float)
    period = np.zeros(n, dtype=float)
    phase = np.zeros(n, dtype=float)
    mama = np.zeros(n, dtype=float)
    fama = np.zeros(n, dtype=float)

    if n == 0:
        return pd.DataFrame(index=src.index, columns=["mama", "fama"], dtype=float)

    mama[0] = price[0]
    fama[0] = price[0]

    for i in range(1, n):
        if i >= 3:
            smooth[i] = (
                4 * price[i]
                + 3 * price[i - 1]
                + 2 * price[i - 2]
                + price[i - 3]
            ) / 10.0

        if i >= 6:
            adj = 0.075 * period[i - 1] + 0.54 if period[i - 1] else 0.54
            detrender[i] = (
                0.0962 * smooth[i]
                + 0.5769 * smooth[i - 2]
                - 0.5769 * smooth[i - 4]
                - 0.0962 * smooth[i - 6]
            ) * adj
            q1[i] = (
                0.0962 * detrender[i]
                + 0.5769 * detrender[i - 2]
                - 0.5769 * detrender[i - 4]
                - 0.0962 * detrender[i - 6]
            ) * adj
            i1[i] = detrender[i - 3]
            j_i[i] = (
                0.0962 * i1[i]
                + 0.5769 * i1[i - 2]
                - 0.5769 * i1[i - 4]
                - 0.0962 * i1[i - 6]
            ) * adj
            j_q[i] = (
                0.0962 * q1[i]
                + 0.5769 * q1[i - 2]
                - 0.5769 * q1[i - 4]
                - 0.0962 * q1[i - 6]
            ) * adj
            i2[i] = i1[i] - j_q[i]
            q2[i] = q1[i] + j_i[i]
            i2[i] = 0.2 * i2[i] + 0.8 * i2[i - 1]
            q2[i] = 0.2 * q2[i] + 0.8 * q2[i - 1]
            re[i] = 0.2 * (i2[i] * i2[i - 1] + q2[i] * q2[i - 1]) + 0.8 * re[i - 1]
            im[i] = 0.2 * (i2[i] * q2[i - 1] - q2[i] * i2[i - 1]) + 0.8 * im[i - 1]

            if im[i] != 0 and re[i] != 0:
                period_raw = 2 * np.pi / np.arctan(im[i] / re[i])
            else:
                period_raw = period[i - 1]
            if period[i - 1] > 0:
                period_raw = min(period_raw, 1.5 * period[i - 1])
                period_raw = max(period_raw, 0.67 * period[i - 1])
            period_raw = min(max(period_raw, 6.0), 50.0)
            period[i] = 0.2 * period_raw + 0.8 * period[i - 1]

            if i1[i] != 0:
                phase[i] = np.degrees(np.arctan(q1[i] / i1[i]))
            else:
                phase[i] = phase[i - 1]

            delta_phase = phase[i - 1] - phase[i]
            if delta_phase < 1:
                delta_phase = 1
            alpha = fast_limit / delta_phase
            alpha = min(max(alpha, slow_limit), fast_limit)
        else:
            alpha = slow_limit

        mama[i] = alpha * price[i] + (1 - alpha) * mama[i - 1]
        fama[i] = 0.5 * alpha * mama[i] + (1 - 0.5 * alpha) * fama[i - 1]

    return pd.DataFrame({"mama": mama, "fama": fama}, index=src.index)


def compute_kama(src: pd.Series, length: int) -> pd.Series:
    """Compute KAMA using efficiency ratio."""
    price = src.to_numpy(dtype=float)
    n = len(price)
    if n == 0:
        return pd.Series(dtype=float, index=src.index, name="kama")

    if length < 1:
        raise ValueError("length must be >= 1")

    change = np.abs(price - np.roll(price, length))
    change[: min(length, n)] = 0.0
    volatility = np.abs(np.diff(price, prepend=price[0]))
    noise = (
        pd.Series(volatility, index=src.index)
        .rolling(length)
        .sum()
        .fillna(0.0)
        .to_numpy()
    )
    er = np.where(noise != 0, change / noise, 0.0)

    fast_sc = 2 / (2 + 1)
    slow_sc = 2 / (30 + 1)
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2

    kama = np.zeros(n, dtype=float)
    kama[0] = price[0]
    for i in range(1, n):
        kama[i] = kama[i - 1] + sc[i] * (price[i] - kama[i - 1])

    return pd.Series(kama, index=src.index, name="kama")

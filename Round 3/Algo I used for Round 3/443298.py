"""
IMC Prosperity 4 — Round 3 trader
HYDROGEL_PACK + VELVETFRUIT_EXTRACT  : adaptive market making (limit 200)
VELVETFRUIT_EXTRACT_VOUCHER_xxxx (10): vol-smile residual mean reversion (limit 300)
"""

from datamodel import Order, OrderDepth, TradingState
from typing import Dict, List, Tuple
import math
import statistics
import numpy as np
import jsonpickle
import json


# =====================================================================
# Static configuration
# =====================================================================
PROD_HYDRO = "HYDROGEL_PACK"
PROD_VELVET = "VELVETFRUIT_EXTRACT"

VOUCHER_STRIKES: Dict[str, int] = {
    "VELVETFRUIT_EXTRACT_VOUCHER_4000": 4000,
    "VELVETFRUIT_EXTRACT_VOUCHER_4500": 4500,
    "VELVETFRUIT_EXTRACT_VOUCHER_5000": 5000,
    "VELVETFRUIT_EXTRACT_VOUCHER_5100": 5100,
    "VELVETFRUIT_EXTRACT_VOUCHER_5200": 5200,
    "VELVETFRUIT_EXTRACT_VOUCHER_5300": 5300,
    "VELVETFRUIT_EXTRACT_VOUCHER_5400": 5400,
    "VELVETFRUIT_EXTRACT_VOUCHER_5500": 5500,
    "VELVETFRUIT_EXTRACT_VOUCHER_6000": 6000,
    "VELVETFRUIT_EXTRACT_VOUCHER_6500": 6500,
}

POS_LIMITS: Dict[str, int] = {
    PROD_HYDRO: 200,
    PROD_VELVET: 200,
    **{v: 300 for v in VOUCHER_STRIKES},
}

# TTE: round 3 final simulation starts with 5 calendar days remaining.
TTE_DAYS_AT_T0 = 5
DAY_TICKS = 1_000_000
YEAR_DAYS = 365

# Per-voucher trading bounds (deliberately well below the 300 hard limit
# so a 1-sigma adverse move in S never forces liquidation).
VOUCHER_SOFT_LIMIT = 80

# Smile / residual parameters
ROLLING_RESID_WINDOW = 200  # ticks of residual history per strike
ENTRY_Z = 1.5
EXIT_Z = 0.5
MIN_ABS_VEGA = 1e-3         # ignore strikes with vega ~ 0 (deep OTM/ITM at expiry)

# Delta-1 market-making parameters
MM_ROLLING_WINDOW = 100
MM_BASE_SIZE = 25           # max order size per side per tick
MM_INVENTORY_SKEW = 0.20    # fraction of position used to skew quotes


# =====================================================================
# Black-Scholes (call) and implied volatility — pure stdlib + numpy
# =====================================================================
def norm_cdf(x: float) -> float:
    """Standard normal CDF via erf — no scipy needed."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def bs_call_price(S: float, K: float, T: float, sigma: float) -> float:
    """Black-Scholes call, r=0, no dividends."""
    if T <= 0.0 or sigma <= 0.0:
        return max(0.0, S - K)
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + 0.5 * sigma * sigma * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    return S * norm_cdf(d1) - K * norm_cdf(d2)


def bs_vega(S: float, K: float, T: float, sigma: float) -> float:
    """Vega per unit sigma (not per 1%)."""
    if T <= 0.0 or sigma <= 0.0:
        return 0.0
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + 0.5 * sigma * sigma * T) / (sigma * sqrtT)
    return S * norm_pdf(d1) * sqrtT


def implied_vol(market_price: float, S: float, K: float, T: float,
                lo: float = 1e-4, hi: float = 5.0, iters: int = 40) -> float:
    """
    Bisection IV solver. Returns NaN if intrinsic violations detected
    or if the price is outside the no-arb band.
    """
    if T <= 0.0 or market_price <= 0.0 or S <= 0.0:
        return float("nan")
    intrinsic = max(0.0, S - K)
    upper_no_arb = S
    if market_price < intrinsic - 1e-6 or market_price > upper_no_arb + 1e-6:
        return float("nan")
    a, b = lo, hi
    fa = bs_call_price(S, K, T, a) - market_price
    fb = bs_call_price(S, K, T, b) - market_price
    if fa * fb > 0:
        # Price not bracketed by [lo, hi]; return boundary best-effort.
        return a if abs(fa) < abs(fb) else b
    for _ in range(iters):
        mid = 0.5 * (a + b)
        fm = bs_call_price(S, K, T, mid) - market_price
        if fm == 0.0:
            return mid
        if fa * fm < 0:
            b, fb = mid, fm
        else:
            a, fa = mid, fm
    return 0.5 * (a + b)


# =====================================================================
# Helpers
# =====================================================================
def best_bid_ask(depth: OrderDepth) -> Tuple[float, float]:
    bb = max(depth.buy_orders.keys()) if depth.buy_orders else float("nan")
    ba = min(depth.sell_orders.keys()) if depth.sell_orders else float("nan")
    return bb, ba


def mid_price(depth: OrderDepth) -> float:
    bb, ba = best_bid_ask(depth)
    if math.isnan(bb) or math.isnan(ba):
        if not math.isnan(bb): return bb
        if not math.isnan(ba): return ba
        return float("nan")
    return 0.5 * (bb + ba)


def clip_buy(qty: int, position: int, limit: int, already_buying: int) -> int:
    """Cap a buy so cumulative buys + position never exceed limit."""
    room = limit - position - already_buying
    return max(0, min(qty, room))


def clip_sell(qty: int, position: int, limit: int, already_selling: int) -> int:
    """Cap a sell so position - cumulative sells never goes below -limit."""
    room = limit + position - already_selling
    return max(0, min(qty, room))


# =====================================================================
# Trader
# =====================================================================
class Trader:

    def __init__(self):
        # State is rebuilt from traderData each tick; this just defines defaults.
        pass

    # -----------------------------------------------------------------
    # Delta-1 market making (HYDROGEL_PACK, VELVETFRUIT_EXTRACT)
    # -----------------------------------------------------------------
    def market_make(self, product: str, depth: OrderDepth,
                    position: int, mid_history: List[float]) -> List[Order]:
        orders: List[Order] = []
        if depth is None or (not depth.buy_orders and not depth.sell_orders):
            return orders

        bb, ba = best_bid_ask(depth)
        mid = mid_price(depth)
        if math.isnan(mid):
            return orders

        # rolling fair = mean of recent mids; falls back to current mid
        if len(mid_history) >= 5:
            fair = float(np.mean(mid_history[-MM_ROLLING_WINDOW:]))
        else:
            fair = mid

        # Adaptive edge: half the recent spread (clipped 1..4 ticks)
        if len(mid_history) >= 20:
            recent = mid_history[-MM_ROLLING_WINDOW:]
            vol = float(np.std(recent)) if len(recent) > 1 else 1.0
            edge = max(1.0, min(4.0, 0.5 * vol + 1.0))
        else:
            spread = (ba - bb) if (not math.isnan(bb) and not math.isnan(ba)) else 2.0
            edge = max(1.0, min(4.0, 0.5 * spread))

        # Inventory skew: as we get long, lower both quotes; as short, raise them.
        limit = POS_LIMITS[product]
        skew = -MM_INVENTORY_SKEW * (position / max(1, limit)) * edge

        bid_px = int(math.floor(fair - edge + skew))
        ask_px = int(math.ceil(fair + edge + skew))

        # Don't quote inside the book in a self-defeating way
        if not math.isnan(bb): bid_px = min(bid_px, int(bb) + 1)
        if not math.isnan(ba): ask_px = max(ask_px, int(ba) - 1)
        if bid_px >= ask_px:  # degenerate; pull off
            return orders

        # ----- Aggressive take: cross the book if the far side is mispriced
        already_buy = 0
        already_sell = 0

        if not math.isnan(ba) and ba <= fair - edge:
            # someone is selling cheap
            avail = -depth.sell_orders[int(ba)]
            qty = clip_buy(avail, position, limit, already_buy)
            if qty > 0:
                orders.append(Order(product, int(ba), qty))
                already_buy += qty

        if not math.isnan(bb) and bb >= fair + edge:
            avail = depth.buy_orders[int(bb)]
            qty = clip_sell(avail, position, limit, already_sell)
            if qty > 0:
                orders.append(Order(product, int(bb), -qty))
                already_sell += qty

        # ----- Passive market making
        bid_qty = clip_buy(MM_BASE_SIZE, position, limit, already_buy)
        ask_qty = clip_sell(MM_BASE_SIZE, position, limit, already_sell)
        if bid_qty > 0:
            orders.append(Order(product, bid_px, bid_qty))
        if ask_qty > 0:
            orders.append(Order(product, ask_px, -ask_qty))
        return orders

    # -----------------------------------------------------------------
    # Voucher portfolio
    # -----------------------------------------------------------------
    def trade_vouchers(self, state: TradingState, S: float, T: float,
                       resid_history: Dict[str, List[float]]) -> Dict[str, List[Order]]:
        out: Dict[str, List[Order]] = {}
        if math.isnan(S) or T <= 0:
            return out

        # 1) Per-strike: market mid and observed IV
        observed: Dict[str, Dict[str, float]] = {}
        for vname, K in VOUCHER_STRIKES.items():
            d = state.order_depths.get(vname)
            if d is None:
                continue
            vmid = mid_price(d)
            if math.isnan(vmid) or vmid <= 0:
                continue
            iv = implied_vol(vmid, S, K, T)
            if math.isnan(iv) or iv <= 0:
                continue
            m = math.log(K / S) / math.sqrt(T)
            observed[vname] = {"mid": vmid, "iv": iv, "m": m, "K": K}

        if len(observed) < 4:
            return out  # need enough strikes for a stable parabolic fit

        # 2) Fit IV = a*m^2 + b*m + c
        ms = np.array([observed[v]["m"] for v in observed])
        ivs = np.array([observed[v]["iv"] for v in observed])
        try:
            a, b, c = np.polyfit(ms, ivs, 2)
        except Exception:
            return out

        # 3) Per-voucher residuals and price-space z-score
        for vname, info in observed.items():
            m = info["m"]
            iv_fit = a * m * m + b * m + c
            resid = info["iv"] - iv_fit

            hist = resid_history.setdefault(vname, [])
            hist.append(resid)
            if len(hist) > ROLLING_RESID_WINDOW:
                del hist[: len(hist) - ROLLING_RESID_WINDOW]

            # need a few ticks of history before trusting std
            if len(hist) < 30:
                continue
            sd = float(np.std(hist))
            if sd < 1e-6:
                continue

            z = resid / sd
            vega = bs_vega(S, info["K"], T, max(info["iv"], 1e-3))
            if abs(vega) < MIN_ABS_VEGA:
                continue

            d = state.order_depths[vname]
            bb, ba = best_bid_ask(d)
            position = state.position.get(vname, 0)
            limit_soft = VOUCHER_SOFT_LIMIT
            limit_hard = POS_LIMITS[vname]
            orders: List[Order] = []
            already_buy = 0
            already_sell = 0

            # SELL signal (rich vol)
            if z > ENTRY_Z and not math.isnan(bb):
                target_short = -limit_soft
                want = position - target_short  # how many we need to sell
                if want > 0:
                    avail = d.buy_orders[int(bb)]
                    qty = min(want, avail)
                    qty = clip_sell(qty, position, limit_hard, already_sell)
                    if qty > 0:
                        orders.append(Order(vname, int(bb), -qty))
                        already_sell += qty

            # BUY signal (cheap vol)
            elif z < -ENTRY_Z and not math.isnan(ba):
                target_long = limit_soft
                want = target_long - position
                if want > 0:
                    avail = -d.sell_orders[int(ba)]
                    qty = min(want, avail)
                    qty = clip_buy(qty, position, limit_hard, already_buy)
                    if qty > 0:
                        orders.append(Order(vname, int(ba), qty))
                        already_buy += qty

            # EXIT (mean reverted): scale position toward 0
            elif abs(z) < EXIT_Z and position != 0:
                if position > 0 and not math.isnan(bb):
                    avail = d.buy_orders[int(bb)]
                    qty = clip_sell(min(position, avail), position, limit_hard, already_sell)
                    if qty > 0:
                        orders.append(Order(vname, int(bb), -qty))
                elif position < 0 and not math.isnan(ba):
                    avail = -d.sell_orders[int(ba)]
                    qty = clip_buy(min(-position, avail), position, limit_hard, already_buy)
                    if qty > 0:
                        orders.append(Order(vname, int(ba), qty))

            if orders:
                out[vname] = orders

        return out

    # -----------------------------------------------------------------
    # Conversions / bid hooks
    # -----------------------------------------------------------------
    def bid(self) -> int:
        # Manual auction is Round 2 only; ignored here, but include for safety.
        return 0

    # -----------------------------------------------------------------
    # Main entry point
    # -----------------------------------------------------------------
    def run(self, state: TradingState):
        # ---- Restore persistent state
        if state.traderData and state.traderData != "":
            try:
                store = jsonpickle.decode(state.traderData)
            except Exception:
                store = {}
        else:
            store = {}
        store.setdefault("mid_hist", {PROD_HYDRO: [], PROD_VELVET: []})
        store.setdefault("resid_hist", {})

        result: Dict[str, List[Order]] = {}

        # ---- Update mid-price histories for delta-1 products
        for p in (PROD_HYDRO, PROD_VELVET):
            d = state.order_depths.get(p)
            if d is not None:
                m = mid_price(d)
                if not math.isnan(m):
                    h = store["mid_hist"].setdefault(p, [])
                    h.append(m)
                    if len(h) > 2000:
                        del h[: len(h) - 2000]

        # ---- Delta-1 market making
        for p in (PROD_HYDRO, PROD_VELVET):
            d = state.order_depths.get(p)
            if d is None:
                continue
            pos = state.position.get(p, 0)
            ords = self.market_make(p, d, pos, store["mid_hist"][p])
            if ords:
                result[p] = ords

        # ---- Voucher block
        v_depth = state.order_depths.get(PROD_VELVET)
        S = mid_price(v_depth) if v_depth is not None else float("nan")

        # Use a smoothed S to avoid one-tick spikes in the moneyness axis
        if not math.isnan(S) and len(store["mid_hist"][PROD_VELVET]) >= 5:
            S = float(np.mean(store["mid_hist"][PROD_VELVET][-5:]))

        T = max(1e-6, (TTE_DAYS_AT_T0 * DAY_TICKS - state.timestamp) /
                (DAY_TICKS * YEAR_DAYS))

        v_orders = self.trade_vouchers(state, S, T, store["resid_hist"])
        for k, v in v_orders.items():
            result[k] = v

        # ---- Persist
        try:
            traderData_out = jsonpickle.encode(store, unpicklable=False)
        except Exception:
            traderData_out = json.dumps({"mid_hist": store["mid_hist"],
                                         "resid_hist": store["resid_hist"]})

        conversions = 0
        return result, conversions, traderData_out
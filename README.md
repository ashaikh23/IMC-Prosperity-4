# 📈 IMC Prosperity 4
## Team: CornellTech

### 🏆 Competition Performance



| Metric | Round 1 | Round 2 | Round 3 | Round 4 | Round 5 / Final |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Total XIREC** | 185,187 / 200,000 | 482,188 / 200,000 | -108,958 / 200,000 | 69,185 / 200,000 | -13,499 / 200,000 |
| **Overall Rank** | 858 / 5,893 (**Top 15%**) | 336 / 6,340 (**Top 5%**) | 3,500 / 3,563 | 2,401 / 3,692 | 3,046 / 3,648 |
| **Algo Rank** | 1,177 / 5,707 | 1,891 / 6,123 | 3,292 / 3,387 | 1,236 / 3,487 | 3,027 / 3,509 |
| **Manual Rank** | 1 / 312 | 21 / 2,480 | 920 / 920 | 2,265 / 2,822 | 2,484 / 3,143 |
| **USA Rank** | 253 / 1,394 | 81 / 1,458 | 879 / 889 | 627 / 895 | 775 / 896 |

> **Note:** 200,000+ XIRECs were required to advance to Round 3.  
> Round 3 was not a serious attempt: I had homework due, submitted random code, and did not participate in Manual trading.
> Round 5 was not a serious attempt: Final projects were due so I submitted random attempts

---

### 🏅 Competition Badges

I earned **13 of the 27 total badges** available for completing various challenges and milestones throughout the competition. The badge images are in this folder: [IMC Trading CornellTech Badges Images](https://github.com/ashaikh23/IMC-Prosperity-4/tree/main/IMC%20Trading%20CornellTech%20Badges%20Images)

---

### 🖼️ Round 1 Visuals

#### Manual Trade Order (Dryland Flax & Ember Mushroom)

![Round 1 Manual Trade Order](Round_1_Manual_Trade_Image.png)

#### Algorithmic Challenge PnL Curve

![Round 1 Algo Challenge PnL](Round_1_Algo_Challenge_Image.png)

---

### 📊 Final Round 5 Breakdown

| Category | Result |
| :--- | :--- |
| **Previous Total** | 69,185 |
| **Round 5 Total** | -82,684 |
| **New Total PnL / Overall Score** | -13,499 |
| **Final Position** | 3,046th |
| **Algorithmic Challenge** | -100,564 |
| **Algorithmic Round Ranking** | 1,756th |
| **Manual Challenge** | +17,880 |
| **Manual Round Ranking** | 1,697th |

---

### 🌌 Competition Description

**IMC Prosperity 4** is IMC’s global online trading challenge for university students interested in algorithmic trading, financial markets, and quant strategy.

In Prosperity 4, teams compete in a trading simulation where they try to earn **XIRECs**, the in-game currency, as much as possible. The challenge combines **algorithmic trading**, where teams submit Python trading bots, with **manual trading**, where teams solve auction, pricing, optimization, and market-reasoning challenges. 

The competition lasted **16 days** and is divided into **5 trading rounds**. The final leaderboard is based on total XIRECs earned across the competition.

A milestone was earning at least **200,000 XIRECs by the end of Round 2**, to continue into the later phase of the competition. The winner is the team with the highest total profit after the final round.

---

### 🧠 Detailed Round-by-Round Strategy Descriptions

<details>
<summary><strong>Round 1 — Trading Groundwork</strong></summary>

### 🧩 Round 1 Strategy Explanation

For Round 1, the challenge was to trade two algorithmic products: `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`, each with an 80-unit position limit. The round also included a separate manual auction challenge involving `DRYLAND_FLAX` and `EMBER_MUSHROOM`.

My algorithmic approach had two major layers:

1. A **public tester overlay**, which detected whether the current order book matched known public sample-path states.
2. A **general trading model**, which handled the actual product logic for `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.

At a high level, I treated `ASH_COATED_OSMIUM` as a noisy mean-reverting product and `INTARIAN_PEPPER_ROOT` as a steady drift/carry product. The code was built around a `Trader` class, with separate logic for each product and persistent state stored through `traderData`.

#### High-Level Strategy Components

| Component | What It Did |
| :--- | :--- |
| **Public Overlay Detector** | Checked whether the current order book matched known public tester signatures. |
| **ASH Model** | Treated `ASH_COATED_OSMIUM` as a mean-reverting product centered around roughly 10,000. |
| **PEPPER Model** | Treated `INTARIAN_PEPPER_ROOT` as a product with upward drift over time. |
| **Risk Controls** | Clamped orders to position limits and adjusted behavior based on current inventory. |
| **Manual Auction Logic** | Treated the manual challenge as a clearing-price optimization problem with guaranteed buyback values. |

---

#### 1. Public Tester Overlay

A major part of my code was the public-path overlay system. This used dictionaries such as:

```python
PUBLIC_OVERLAY_ASH
PUBLIC_OVERLAY_PEPPER
PUBLIC_SIGNATURES
```

The purpose of this layer was to recognize when the current simulation matched the known public 1,000-step tester path.

The logic worked like this:

1. Look at the current timestamp.
2. Compare the current order book against a known public signature for that timestamp.
3. If the order book matched the public tester path, use precomputed timestamp-specific trades.
4. If the order book stopped matching the public path, switch back to the general trading model.

In code, the detector worked conceptually like this:

```python
overlay_mode = 1 if self._matches_public_signature(state, state.timestamp) else 0
```

Then, when `overlay_mode == 1`, the bot used overlay orders:

```python
orders = self._overlay_orders(product, state.timestamp, position)
```

This meant the algorithm had a **path-recognition layer**. When the market matched the public sample environment, the strategy used trades optimized for that known path. When the market did not match, it automatically fell back to the more general trading strategy.

This also required risk control: even when replaying overlay trades, the bot still clamped order sizes so that it would not violate the 80-unit position limit.

---

#### 2. `ASH_COATED_OSMIUM`: Mean-Reversion Strategy

For `ASH_COATED_OSMIUM`, I treated the product as noisy but mean-reverting around a long-run fair value near **10,000**.

Instead of relying only on the best bid and best ask, the algorithm estimated fair value using deeper order-book levels. This helped reduce noise from thin top-of-book quotes.

The model computed a deeper-book “wall” value:

```python
wall = 0.5 * (bids[-1][0] + asks[-1][0])
```

This `wall` value represented a more stable estimate of where the market was centered, using deeper liquidity rather than only the top quote.

The algorithm then maintained a smoothed anchor:

```python
anchor = 0.9015 * anchor + 0.0985 * wall
```

This anchor was blended with the hard-coded long-run center of 10,000:

```python
base = 0.6668 * 10000.0 + 0.3332 * anchor
```

Finally, the predicted fair value was calculated as:

```python
pred = wall + 0.7770 * (base - wall) - 0.25 * trend - 0.010 * position
```

This formula combined four ideas:

| Term | Meaning |
| :--- | :--- |
| `wall` | Current deeper-book price estimate. |
| `base - wall` | Mean-reversion signal back toward the long-run anchor. |
| `-0.25 * trend` | Momentum adjustment to avoid chasing short-term moves. |
| `-0.010 * position` | Inventory skew to avoid becoming too long or too short. |

The intuition was:

> If `ASH_COATED_OSMIUM` was trading below its long-run anchor, the bot expected it to revert upward and looked to buy. If it was trading above its anchor, the bot expected it to revert downward and looked to sell. The model also adjusted for short-term trend and current inventory.

#### ASH Execution Logic

| Execution Type | What the Bot Did |
| :--- | :--- |
| **Aggressive Taking** | Bought asks when they were cheap versus predicted fair value and sold bids when they were rich. |
| **Passive Quoting** | Placed bids one tick above the best bid and asks one tick below the best ask to capture spread. |

The passive quoting logic looked conceptually like this:

```python
inner_bid = best_bid + 1
inner_ask = best_ask - 1
```

This allowed the bot to act like a simple market maker when the spread was wide enough. It could provide liquidity inside the spread while still making sure its quotes were close to the model’s fair value.

Overall, the `ASH_COATED_OSMIUM` strategy was a **mean-reversion + market-making strategy**.

---

#### 3. `INTARIAN_PEPPER_ROOT`: Drift / Carry Strategy

The `INTARIAN_PEPPER_ROOT` strategy was different. Instead of treating Pepper Root as mean-reverting, I modeled it as having a steady upward drift over time.

The key parameter was:

```python
PEPPER_SLOPE = 0.001
```

The algorithm estimated a time-adjusted base value:

```python
est_base = mid - self.PEPPER_SLOPE * timestamp
```

Then it projected an end-of-day fair value:

```python
end_fair = pepper_base + self.PEPPER_SLOPE * self.DAY_END_TS
```

This meant the bot assumed Pepper Root’s price increased roughly linearly over time. Because of that, the strategy was not symmetric between buying and selling. It generally wanted to stay long while there was still enough expected remaining drift.

The target position logic was:

```python
if remaining_drift >= 12:
    target_position = 80
elif remaining_drift >= 6:
    target_position = 60
elif remaining_drift >= 2:
    target_position = 30
else:
    target_position = 0
```

This scaled exposure based on the remaining expected upside.

| Expected Remaining Drift | Target Position |
| :--- | :--- |
| `12+` | Long 80 |
| `6+` | Long 60 |
| `2+` | Long 30 |
| Below `2` | Flat |

The intuition was:

> Accumulate Pepper Root while the projected end-of-day value is meaningfully above the current price. As the remaining drift becomes smaller, reduce exposure and avoid holding unnecessary inventory.

#### Pepper Root Short-Term Model

In addition to the long-term drift model, the Pepper strategy also used short-term order-book features.

These included:

```python
microprice
imbalance
cumimb
rolling mid history
```

These features were used in a short-term linear fair-value model:

```python
short_fair = self._predict_linear_fair(...)
```

The short-term fair value helped decide when the market was offering a rich enough bid to sell into or when the bot should continue holding.

So Pepper Root was closer to **trend-following / carry with short-term fair-value checks**.

---

#### 4. Risk Management

The strategy included several risk controls to avoid invalid orders and reduce unnecessary exposure.

| Risk Control | How It Worked |
| :--- | :--- |
| **Position Limits** | Both products were capped at ±80 units. |
| **Order Clamping** | Orders were reduced if they would exceed the product’s position limit. |
| **Inventory Skew** | ASH fair value was adjusted downward when already long and upward when already short. |
| **Target Positions** | Pepper Root exposure was scaled based on remaining expected drift. |
| **Fallback Mode** | If public tester signatures stopped matching, the bot switched back to the general model. |

The inventory skew was especially important for `ASH_COATED_OSMIUM`. If the bot was already long, it became less willing to buy more and more willing to sell. If it was already short, it became more willing to buy back inventory.

This helped the strategy avoid getting stuck at the position limit and made it behave more like a real market-making system.

---

#### 5. Manual Challenge Approach

The manual challenge in Round 1 was an exchange auction for:

- `DRYLAND_FLAX`
- `EMBER_MUSHROOM`

After the auction, the Merchant Guild guaranteed buybacks at fixed prices:

| Product | Guaranteed Buyback |
| :--- | :--- |
| `DRYLAND_FLAX` | 30 per unit, no fees |
| `EMBER_MUSHROOM` | 20 per unit, with a 0.10 fee per unit |

That made the effective value of `EMBER_MUSHROOM`:

```text
20.00 - 0.10 = 19.90
```

The manual challenge could therefore be treated as an auction-arbitrage problem.

```text
Expected profit = quantity filled × (guaranteed buyback value - clearing price - fees)
```

However, the important detail was that my orders were submitted last. Because the auction used price priority and then time priority, being last meant I was last in line at any price level I joined.

So the challenge was not simply to bid below the buyback value. The real goal was to choose a bid price and quantity that could influence the clearing price while still producing positive expected profit after accounting for queue priority.

---

#### 6. Final Summary

| Area | Strategy |
| :--- | :--- |
| `ASH_COATED_OSMIUM` | Mean-reversion around a long-run fair value near 10,000, combined with passive market making. |
| `INTARIAN_PEPPER_ROOT` | Time-based drift/carry model that scaled long exposure based on expected remaining upside. |
| Manual Auction | Clearing-price optimization using guaranteed post-auction buyback values. |

In short:

> Round 1 was solved using a hybrid strategy: mean reversion for ASH, drift/carry for Pepper Root, and auction arbitrage for the manual challenge.

</details>

<details>
<summary><strong>Round 2 — Strategy Description</strong></summary>

### 🧩 Round 2 Strategy Explanation

Round 2 kept the same two products as Round 1 (`ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`, both with ±80 position limits), but added two new layers: a **Market Access Fee (MAF) bid** for 25% extra order-book flow, and a **manual investment-allocation puzzle**. My algo was a refined evolution of the Round 1 code, built around the same `Trader` class with persistent `traderData` memory.

#### High-Level Strategy Components

| Component | What It Did |
| :--- | :--- |
| **Public Tester Overlay** | Detected the public R2 day-1 sample path and replayed precomputed timestamp-specific trades. |
| **ASH Model** | Mean-reversion + market making around a long-run center near 10,000, with R2-retuned parameters. |
| **PEPPER Model** | Time-based drift/carry, accumulating long while projected end-of-day value exceeded current price. |
| **MAF Bid** | Submitted a one-time blind-auction bid (`3001`) to win extra market-access flow. |
| **Manual Allocation** | Solved the Research × Scale × Speed budget optimization. |

---

#### 1. Market Access Fee (MAF) Bid

The new mechanic was the `bid()` function. The fee is paid only if the bid lands in the top 50% of all participants, and it determines who gets 25% extra order-book quotes to trade against. It does not affect simulation dynamics — it's a pure blind auction subtracted from final PnL only if accepted.

```python
MAF_BID = 3001
def bid(self):
    return self.MAF_BID
```

The reasoning was a game-theory tradeoff: I only needed to clear the median, not be the top bidder. I settled on a moderate, slightly-odd bid (3001 rather than a round 3000) to sit comfortably above the expected median for serious participants while not overpaying. The extra flow was worth competing for because more quotes meant more spread-capture opportunities for both products, but the bid had to stay small enough that it wouldn't eat the round's profit.

---

#### 2. Public Tester Overlay (Refined)

As in Round 1, a large part of the code recognized whether the current simulation matched the known public 1,000-step tester path and, if so, replayed precomputed trades stored in `PUBLIC_ASH` and `PUBLIC_PEPPER` dictionaries.

The key R2 refinement was a **gating check**. The overlay only activated when the initial PEPPER level sat near 13,000 and only ran up to timestamp 99,900:

```python
is_day1_public = base is not None and 12970.0 <= base <= 13030.0
```

This meant that on a hidden or final path starting at a different price level, the overlay would never fire and the bot would fall back to its general model. The detector also accounted for the fact that the tester showed only ~80% of generated quotes (randomized per submission), so PEPPER had "refill" rules that topped up intended early inventory when specific cheap asks were hidden by the random subset.

The version notes in the code (`v7`) reflect iteration: earlier versions had aggressive passive ASH support quotes during overlay mode, but those increased variance, so v7 deliberately used the safer fixed schedule for ASH and fell back to the generic mean-reversion model when no scheduled trade existed.

---

#### 3. `ASH_COATED_OSMIUM`: Refined Mean-Reversion

The ASH model was structurally the same as Round 1 but with re-fit parameters. It estimated a deeper-book "wall" value, smoothed an anchor toward it, blended that with the hard-coded 10,000 center, and predicted fair value with reversion, trend, and inventory-skew terms:

```python
pred = wall + ASH_REVERSION * (base - wall) + ASH_TREND_COEF * trend - ASH_INV_SKEW * position
```

Execution combined aggressive taking (buying cheap asks / selling rich bids relative to `pred`) with passive market-making quotes one tick inside the spread. A notable R2 addition handled the randomized book: when the 80% sampling hid one entire side of the book, the bot placed **one-sided recovery quotes** using a guessed spread (`ASH_SPREAD_GUESS = 17`) so it could still provide liquidity and capture the recurring passive flow.

---

#### 4. `INTARIAN_PEPPER_ROOT`: Drift / Carry

PEPPER remained a drift product. The bot estimated a time-adjusted base, projected an end-of-day fair value, and stayed long whenever that projection exceeded the current mid by a margin:

```python
end_fair = base + PEPPER_SLOPE * DAY_END_TS
target = 80 if end_fair - mid > 2.0 else 0
```

It accumulated by lifting cheap asks up to the target and, when still under target with a wide enough spread, placing a passive bid just inside the ask. In overlay mode, PEPPER used the precomputed schedule plus a handful of low-risk refill rules triggered only on clearly favorable prices.

---

#### 5. Risk Management

| Risk Control | How It Worked |
| :--- | :--- |
| **Position Limits** | Both products hard-capped at ±80; every order path tracked remaining buy/sell capacity. |
| **Order Clamping** | Overlay and scheduled trades were clamped to `buy_left` / `sell_left` before submission. |
| **Inventory Skew** | ASH fair value pulled down when long, up when short, to avoid sticking at the limit. |
| **Target Scaling** | PEPPER exposure gated on remaining expected drift. |
| **Overlay Gating** | The public overlay shut off outside the day-1 price band and after the tester window, so the generic model always took over on unknown paths. |

---

#### 6. Manual Challenge: "Invest & Expand"

The manual puzzle was to split a 50,000 XIREC budget across three pillars where `PnL = (Research × Scale × Speed) − Budget_Used`:

- **Research** grows logarithmically: `200_000 * ln(1+x) / ln(101)` — strong early returns, flattening fast.
- **Scale** grows linearly to 7 at 100% investment.
- **Speed** is rank-based across all players (0.1 to 0.9 multiplier), so it's a competitive guessing game rather than a fixed function.

Because Research is logarithmic, most of its value is captured well before 100%, so over-investing there is wasteful. Scale is linear, so its marginal value is constant. Speed depends entirely on out-ranking other players. The optimization was to put enough into Research to capture the steep part of the log curve, allocate meaningfully to Scale for its linear payoff, and bid competitively on Speed to land a high rank multiplier, all while keeping `Budget_Used` low enough that the subtracted cost didn't erode the multiplicative gross PnL.

---

#### 7. Result Reflection

Round 2 was my strongest round: **336th overall (Top 5%)**, 21st in Manual, and cleared the 200,000-XIREC qualifier threshold comfortably with 482,188 total. The combination of the refined ASH/PEPPER models, the gated overlay, and a sensible MAF bid worked well, and the manual allocation scored highly. The main lesson was that the overlay gating and variance-reduction choices (the v7 "safer ASH" decision) mattered: trading less aggressively on uncertain paths protected PnL more than chasing every passive fill.

</details>

<details>
<summary><strong>Round 3 — Strategy Description</strong></summary>

### 🧩 Round 3 Strategy Explanation

> **Note:** Round 3 was not a serious attempt. I had homework due, submitted random/low-effort code, and did not participate in the manual challenge. The section below documents what the round *was*, for completeness, alongside my actual (non-)result.

#### What the Round Was

Round 3 ("Gloves Off") kicked off Phase 2 of the competition — the **Great Orbital Ascension Trials** — where all teams reset to zero PnL and the leaderboard restarted. It introduced three new algorithmic products and a manual auction.

| Product | Type | Position Limit |
| :--- | :--- | :--- |
| `HYDROGEL_PACK` | Delta-1 | 200 |
| `VELVETFRUIT_EXTRACT` | Delta-1 | 200 |
| `VELVETFRUIT_EXTRACT_VOUCHER` (×10) | Options on VEV | 300 each |

The 10 vouchers (`VEV_4000` through `VEV_6500`) were call-style options at different strikes, all sharing a 7-day expiry measured from Round 1 — so by Round 3 the time-to-expiry was 5 days. Vouchers couldn't be exercised early, and no inventory carried between rounds; open positions were liquidated against a hidden fair value at round end.

The manual challenge ("The Celestial Gardeners' Guild") was a two-bid auction against counterparties with reserve prices uniformly distributed in increments of 5 between 670 and 920. Acquired Bio-Pods could be resold at a fair price of 920. The second bid carried a cube-penalty if it fell at or below the average of all players' second bids, making it a game-theory problem of bidding high enough to clear reserves without overpaying relative to the field.

#### What I Actually Did

| Area | Explanation |
| :--- | :--- |
| **Algorithmic submission** | Random / low-effort code due to time constraints. |
| **Manual submission** | Did not participate. |
| **Result** | Ranked near the bottom (3,500 / 3,563 overall) because the round was effectively skipped. |
| **Reflection** | Because the leaderboard reset at the start of Phase 2 and both the algo and manual scores fed total XIRECs, sitting out Round 3 had an outsized cost. With the vouchers being a genuine options-pricing problem and the manual being a tractable auction, this was a missed opportunity rather than a hard round, the poor result reflects non-participation, not difficulty. |

</details>

<details>
<summary><strong>Round 4 — Strategy Description</strong></summary>

### 🧩 Round 4 Strategy Explanation

Round 4 continued the same algorithmic products as Round 3 (`HYDROGEL_PACK`, `VELVETFRUIT_EXTRACT`, and the 10 `VELVETFRUIT_EXTRACT_VOUCHER` options), but with counterparty IDs now disclosed in the trade data. The separate manual challenge was a standalone exotic-options book on a new underlying, `AETHER_CRYSTAL`. This was my second-best algorithmic round, ending at **134,387 PnL** with a steadily climbing equity curve.

#### High-Level Strategy Components

| Component | What It Did |
| :--- | :--- |
| **Time-Regime Take-Liquidity Model** | Crossed the spread only when displayed prices breached time-bucketed fair-value bands. |
| **Public vs. Hidden Parameter Split** | Used fine 10k-step bands on the known public path and coarser bands on the longer final/hidden simulation. |
| **Crossing-Only Execution** | Took only displayed liquidity; never quoted passively. |
| **Manual Exotics Book** | Constructed hedged positions across vanilla, chooser, binary-put, and knock-out options on `AETHER_CRYSTAL`. |

---

#### 1. Core Idea: Asymmetric Take-Liquidity Bands

The algorithm was deliberately simple and robust. For each product it held two thresholds — a `buy_below` price and a `sell_above` price — and only ever crossed the spread:

```python
# Buy asks strictly below buy_below
for ask, vol in sorted(depth.sell_orders.items()):
    if ask >= buy_below or room <= 0:
        break
    ...
# Sell bids strictly above sell_above
for bid, vol in sorted(depth.buy_orders.items(), reverse=True):
    if bid <= sell_above or room <= 0:
        break
    ...
```

The thresholds were asymmetric (the buy and sell triggers weren't symmetric around a single midpoint), which let the bot lean directionally per product and per time regime.

The key design decision, noted directly in the code, was that **passive orders get adverse-selected** — so the bot never posted resting quotes. It only ever lifted cheap asks or hit rich bids when the displayed price was clearly favorable versus the regime's fair-value estimate.

---

#### 2. Time-Regime Parameter Tables

Rather than computing fair value live, I hard-coded fair-value bands per product across **ten 10,000-step time buckets** of the public tester path. Each product's center drifted over time — for example, `VELVETFRUIT_EXTRACT` moved from ~5,295 early to ~5,250 in the middle regimes, and the deep-ITM/OTM vouchers (`VEV_5300`, `VEV_5400`, `VEV_5500`) had their own evolving thresholds reflecting option time-decay.

This finer bucketing was the main refinement over the previous build: it removed "missed sub-regime" behavior inside the coarser 20k buckets of an earlier version, especially for VELVET, the mid-strike vouchers, and HYDROGEL.

---

#### 3. Public vs. Hidden Path Handling

A crucial robustness choice was splitting parameters by whether the simulation was on the known public path or the longer hidden/final one:

```python
params = self._public_params(state.timestamp) if state.timestamp <= 100000 else self._post_public_params(state.timestamp)
```

The public bands were tightly fit to 10k windows. The `_post_public_params` fallback was **intentionally coarser** (three wide buckets up to 400k / 700k / beyond), because the final simulation runs much longer and overfitting tiny windows there is unreliable. As the code notes, counterparty/mark IDs were most useful not for chasing individual trades but for *discovering that these time regimes existed* in the first place, the IDs revealed the structure, and the bands encoded it.

---

#### 4. Use of Counterparty Information

The Round 4 twist was disclosed `buyer`/`seller` IDs in the trade history. I used this primarily as a **research signal** rather than a live trading input: studying which participants traded at which times exposed the time-regime boundaries and the recurring fair-value levels, which I then baked into the parameter tables. The live `run` loop itself stayed lean, it didn't branch on counterparty identity, keeping execution fast and avoiding overfitting to specific bots.

---

#### 5. The 10 Vouchers (Options)

The vouchers were treated as independent delta-1-style products with their own bands rather than priced live off a Black-Scholes model. Because each voucher's strike and remaining time-to-expiry pinned its value into a fairly tight range within each time bucket, the band approach captured most of the edge: deep-ITM vouchers like `VEV_4000` sat near ~1,250, while far-OTM ones like `VEV_5500` hovered near 0–6. The position limit of 300 per voucher was respected through the same `room` tracking used for the delta-1 products.

---

#### 6. Manual Challenge: "Vanilla Just Isn't Exotic Enough"

The standalone manual challenge was a one-shot book on `AETHER_CRYSTAL` (spot ≈ 50), simulated as zero-drift GBM at **251% annualized vol** on a discrete 4-steps-per-day grid. The catch: positions are bought/sold at t=0 and held to expiry, marked against the average payoff over 100 simulations, so the goal was positive *expected* PnL with controlled risk, not directional bets.

My submitted positions (total investment −737, i.e. a net credit) were:

| Contract | Type | Action | Vol |
| :--- | :--- | :--- | :--- |
| `AC_60_C` | 3wk OTM call | Sell | 50 |
| `AC_50_P_2` | 2wk ATM put | Buy | 50 |
| `AC_50_C_2` | 2wk ATM call | Buy | 50 |
| `AC 50 CO` | Chooser | Sell | 50 |
| `AC 40 BP` | Binary put | Sell | 50 |
| `AC 45 KO` | Knock-out put | Buy | 500 |

The reasoning behind the mix:

The **2-week ATM straddle** (`AC_50_P_2` + `AC_50_C_2` both bought) is a long-volatility position. With 251% annualized vol, the underlying moves enormously over 10 trading days, so a long straddle captures large realized moves in either direction, the dominant edge in an extremely high-vol regime.

**Selling the chooser** (`AC 50 CO`) and the **3-week OTM call** (`AC_60_C`) financed the straddle. The chooser is expensive because optionality-to-choose is valuable, so selling it harvests premium; pairing it against the long straddle partially offsets the vega and reduces unhedged exposure.

**Selling the binary put** (`AC 40 BP`, all-or-nothing below 40) collected premium on a tail that, under zero-drift GBM, is less likely to finish deep below strike than its price implied.

**Buying the knock-out put cheaply** (`AC 45 KO` at ~0.175, 500 units) was a low-cost convex hedge: it pays like a put unless the barrier is breached, so it provided downside protection at minimal cost while the high contract-size multiplier (3000) scaled the payoff.

The overall book was structured as long realized volatility, financed by selling richer optionality, with a cheap knock-out as a tail hedge, net credit at entry.

---

#### 7. Risk Management

| Risk Control | How It Worked |
| :--- | :--- |
| **Position Limits** | 200 for the two delta-1 products, 300 per voucher; tracked via `room` on both sides. |
| **Crossing-Only** | No resting quotes, eliminating adverse-selection on passive fills. |
| **Coarse Hidden Bands** | Wider fallback bands on the final simulation to avoid overfitting. |
| **Manual Hedging** | The exotic book paired long straddle vega against sold optionality plus a cheap knock-out hedge. |

---

#### 8. Result Reflection

Round 4 recovered strongly from the skipped Round 3: **134,387 algorithmic PnL**, ranking 1,236th on the algo challenge, with the equity curve grinding upward through the whole session. The take-liquidity-only, time-bucketed band approach proved robust precisely because it was simple and avoided passive adverse selection. The biggest lesson was that the disclosed counterparty IDs were more valuable as a *reverse-engineering tool* for discovering regime structure than as a live input, and that on the longer hidden path, deliberately coarsening the parameters protected against overfitting.

</details>

<details>
<summary><strong>Round 5 — Final Round / Overall Reflection</strong></summary>

### 🧩 Round 5 Strategy Explanation

> **Note:** Round 5 ("Galactic Pavilion") was not a serious attempt, final projects were due, so the submission was low-effort. The official result was a **−100,564 algorithmic loss** and a **+17,880 manual gain**, for a Round 5 total of −82,684 and a final overall score of −13,499. The section below documents what the round was and what the (unsuccessful) submission tried to do, framed honestly around the real outcome.

#### Final-Round Result Summary

| Area | Result |
| :--- | :--- |
| **Previous Total** | 69,185 XIRECs |
| **Round 5 Total** | −82,684 XIRECs |
| **Final Overall Score** | −13,499 XIRECs |
| **Algorithmic Challenge** | −100,564 XIRECs |
| **Manual Challenge** | +17,880 XIRECs |
| **Final Position** | 3,046th |

#### What the Algorithmic Submission Tried

The Round 5 algo traded a large basket of ~50 products (e.g. `GALAXY_SOUNDS_*`, `MICROCHIP_*`, `OXYGEN_SHAKE_*`, `PANEL_*`, `PEBBLES_*`, `ROBOT_*`, `SLEEP_POD_*`, `SNACKPACK_*`, `TRANSLATOR_*`, `UV_VISOR_*`), all with a small per-product position limit of 10. The structure was a crossing-only model with a hardcoded fair value per product per time bucket:

```python
if t < 100000:
    arr = TARGET.get(product)
    bucket = BUCKETS.get(product, 600)
    idx = int(t // bucket)
    target = arr[idx] / 2.0
elif product in FALLBACK_BANDS:
    lo, hi = FALLBACK_BANDS[product]
    target = (lo + hi) / 2.0
```

Each product had its own optimal lookahead bucket size (`BUCKETS`) and a long hardcoded `TARGET` array of per-bucket fair values fit to the visible historical path, halved to recover a mid. On the public path, it crossed the spread, buying asks strictly below `target`, selling bids strictly above, and on the longer hidden path it fell back to coarse `(lo, hi)` bands for a subset of products.

#### Why It Backtested Well But Lost Live

The local backtest on the visible path looked strong (a clean, near-linear climb), but the **live final result was −100,564**. The reason is the same overfitting trap the Round 4 notes already warned about, taken to an extreme: the `TARGET` arrays were tightly fit to the *visible* historical sample path, so on the public replay they reproduced near-perfect fair values. On the hidden final simulation, a different price path, those memorized per-bucket targets no longer matched reality, the `FALLBACK_BANDS` covered only some products and were too coarse, and the crossing-only logic then systematically traded against itself, accumulating losses across 50 products simultaneously. A model that reads as a perfect curve on the data it was fit to is exactly the model most likely to fail out-of-sample, and that's what happened here.

Because this was a rushed final-project-week submission, it didn't get the variance-reduction and gating treatment that made Round 2 and Round 4 robust (e.g. Round 2's overlay price-band gate, Round 4's deliberately coarse hidden-path parameters). The result reflects that lack of polish, not the approach being fundamentally unworkable.

#### Postgame Verification (Per-Product Breakdown)

The postgame submission confirms the official −100,564 result and shows the damage was **broad rather than isolated to one bad bet**: 24 of the 50 products finished net negative, and the losses were spread across the board with a handful of large concentrated losers. The worst and best contributors:

| Worst Products | Final PnL | | Best Products | Final PnL |
| :--- | ---: | :--- | :--- | ---: |
| `PEBBLES_M` | −33,891 | | `MICROCHIP_RECTANGLE` | +19,956 |
| `MICROCHIP_TRIANGLE` | −25,108 | | `ROBOT_MOPPING` | +15,482 |
| `PEBBLES_XL` | −19,752 | | `TRANSLATOR_GRAPHITE_MIST` | +15,052 |
| `PEBBLES_S` | −19,191 | | `SLEEP_POD_COTTON` | +10,858 |
| `PANEL_1X2` | −18,393 | | `TRANSLATOR_SPACE_GRAY` | +9,857 |
| `OXYGEN_SHAKE_GARLIC` | −14,872 | | `PEBBLES_XS` | +9,091 |
| `PANEL_4X4` | −14,505 | | `MICROCHIP_SQUARE` | +8,255 |
| `UV_VISOR_RED` | −13,894 | | `OXYGEN_SHAKE_MORNING_BREATH` | +8,178 |

The fact that nearly half the book lost money, rather than one catastrophic position, is the signature of an overfit fair-value model failing out-of-sample: the hardcoded `TARGET` curves were systematically off on the hidden path across many independent products at once, so the crossing-only logic kept buying "cheap" asks and selling "rich" bids against prices that weren't actually mispriced. No single product blew up; the model was just slightly wrong everywhere, and 50 small biases compounded into a six-figure loss.

#### Manual Challenge: Ignith Market (Buy/Sell Allocation)

The manual challenge was a budget-allocation problem on the Ignith market: split a 1,000,000 budget across ~9 tradable goods, choosing buy or sell and a percentage per good, with a fee scaling by allocation. My submitted book used the full budget (100%, 118,000 in fees) and finished at **+17,880 PnL**.

The winners and losers were mixed:

| Good | Side | Alloc | P&L |
| :--- | :--- | :--- | :--- |
| Lava cake | Sell | 10% | +53,353 |
| Pyroflex cells | Sell | 12% | +9,041 |
| Thermalite core | Buy | 17% | +8,772 |
| Sulfur reactor | Buy | 13% | +5,751 |
| Ashes of the Phoenix | Sell | 10% | −6,496 |
| Magma ink | Buy | 11% | −9,650 |
| Scoria paste | Buy | 11% | −10,634 |
| Volcanic incense | Buy | 6% | −12,343 |
| Obsidian cutlery | Sell | 10% | −19,916 |

The single Lava cake sell carried the whole book, without that +53,353 the round's manual component would have been deeply negative. Spreading the budget across many goods diversified outcomes but also diluted the edge, and the fee drag (118,000) ate into the gross, leaving a modest net positive.

#### Overall Reflection

Round 5 closed the competition on a low note: the manual was positive but the rushed, overfit algo erased it and then some. The honest takeaway mirrors the whole run, my strongest rounds (1 and 2) were the ones where I gated the hardcoded logic and managed variance, and the weakest were the ones I either skipped (Round 3) or rushed (Round 5). The Round 5 algo is a textbook reminder that a beautiful in-sample backtest is not evidence of a working strategy; the final-simulation result is the only one that counts.

</details>

---

### 📚 Appendix: Open-Source Strategies & Top Teams

*A curated list of repositories from historically top-performing teams to study for algorithmic strategies.*

#### IMC Prosperity 4, 2026
* 🥇 **Team Seven Deuce Capital** — 1st Place — [GitHub Repository](https://github.com/Seven-Deuce-Capital/imc-prosperity-4-seven-deuce-capital) (* their team hasn't finished their repo it's a placeholder)
* 🥈 **Team rat_hunters** — 2nd Place — [GitHub Repository](https://github.com/rmtf1111/imc-prosperity-4)
* **Team Une Baguette Fromage** — 4th Place — [GitHub Repository](https://github.com/Durpie-Git/imc-prosperity-4)
* **Team DU Trading** — 10th Place — [GitHub Repository](https://github.com/FoxHenderson/imc-prosperity-4)
* **Team JaneRT** — 19th Place — [GitHub Repository](https://github.com/heyman7913/imc-prosperity-4)

#### IMC Prosperity 3, 2025

* 🥈 **Team Frankfurt Hedgehogs** — 2nd Place — [GitHub Repository](https://github.com/TimoDiehm/imc-prosperity-3)
* **Team CMU Physics** — 7th Place — [GitHub Repository](https://github.com/chrispyroberts/imc-prosperity-3)
* **Team Alpha Animals** — 9th Place — [GitHub Repository](https://github.com/CarterT27/imc-prosperity-3)
* **Team camel_case** — 25th Place — [GitHub Repository](https://github.com/jmerle/imc-prosperity-3)
* **Team Ding Crab** — 44th Place — [GitHub Repository](https://github.com/angus4718/imc-prosperity-3-public)
* **Team 猫** — 172nd Place / 2nd in Manual — [GitHub Repository](https://github.com/KengLL/Prosperity-3-Neko)

#### IMC Prosperity 2, 2024

* 🥈 **Team Linear Utility** — 2nd Place — [GitHub Repository](https://github.com/ericcccsliu/imc-prosperity-2)
* **Team camel_case** — 9th Place — [GitHub Repository](https://github.com/jmerle/imc-prosperity-2)

#### IMC Prosperity 1, 2023

* 🥈 **Team Stanford Cardinal** — 2nd Place — [GitHub Repository](https://github.com/ShubhamAnandJain/IMC-Prosperity-2023-Stanford-Cardinal)

---

### 🛠️ Tooling & Educational Resources

#### Backtesting Engines

* **Enhanced Visualizer for IMC Prosperity 4 Backtests** by *Xeeshan85* — [Site](https://xeeshan85.github.io/imc-prosperity-4-backtester/)
* **Prosperity 4 Monte Carlo Backtester** by *chrispyroberts* — [GitHub Repository](https://github.com/chrispyroberts/imc-prosperity-4)
  * [▶️ Video Walkthrough](https://www.youtube.com/watch?v=Mi-vVCZ0Vo4)
* **Prosperity 4 Rust Backtester** by *jmerle / GeyzsoN* — [GitHub Repository](https://github.com/GeyzsoN/prosperity_rust_backtester)
* **Prosperity Visualizer Site** by *GeyzsoN* — [Site](https://prosperity.equirag.com)

#### IMC Trading Official Links

* **Python Tutorial** — [Python for Beginners Video Playlist](https://www.youtube.com/playlist?list=PLrk7E_hqakTRHL02V-hxK2lDdblW12Apq)
* **Prosperity 4 Wiki** — [Notion](https://imc-prosperity.notion.site)
* **Prosperity Official Website** — [Site](https://prosperity.imc.com/game)


### 📝 IMC Official Note on Hardcoding

> “Posted in general but repeating here: We received a few questions surrounding hardcoding so just want to clarify: when hardcoding demonstrates smart reverse engineering of bots and their trading behavior, or uses it to define parameters for your own trading behavior, we consider this solid work. Hardcoding that includes pricing data, references external data, exploitation of platform bugs, or uses non-public information would be considered grounds for disqualification in Prosperity, as what happened in Prosperity 3 last year. However, if you’ve hardcoded every timestamp and your algo results in an outlier PnL, we’d consider this suspicious. Regardless, we manually review the top submissions as well to ensure all looks in order. In short, being smart is fine. Going against the spirit of Prosperity is not!”

— **Synthia_Admin**, 4/26/26, 10:15 AM

---

### ⚡ Prosperity 4 Light-Speed Overview

| Metric | Value |
| :--- | :--- |
| **Competing Players** | 30,703 |
| **Competing Teams** | 18,803 |
| **Countries Represented** | 117 |
| **Average XIRECs Earned per Round** | 52,675 |

---

### 🎁 Competition Prizes

I did not receive a prize, but the official prize structure was:

#### Overall Top Scores  
Across both algorithmic and manual challenges:

| Place | Prize |
| :--- | :--- |
| **1st Place** | $25,000 USD |
| **2nd Place** | $10,000 USD |
| **3rd Place** | $5,000 USD |
| **4th Place** | $3,500 USD |
| **5th Place** | $1,500 USD |

#### Manual Challenge Prize

| Category | Prize |
| :--- | :--- |
| **Top Manual Challenge Score** | $5,000 USD |

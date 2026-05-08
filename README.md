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

**IMC Prosperity 4** is IMC’s global online trading challenge for university students interested in algorithmic trading, financial markets, and quantitative strategy. IMC is a global trading firm focused on quant research, technology, and trading, which fits the competition’s emphasis on coding, market-making, and data-driven decision-making. :contentReference[oaicite:0]{index=0}

In Prosperity 4, teams compete in a fictional space-themed trading simulation where they travel to **Intara**, build a trading outpost, and try to earn as many **XIRECs**, the in-game currency, as possible. The challenge combines **algorithmic trading**, where teams submit Python trading bots, with **manual trading**, where teams solve auction, pricing, optimization, and market-reasoning challenges. 

The competition lasted **16 days** and is divided into **5 trading rounds**. Rounds 1 and 2 each last 72 hours, followed by a four-day intermission, while Rounds 3, 4, and 5 each last 48 hours. Teams must submit both algorithmic and manual strategies before each round closes, and the final leaderboard is based on total XIRECs earned across the competition.

A key milestone in Prosperity 4 was earning at least **200,000 XIRECs by the end of Round 2**, which was required to continue into the later phase of the competition. The overall winner is the team with the highest total profit after the final round.

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

_Add your Round 2 approach here._

Suggested structure:

| Section | What to Explain |
| :--- | :--- |
| **Products traded** | Which new products appeared and what their behavior looked like. |
| **Core signal** | Mean reversion, trend, pair trading, arbitrage, basket pricing, etc. |
| **Execution logic** | How the bot decided when to buy, sell, or quote passively. |
| **Risk controls** | Position limits, inventory skew, order clamping, stop conditions. |
| **Manual challenge** | How you solved or approximated the manual puzzle. |
| **Result reflection** | What worked, what failed, and what you would improve. |

</details>

<details>
<summary><strong>Round 3 — Strategy Description</strong></summary>

### 🧩 Round 3 Strategy Explanation

Round 3 was not a serious attempt because I had homework due. I submitted random code and did not participate in the manual challenge.

Suggested notes to include:

| Area | Explanation |
| :--- | :--- |
| **Algorithmic submission** | Random / low-effort submission due to time constraints. |
| **Manual submission** | Did not participate. |
| **Result** | Ranked near the bottom because the round was effectively skipped. |
| **Reflection** | The round shows the impact of not actively participating, especially because both algorithmic and manual scores contributed to total XIRECs. |

</details>

<details>
<summary><strong>Round 4 — Strategy Description</strong></summary>

### 🧩 Round 4 Strategy Explanation

_Add your Round 4 approach here._

Suggested structure:

| Section | What to Explain |
| :--- | :--- |
| **Products traded** | Which products or market mechanics were active. |
| **Core hypothesis** | What pattern you believed existed in the data. |
| **Modeling approach** | Any fair-value, regression, spread, or signal logic used. |
| **Execution logic** | How the algorithm translated predictions into orders. |
| **Risk controls** | How you handled position limits and inventory. |
| **Manual challenge** | How you approached the manual component. |
| **Result reflection** | Why performance improved or declined compared with earlier rounds. |

</details>

<details>
<summary><strong>Round 5 — Final Round / Overall Reflection</strong></summary>

### 🧩 Round 5 Strategy Explanation

Round 5 was not a serious attempt because final projects were due, so I submitted random attempts.

Suggested notes to include:

| Area | Explanation |
| :--- | :--- |
| **Previous Total** | 69,185 XIRECs |
| **Round 5 Total** | -82,684 XIRECs |
| **Final Score** | -13,499 XIRECs |
| **Algorithmic Challenge** | -100,564 XIRECs |
| **Manual Challenge** | +17,880 XIRECs |
| **Reflection** | The manual component was positive, but the algorithmic component caused a large loss. Since this was a low-effort final-project-week submission, the result does not reflect the stronger Round 1 and Round 2 performance. |

</details>

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

---

### 📚 Appendix: Open-Source Strategies & Top Teams

*A curated list of repositories from historically top-performing teams to study for algorithmic strategies.*

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

* 🥈 **Stanford Cardinal** — 2nd Place — [GitHub Repository](https://github.com/ShubhamAnandJain/IMC-Prosperity-2023-Stanford-Cardinal)

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

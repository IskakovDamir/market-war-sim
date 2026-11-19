# Market War rules: every formula and constant

Source of truth is the code: `scripts/spec.py` (market data) and `scripts/sim.py` (mechanics). This file mirrors them. If the two ever disagree, the code wins and this file is the bug.

## Game shape

- 5 companies, 5 segments, 12 channels, 14 action cards.
- 3 checkpoints = 3 quarters. Checkpoint N decides quarter N.
- Budgets are for the whole game. Money is never refunded.
- The sim is deterministic: `random.Random(seed)` with seed 7. Random draws, in order: one `uniform(-1, 1)` per channel with spend > 0 (company order lovable, bolt, v0, base44, rork; channel order as written in the move), one `randint(1, 6)` per viral card at its position in that company's turn.

## Market data (scripts/spec.py)

| Segment | id | Size | WTP $/mo | Base paid share |
| --- | --- | --- | --- | --- |
| Студенты и новички | stud | 120000 | 8 | 0.06 |
| Фаундеры без кода | fnd | 40000 | 40 | 0.30 |
| Дизайнеры и продакты | des | 25000 | 30 | 0.22 |
| Разработчики | dev | 30000 | 25 | 0.15 |
| Малый бизнес и агентства | smb | 25000 | 60 | 0.25 |

| Company | id | Budget | List price | Paid stud/fnd/des/dev/smb | Free | Start MRR | AI cost $/user/mo paid/free |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Lovable | lovable | 1000000 | 25 | 1500/3500/1500/800/1700 | 50000 | 225000 | 7/1.5 |
| Bolt | bolt | 600000 | 25 | 1200/1200/300/900/400 | 30000 | 100000 | 8/1.5 |
| v0 | v0 | 400000 | 20 | 200/500/1300/900/100 | 20000 | 60000 | 6/1.0 |
| Base44 | base44 | 400000 | 30 | 200/700/100/200/1300 | 12000 | 75000 | 7/1.5 |
| Rork | rork | 150000 | 25 | 100/450/50/50/150 | 5000 | 20000 | 8/1.5 |

Start MRR = sum of paid x list price. Market start MRR = 480000, Lovable share 46.9%. Starting free users are split across segments in the same proportion as paid users.

Cost per new user, $ (lo-hi). n/a = the channel does not work in that segment.

| Channel | id | Min bid | Delay (this q / +1 / +2) | Target | Var | stud | fnd | des | dev | smb |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Таргет в соцсетях | social | 10000 | 1.0 | 0.7 | 0.10 | 4-10 | 25-60 | 30-70 | 60-140 | 20-50 |
| Короткие видео | shorts | 5000 | 1.0 | 0.3 | 0.40 | 2-6 | 20-50 | 25-60 | 70-160 | 40-100 |
| Креаторы и блогеры | creators | 15000 | 1.0 | 0.7 | 0.30 | 5-12 | 15-40 | 20-45 | 30-70 | 40-90 |
| Поисковая реклама | search | 10000 | 1.0 | 0.7 | 0.10 | 15-30 | 20-45 | 30-60 | 25-50 | 12-30 |
| Telegram-чаты и каналы | telegram | 5000 | 1.0 | 0.5 | 0.15 | 3-8 | 10-30 | 30-60 | 25-60 | 15-40 |
| SEO и контент | seo | 20000 | 0.2/0.5/0.3 | 0.5 | 0.10 | 3-8 | 8-20 | 10-25 | 6-15 | 8-20 |
| AI-поиск (GEO) | geo | 20000 | 0.3/0.7 | 0.5 | 0.10 | 6-15 | 6-15 | 10-25 | 5-12 | 10-25 |
| Сообщество и хакатоны | community | 25000 | 0.5/0.5 | 0.6 | 0.10 | 2-6 | 10-25 | 15-35 | 8-20 | 40-100 |
| Партнёрства и платформы | partners | 30000 | 0.0/1.0 | 0.9 | 0.10 | 3-10 | 10-30 | 20-50 | 20-50 | 15-40 |
| Продажи | sales | 40000 | 1.0 | 1.0 | 0.10 | n/a | 150-300 | 120-250 | n/a | 80-200 |
| Engineering as marketing и open source | eam | 30000 | 0.3/0.7 | 0.6 | 0.10 | 4-10 | 8-20 | 15-30 | 3-8 | 15-35 |
| Ивенты и выступления | events | 30000 | 1.0 | 0.8 | 0.15 | 10-25 | 15-40 | 25-50 | 25-60 | 30-70 |

Users that land after quarter 3 are lost: partners money in Q3 burns, SEO in Q3 delivers 20%, GEO, community and EaM in Q3 deliver 30% to 50%.

## Constants (scripts/sim.py)

| Name | Value | Meaning |
| --- | --- | --- |
| POOL_SHARE | 0.35 | max share of a segment that can arrive at all companies together in one quarter |
| BASE_CHURN | 0.25 | paid churn per quarter |
| FREE_CHURN | 0.20 | free churn per quarter |
| LOOK | 0.10 | share of a company's paid users in a segment that look at alternatives each quarter |
| ACTION_COST | decoy 10000, upsell 15000, referral 20000, viral 50000, onboarding 30000, copy 60000, attack 30000, exclusive 60000 | card prices; price_cut, free_tier, overpromise, team_deal are free; custom = max(20000, cost); mna = its price |
| ASSET_SCORE | bolt: stud +1, dev +1; rork: fnd +1, smb +1 | permanent score bonus |
| Auction | +15% cost per other team | social and search only |
| Below min bid | 30% effect | any channel |
| Consistency cost | 1 -> x1.00, 0.5 -> x1.10, 0 -> x1.25 | cost per user |
| Telegram spam | spend > 60000 in a quarter -> -1 score everywhere | |
| Referral | 6% of active users x avg score / 6, $10 per invite | |
| Viral | d6: 5 or 6 -> +15000 users, 1 to 4 -> +2000 | |

## One quarter, in order

### 0. Input check
Unknown company ids are dropped and listed in `res["warnings"]`. Unknown channels, unknown cards and cards missing a field they need (`target`, `seg`, `partner`; for mna `target` with `price`, or `buyer`) are dropped with a log line, are not charged and have no effect.

### 1. Missing submissions
A company without a move this quarter replays its previous move (first quarter: one plan "Pro" at list price, icp `fnd`, all scores 5) with `spend = {}`, `actions = []`, `consistency = 1`.

### 2. M&A
A buyer action `{"id": "mna", "target": T, "price": P}` is accepted when T's move this quarter has `{"id": "mna", "buyer": <buyer>}` and `P >= 3 x 3 x paid(T) x list_price(T)` (three quarterly revenues). Accepted: T's owner becomes the buyer, P is added to the buyer's spent. T keeps playing its own moves as the buyer's brand. In final scoring the buyer and every company it owns are one group.

### 3. Effective score per segment
```
score = AI score (default 5)
      + asset bonus (ASSET_SCORE)
      + 0.5 in the ICP if the company played events last quarter
      - 1 everywhere if consistency == 0
      - 1 everywhere if telegram spend > 60000
      - 1 everywhere in the quarter after an overpromise
      + 0.5 in seg for a team_deal that the partner also declared (pointing back)
      + 1 in seg for each copy card; the copied rival loses 50% of its asset bonus there
      - 0.5 everywhere for each copy card once the company has played copy twice or more in the game
clamped to [1, 10]
```

### 4. Exclusive partner
The first `{"id": "exclusive", "seg": S}` claim wins segment S for the rest of the game: partners cost x0.6 for the owner and x1.3 for everyone else in S.

### 5. Budget
```
cards  = sum of card prices this quarter (a second decoy is free and does nothing)
left   = budget - spent  (+ remaining budget of every company this one owns)
if channels + cards > left:  every channel is scaled by k = max(0, (left - cards) / channels)
spent += channels + cards
```

### 6. Acquisition, per channel with spend > 0
```
effective = spend if spend >= min bid else 0.3 x spend
sales with no plan >= $50: nothing happens, money is still spent
reach[s]  = size(s) / mid cost(s)            for segments the channel works in
alloc[s]  = effective x (1 - target) x reach[s] / sum(reach)
alloc[icp]+= effective x target               (if the channel works in the ICP)
otherwise   alloc[s] += effective x target x 0.5 x reach[s] / sum(reach)   (the other half is lost)
u         = uniform(-1, 1), one draw per channel
cost[s]   = hi - (hi - lo) x (score[s] - 1) / 9
          x consistency factor
          x (1 + 0.15 x other teams with social/search >= min bid on this ICP)   social, search
          / (1 + 0.2 x (quarter - 1))                                           geo
          x 0.7                                                                 community, Lovable
          x 0.6                                                                 partners, v0 in des and dev, Base44 in smb
          x 0.6 owner / x 1.3 others                                            partners in an exclusive segment
users[s]  = alloc[s] / cost[s] x (1 + var x u), split over quarters by the delay fractions
```
Community spend sets a churn bonus of 0.2 for this and next quarter. Events spend gives +0.5 score in the ICP next quarter. Sales users go to a separate sales pool.

Viral card: users = 15000 or 2000, spread over segments by `size / (lo + hi)` of the shorts channel, land this quarter. Referral card: `invites = (paid + free) x 0.06 x avg(score) / 6`, spread by the company's current user mix, `$10 x invites` added to spent.

### 7. Arrivals
```
arrivals[s] = users landing this quarter
            x 1.4 with free_tier
            x 0.6 if no free plan
```

### 8. Pool cap
For each segment, if all companies' arrivals plus sales arrivals exceed `0.35 x size`, every company is scaled by the same factor.

### 9. Conversion
```
price      = chosen price for the segment: the highest paid plan <= 1.3 x WTP, else the cheapest paid plan; 0 if only free plans
rate       = 0 if price == 0, else
             base_paid x clamp((WTP / price) ^ 0.7, 0.3, 1.5) x (0.7 + 0.06 x score)
             x 0.75 free_tier x 1.10 onboarding x 1.30 overpromise x 1.4 no free plan
             capped at 0.9
new paid   = arrivals x rate + 0.6 x sales arrivals (if price > 0)
new free   = arrivals x (1 - rate) + 0.4 x sales arrivals
```
Cohort ARPU per segment:
```
new customers pay  price x 1.15 (decoy, from the quarter it was played) x 1.10 (upsell, same)
existing customers keep their ARPU; if price < their ARPU they drop to price
ARPU = (old paid x old ARPU + new paid x new price) / (old paid + new paid)
```
Custom card with `"as": X` applies X's conversion effect.

### 10. Switching (paid users only)
```
look        = 0.10 x paid(c, s)
attack on c in s by a:  score(a, s) > score(c, s)  -> look moves from c to a
                        otherwise                  -> 5% of a's paid in s moves to c
attractiveness(x, s) = score(x, s) - 0.5 x log2(price(x, s) / WTP(s))   (no paid plan -> price 999)
best rival = highest attractiveness; if best - attractiveness(c) >= 1, look moves from c to best
```

### 11. Churn
```
paid churn = 0.25 x (1 - community bonus) x 0.7 with onboarding
free churn = 0.20
overpromise: after churn, half of this quarter's new paid leave (spread by current paid mix)
```

### 12. Metrics per quarter
`users = paid + free`, `MRR = sum(paid[s] x ARPU[s])`, `CAC = quarter spend / new paid` (None if new paid <= 1), `AI cost = 3 x (paid x paid cost + free x free cost)` (reported, not used in scoring), `budget left = budget - spent`.

## Final score (sim.final_scores)

Companies are grouped by owner. Market total MRR counts every company once.

| Role | Goal formula (0..100) |
| --- | --- |
| Lovable | `100 - 6 x max(0, 40 - revenue share %)`, floor 0 |
| Bolt | `100 x (final MRR / start MRR - 1)`, clamped 0..100 (double = 100) |
| v0 | 100 if #1 by revenue in `des`, else `100 x own / best` |
| Base44 | same in `smb` |
| Rork | `100 x share of ICP segment revenue / 0.20`, capped 100; ICP from checkpoint 1 (`state.icps`, default `fnd`) |

```
efficiency = (sum over quarters of 3 x MRR  -  3 x start MRR x quarters) / max(1, spent)
eff score  = 100 x efficiency / best efficiency, floor 0
final      = 0.7 x goal + 0.3 x eff score
```
An acquired company shows its owner's goal and final. The +5 prediction bonus is stored in `state.bonus` and added on the final dashboard only.

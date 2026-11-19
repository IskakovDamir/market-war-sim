# Scoring rubric: AI scores and consistency

The host (Claude) turns each team's doc into a move. Two numbers are judgment calls: the **score 1..10 per segment** and **consistency 0 / 0.5 / 1**. Everything else in the move is copied from the doc (plans, spend, cards) or mapped mechanically (ICP, card ids).

## What a score does in the sim

For one segment, the score moves two things:

- **Cost per new user**: `hi - (hi - lo) x (score - 1) / 9`. Score 1 pays the top of the channel range, 10 pays the bottom. Each point is 1/9 of the range, roughly 5% to 10% cheaper users.
- **Paid conversion**: factor `0.7 + 0.06 x score`. Score 1 gives 0.76, 5 gives 1.00, 10 gives 1.30.

It also decides attacks (attacker needs a strictly higher score than the target in that segment) and switching (attractiveness = score minus a price penalty).

The sim adds on its own: asset bonuses (Bolt +1 stud/dev, Rork +1 fnd/smb), events bonus, team deals, copy cards, consistency 0 penalty, Telegram spam and overpromise penalties. **Do not bake any of these into the AI score.**

## Inputs per team

Read the open part of the doc for this checkpoint: positioning, main ad, ad visual, first screen (headline, subheadline, button), plans and prices, public announcement. Read ICP and war type from the closed part only to understand intent: a segment is not scored higher just because the team named it ICP.

For each segment keep the market card in view (scripts/spec.py):

| Segment | WTP | What it values | Where it is |
| --- | --- | --- | --- |
| stud | $8 | бесплатный старт, простота, обучение | TikTok, YouTube, Discord, хакатоны, Telegram |
| fnd | $40 | быстро до рабочего MVP с оплатой и базой | X, YouTube, Telegram-чаты стартапов, AI-поиск |
| des | $30 | красивый результат, контроль дизайна | LinkedIn, Figma-комьюнити, рассылки |
| dev | $25 | качество кода, экспорт, нет привязки | GitHub, Reddit, X, AI-поиск |
| smb | $60 | надёжность, поддержка, хостинг, местные платежи | поиск, Instagram, партнёры, продажи |

## Procedure: one segment at a time

Start every segment at **5** and apply four fits. Each fit is +2, +1, 0, -1 or -2.

Price level is not a fit: the sim already prices it in through `(WTP / price) ^ 0.7` in conversion and the price term in switching. Scoring it again would count it twice. The Offer fit only judges packaging.

| Fit | +2 | +1 | 0 | -1 | -2 |
| --- | --- | --- | --- | --- | --- |
| Positioning | names this segment and its outcome, with a sharp contrast to an alternative | speaks to this segment's values without naming it | generic ("for everyone", "build apps faster") | aimed at another segment, neutral for this one | contradicts this segment's values (e.g. "no code needed" for dev, "enterprise" for stud) |
| Ad (25 words, result over features) | concrete result this segment wants, with a number or time frame | right result, vague | feature list or slogan | result this segment does not care about | confusing, over 25 words, or promises the product cannot keep |
| First screen | headline, subheadline and button continue the ad's promise for this segment, clear next step | consistent, weaker button | generic | disconnected from the ad | contradicts the ad |
| Offer | plans are packaged the way this segment buys (free start for stud and dev, a team or business tier for smb) and say what this segment gets | packaging fits, plan names say little | neutral | missing what the segment expects (no free plan for stud or dev) | no paid plan this segment can buy and no free plan |

Only one fit may reach +2 unless the move is clearly aimed at that segment: a doc that is generic everywhere tops out around 7. Then clamp to 1..10 and round to an integer (halves are fine when torn).

Anchors to sanity check the result:

| Score | Meaning |
| --- | --- |
| 9-10 | this segment would forward the ad to a friend; every element is specific to it |
| 7-8 | clear fit, one weak element |
| 5-6 | generic; nothing wrong, nothing for this segment in particular |
| 3-4 | aimed elsewhere; this segment would scroll past |
| 1-2 | actively repels this segment |

A typical move has one or two segments at 7-8, two at 5-6 and one or two at 3-4. A move with every segment at 8+ is a red flag: a sharp positioning cannot please everyone.

### Worked example: samples/team_doc_filled_rork.md, checkpoint 1

Positioning "Для фаундеров, которым нужно мобильное приложение, мы лучший выбор: App Store за неделю, в отличие от Lovable". Ad "Твоё приложение в App Store через неделю". First screen "Настоящее мобильное приложение / iOS и Android из одного описания / Начать". Plans Free and Pro $25.

| Segment | Positioning | Ad | First screen | Offer | Score |
| --- | --- | --- | --- | --- | --- |
| fnd | +2 named, outcome, contrast with Lovable | +1 result with a time frame | 0 headline is about the product, not the founder's outcome | 0 Free and Pro, nothing founder specific | 8 |
| smb | +1 an App Store presence is what a local business wants | 0 | 0 | 0 | 6 |
| stud | 0 | 0 | 0 | 0 free plan exists | 5 |
| des | 0 | 0 | 0 | 0 | 5 |
| dev | -1 "из одного описания" reads as no code, no export | 0 | 0 | 0 | 4 |

This gives the sample move `{"stud": 5, "fnd": 8, "des": 5, "dev": 4, "smb": 6}`. The asset bonus (+1 fnd and smb) is added by the sim, not here.

## Consistency

Compare the positioning at this checkpoint with the previous one. Checkpoint 1 is always 1.

| Value | When | Sim effect |
| --- | --- | --- |
| 1 | same target and same core promise; wording, numbers or proof points may change | none |
| 0.5 | same target with a different core promise, or same promise for a wider or narrower audience | cost per user x1.10 |
| 0 | different target segment or a different product category | cost per user x1.25 and -1 score everywhere |

The public dashboard flags any text change as "позиционирование изменилось". That flag is not the score: a reworded sentence with the same meaning is still 1.

## Mechanical mapping from the doc

| Doc field | Move key |
| --- | --- |
| ICP free text | `icp`: the segment id it names (Студенты -> stud, Фаундеры -> fnd, Дизайнеры/продакты -> des, Разработчики -> dev, Малый бизнес/агентства -> smb). At checkpoint 1 this is Rork's goal segment for the whole game |
| Тарифы table | `plans` (live.py fills it if omitted) |
| Бюджет по каналам | `spend` (live.py fills it if omitted). Check the parsed numbers against the doc: a typo there is real money |
| Карточки table | `actions`, by card name: Ценовой удар price_cut, Щедрый бесплатный тариф free_tier, Тариф-приманка decoy, Апселл upsell, Реферальная программа referral, Вирусная акция viral, Онбординг onboarding, Скопировать фичу copy, Сравнительная атака attack, Эксклюзивный партнёр exclusive, Обещание сверх продукта overpromise. Rival and segment go to `target` and `seg` |
| Сделка с другой командой | `team_deal` with `partner` and `seg`, only when the partner's doc has the same deal |
| Покупка компании | `mna`: buyer writes `target` and `price`, seller writes `buyer`. Both docs must agree |
| Своё действие | `custom` with `cost` (min 20000) and `as` = the closest ready card. Reject it (leave it out) if it is stronger than that card |
| Обещание сверх продукта | add `overpromise` also when the ad or first screen promises what the product cannot do, even if the card was not written: that is the trap |

Missing team: leave it out of the file. The sim replays its previous offer with zero spend and no cards.

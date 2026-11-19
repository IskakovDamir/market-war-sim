# Moves JSON schema

Two files use the same move object:

1. **Checkpoint file** for `live.py moves <cp> <file>`: one object keyed by company id. Example: `samples/moves_cp1.json`.
2. **Full game file** for `report.py` and `sim.run`: `{"quarters": [checkpoint1, checkpoint2, checkpoint3]}`. Example: `samples/test_moves.json`.

Company ids: `lovable`, `bolt`, `v0`, `base44`, `rork`.
Segment ids: `stud`, `fnd`, `des`, `dev`, `smb`.
Channel ids: `social`, `shorts`, `creators`, `search`, `telegram`, `seo`, `geo`, `community`, `partners`, `sales`, `eam`, `events`.
Action ids: `price_cut`, `free_tier`, `decoy`, `upsell`, `referral`, `viral`, `onboarding`, `copy`, `attack`, `exclusive`, `overpromise`, `team_deal`, `mna`, `custom`.

## Move object

| Key | Type | Required | Default when missing | Meaning |
| --- | --- | --- | --- | --- |
| `plans` | array of `{"name": str, "price": number}` | no | live.py: plans parsed from the team doc; sim: one plan "Pro" at list price | up to 3 plans, `price` in $/month, `0` = free plan |
| `icp` | segment id | yes at checkpoint 1 | `fnd` | main segment; at checkpoint 1 it also fixes Rork's goal segment |
| `scores` | object segment id -> number 1..10 | yes | 5 per missing segment | AI fit score per segment, see scoring-rubric.md |
| `consistency` | 1, 0.5 or 0 | yes | 1 | positioning vs previous checkpoint, see scoring-rubric.md |
| `spend` | object channel id -> dollars | no | live.py: parsed from the team doc; sim: none | channel budget this quarter |
| `actions` | array of action objects | no | none | cards played this quarter |

Extra keys are ignored by the sim, so notes such as `"why": "..."` are allowed.

## Action objects

| id | Shape | Cost |
| --- | --- | --- |
| `price_cut` | `{"id": "price_cut"}` (the cut itself is the lower price in `plans`) | 0 |
| `free_tier` | `{"id": "free_tier"}` | 0 |
| `decoy` | `{"id": "decoy"}` | 10000, once per game |
| `upsell` | `{"id": "upsell"}` | 15000 |
| `referral` | `{"id": "referral"}` | 20000 + $10 per invite |
| `viral` | `{"id": "viral"}` | 50000 |
| `onboarding` | `{"id": "onboarding"}` | 30000 |
| `copy` | `{"id": "copy", "target": company, "seg": segment}` | 60000 |
| `attack` | `{"id": "attack", "target": company, "seg": segment}` | 30000 |
| `exclusive` | `{"id": "exclusive", "seg": segment}` | 60000 |
| `overpromise` | `{"id": "overpromise"}` | 0 |
| `team_deal` | `{"id": "team_deal", "partner": company, "seg": segment}` (both teams must write it, each naming the other) | 0 |
| `mna`, buyer side | `{"id": "mna", "target": company, "price": dollars}` | the price |
| `mna`, seller side | `{"id": "mna", "buyer": company}` | 0 |
| `custom` | `{"id": "custom", "cost": dollars, "as": action id}` (the closest ready card; effect is never stronger than it) | max(20000, cost) |

## JSON Schema (draft 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "market-war/checkpoint-moves",
  "type": "object",
  "propertyNames": {"enum": ["lovable", "bolt", "v0", "base44", "rork"]},
  "additionalProperties": {"$ref": "#/$defs/move"},
  "$defs": {
    "seg": {"enum": ["stud", "fnd", "des", "dev", "smb"]},
    "company": {"enum": ["lovable", "bolt", "v0", "base44", "rork"]},
    "move": {
      "type": "object",
      "properties": {
        "plans": {
          "type": "array", "maxItems": 3,
          "items": {"type": "object", "required": ["name", "price"],
                    "properties": {"name": {"type": "string"}, "price": {"type": "number", "minimum": 0}}}
        },
        "icp": {"$ref": "#/$defs/seg"},
        "scores": {
          "type": "object",
          "propertyNames": {"$ref": "#/$defs/seg"},
          "additionalProperties": {"type": "number", "minimum": 1, "maximum": 10}
        },
        "consistency": {"enum": [0, 0.5, 1]},
        "spend": {
          "type": "object",
          "propertyNames": {"enum": ["social", "shorts", "creators", "search", "telegram", "seo",
                                     "geo", "community", "partners", "sales", "eam", "events"]},
          "additionalProperties": {"type": "number", "minimum": 0}
        },
        "actions": {"type": "array", "items": {"$ref": "#/$defs/action"}}
      }
    },
    "action": {
      "type": "object", "required": ["id"],
      "oneOf": [
        {"properties": {"id": {"enum": ["price_cut", "free_tier", "decoy", "upsell", "referral",
                                        "viral", "onboarding", "overpromise"]}}},
        {"properties": {"id": {"enum": ["copy", "attack"]}, "target": {"$ref": "#/$defs/company"},
                        "seg": {"$ref": "#/$defs/seg"}}, "required": ["target", "seg"]},
        {"properties": {"id": {"const": "exclusive"}, "seg": {"$ref": "#/$defs/seg"}}, "required": ["seg"]},
        {"properties": {"id": {"const": "team_deal"}, "partner": {"$ref": "#/$defs/company"},
                        "seg": {"$ref": "#/$defs/seg"}}, "required": ["partner"]},
        {"properties": {"id": {"const": "mna"}, "target": {"$ref": "#/$defs/company"},
                        "price": {"type": "number"}}, "required": ["target", "price"]},
        {"properties": {"id": {"const": "mna"}, "buyer": {"$ref": "#/$defs/company"}}, "required": ["buyer"]},
        {"properties": {"id": {"const": "custom"}, "cost": {"type": "number", "minimum": 20000},
                        "as": {"type": "string"}}, "required": ["cost"]}
      ]
    }
  }
}
```

The full game file wraps checkpoint objects: `{"quarters": {"type": "array", "maxItems": 3, "items": <checkpoint-moves>}}`.

## Example checkpoint file

```json
{
  "rork": {
    "plans": [{"name": "Free", "price": 0}, {"name": "Pro", "price": 25}, {"name": "Max", "price": 60}],
    "icp": "fnd",
    "scores": {"stud": 5, "fnd": 8, "des": 5, "dev": 4, "smb": 6},
    "consistency": 1,
    "spend": {"telegram": 20000, "creators": 20000},
    "actions": [
      {"id": "attack", "target": "lovable", "seg": "fnd"},
      {"id": "team_deal", "partner": "v0", "seg": "fnd"}
    ]
  },
  "v0": {
    "icp": "des",
    "scores": {"stud": 4, "fnd": 5, "des": 8, "dev": 7, "smb": 3},
    "consistency": 1,
    "actions": [{"id": "team_deal", "partner": "rork", "seg": "fnd"}]
  }
}
```

Here v0 has no `plans` and no `spend`: `live.py moves` fills both from v0's ingested doc for that checkpoint.


## Invalid input

The sim never crashes on a bad id:

- unknown company id: the move is skipped and listed in `res["warnings"]`;
- unknown channel id: the spend is skipped, not charged, and a log line is added;
- unknown action id, or a card missing `target`/`seg`/`partner`: the card is skipped, not charged, and a log line is added.

Logs appear in the "события" block of the final dashboard, so fix typos before the final render.

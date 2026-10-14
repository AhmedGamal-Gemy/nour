# nour — product map (visual)

The session model from `PLAN.md` §2b, drawn instead of described. If text and
picture disagree, the text in `PLAN.md` wins — update both.

## 1. The session loop

```mermaid
flowchart LR
    A["1. AGENDA<br/>app suggests today's portion"] --> B["2. BEGIN<br/>you recite from memory, unprompted"]
    B --> C["3. TRACK<br/>app silent, knows every word"]
    C --> D{"stall?"}
    D -- "no" --> E["5. CONTINUE<br/>run never restarts"]
    D -- "yes" --> F["4. LADDER<br/>wait, hint, word"]
    F --> E
    E --> G{"finished?"}
    G -- "no" --> C
    G -- "yes" --> H["6. SCORE<br/>one run, one segment score"]
    H --> I["7. WISDOM<br/>mutashabihat if clean"]
```

## 2. The prompt ladder

```mermaid
flowchart TD
    S["stall detected"] --> W["RUNG 0: wait about 1s<br/>mic open, app silent"]
    W --> R0{"recovered?"}
    R0 -- "yes" --> C["carry on (-0.5 stumble)"]
    R0 -- "no" --> H["RUNG 1: first letters on screen<br/>hint, -0.5"]
    H --> R1{"remembered?"}
    R1 -- "yes" --> C2["carry on"]
    R1 -- "no" --> F["RUNG 2: qari speaks the word<br/>mic muted, -1.0"]
    F --> C3["carry on"]
    C --> N["next words..."]
    C2 --> N
    C3 --> N
```

## 3. The three segments and the two cursors

```mermaid
flowchart LR
    subgraph TODAY["today's session"]
        direction TB
        N["1. NEAR OLD<br/>yesterday, hidden"] --> L["2. LONG TERM<br/>revision cursor, hidden"]
        L --> W["3. NEW<br/>next in sequence, visible"]
    end
    M["MEMORIZE cursor"] --> W
    R["REVISION cursor"] --> L
    G["gap: measured, not chosen"] -.-> R
    D["decay outruns cursor?"] -. "yes: reset cursor back" .-> R
```

## Reading guide

- Diagram 1 is the whole product. Everything else is detail.
- Diagram 2 is the only intelligent interaction. One tunable: the wait duration.
- Diagram 3 is the scheduler. Mechanical order, one measured gap, one override.

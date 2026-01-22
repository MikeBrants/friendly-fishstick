# Guide Multi-Agent Cursor — FINAL TRIGGER v2

**Version:** 1.0  
**Date:** 2026-01-22

---

## Vue d'ensemble

Le systeme multi-agent permet de paralleliser le travail de validation des assets crypto via plusieurs agents specialises communiquant par fichiers Markdown.

### Architecture actuelle (simplifiee - 3 agents)

```
┌─────────────────────────────────────────────────────────┐
│                      WORKFLOW                           │
│                                                         │
│   Casey (Orchestrateur)                                 │
│      │                                                  │
│      ▼ [TASK] dans casey-quant.md                       │
│   Jordan (Developer)                                    │
│      │                                                  │
│      ▼ [RUN_COMPLETE] dans jordan-dev.md                │
│   Sam (QA)                                              │
│      │                                                  │
│      ▼ [VALIDATION] dans sam-qa.md                      │
│   Casey (Verdict)                                       │
│      │                                                  │
│      ▼ PROD / BLOCKED / RETEST                          │
└─────────────────────────────────────────────────────────┘
```

### Architecture etendue (5 agents - optionnel)

```
Casey (Orchestrateur)
  ├─> Jordan (Dev Backtest) ──> Sam (QA Guards)
  ├─> Alex (Lead Pipelines)
  ├─> Riley (Operations)
  └─> Taylor (Infrastructure)
```

---

## Architecture

### Agents principaux (actifs)

| Agent | Role | Fichier comms | Fichier rules | Status |
|-------|------|---------------|---------------|--------|
| **Casey** | Orchestrateur, decisions finales | `comms/casey-quant.md` | `.cursor/rules/casey-orchestrator.mdc` | ✅ Actif |
| **Jordan** | Execute pipelines, documente runs | `comms/jordan-dev.md` | `.cursor/rules/jordan-backtest.mdc` | ✅ Actif |
| **Sam** | Valide 7 guards, recommande verdict | `comms/sam-qa.md` | `.cursor/rules/sam-guards.mdc` | ✅ Actif |

### Agents etendus (optionnels - fichiers existants)

| Agent | Role | Fichier comms | Usage |
|-------|------|---------------|-------|
| **Alex** | Lead pipelines multi-asset | `comms/alex-lead.md` | Pipelines batch (EGLD, IMX) |
| **Riley** | Operations, runs paralleles | `comms/riley-ops.md` | Execution multi-asset (YGG, CELO) |
| **Taylor** | Infrastructure, monitoring | `comms/taylor-infra.md` | Runs infrastructure (ARKM, AR) |

**Note:** Les agents Alex/Riley/Taylor sont des variantes de Jordan pour paralleliser plusieurs assets. Le workflow standard utilise Casey → Jordan → Sam.

### Fichiers cles

```
friendly-fishstick/
├── .cursor/rules/
│   ├── MASTER_PLAN.mdc          # Vision globale (alwaysApply)
│   ├── global-quant.mdc         # Regles quant (alwaysApply)
│   ├── casey-orchestrator.mdc   # Role Casey
│   ├── jordan-backtest.mdc      # Role Jordan
│   └── sam-guards.mdc           # Role Sam
├── comms/
│   ├── casey-quant.md           # Taches assignees (Casey)
│   ├── jordan-dev.md            # Logs des runs (Jordan)
│   ├── sam-qa.md                # Validations guards (Sam)
│   ├── alex-lead.md             # Pipelines batch (Alex - optionnel)
│   ├── riley-ops.md             # Operations paralleles (Riley - optionnel)
│   └── taylor-infra.md          # Infrastructure runs (Taylor - optionnel)
└── status/
    └── project-state.md         # Source de verite (Casey)
```

---

## Quand utiliser quels agents ?

### Workflow standard (3 agents) - Recommande

**Utilise:** Casey → Jordan → Sam

**Quand:**
- Validation d'1-2 assets a la fois
- Besoin de supervision etendue
- Debugging ou retest avec variants

**Avantages:** Controle fin, tracabilite complete, moins de confusion

### Workflow parallele (5 agents) - Optionnel

**Utilise:** Casey assigne a Alex/Riley/Taylor en parallele, puis Sam valide

**Quand:**
- Batch de 3+ assets similaires
- Pas besoin de supervision fine
- Execution en arriere-plan

**Avantages:** Parallelisation, plus rapide pour batchs

**Inconvenients:** Moins de controle, risque de confusion si plusieurs agents ecrivent en meme temps

**Note:** Les agents Alex/Riley/Taylor suivent le meme pattern que Jordan mais pour des assets differents. Ils peuvent tourner en parallele si tu as plusieurs fenetres Cursor.

---

## Modes d'operation

### Mode A: Manuel (micro-management)

Tu lances chaque agent un par un, tu attends qu'il finisse, tu lances le suivant.

**Avantages:** Controle total, pas de race condition  
**Inconvenients:** Lent, tu dois relancer manuellement

### Mode B: Semi-autonome (recommande)

Tu lances les 3 agents dans 3 fenetres Cursor. Chaque agent boucle et relit les fichiers comms toutes les 30s.

**Avantages:** Plus rapide, agents travaillent en parallele  
**Inconvenients:** Tu dois surveiller, relancer si blocage

### Mode C: Full autonome (Background Agents)

Tu lances Jordan et Sam en Background Agent Cursor. Casey reste manuel comme superviseur.

**Avantages:** Execution asynchrone, pas besoin de surveiller  
**Inconvenients:** Privacy (code envoye remote), timeouts sur longs runs, moins de controle

---

## Comment lancer un cycle

### Etape 1: Preparer la tache (Casey)

Ecris la tache dans `comms/casey-quant.md`:

```markdown
## [HH:MM] [TASK] @Casey -> @Jordan

**Context:** [Pourquoi cet asset, quel probleme resoudre]
**Asset:** XXX
**Variant:** baseline | medium_distance_volume | disp=78
**Hypothese:** [Ce qu'on espere]

**Command:**
\`\`\`bash
python scripts/run_full_pipeline.py \
  --assets XXX \
  --workers 6 \
  --enforce-tp-progression \
  --run-guards
\`\`\`

**Criteres succes:** 7/7 guards, WFE > 0.6
**Next:** @Jordan execute
```

### Etape 2: Lancer les agents

Ouvre 3 fenetres/tabs Cursor et colle ces prompts:

**Fenetre 1 — Casey:**
```
Tu es Casey. Applique @.cursor/rules/casey-orchestrator.mdc et @.cursor/rules/global-quant.mdc.
Lis @status/project-state.md et @comms/*.md.
Supervise le cycle en cours. Boucle jusqu'au verdict final.
```

**Fenetre 2 — Jordan:**
```
Tu es Jordan. Applique @.cursor/rules/jordan-backtest.mdc et @.cursor/rules/global-quant.mdc.
Lis @comms/casey-quant.md pour la tache assignee.
Execute et documente dans @comms/jordan-dev.md. Boucle tant qu'il y a des taches.
```

**Fenetre 3 — Sam:**
```
Tu es Sam. Applique @.cursor/rules/sam-guards.mdc et @.cursor/rules/global-quant.mdc.
Lis @comms/jordan-dev.md pour les runs a valider.
Valide les 7 guards dans @comms/sam-qa.md. Boucle tant qu'il y a des runs.
```

### Etape 3: Superviser

- Surveille les fichiers `comms/*.md` pour voir la progression
- Relance un agent s'il semble bloque (pas d'update > 5 min)
- Casey rend le verdict final et met a jour `status/project-state.md`

---

## Format des messages

### Casey — Assigner une tache

```markdown
## [HH:MM] [TASK] @Casey -> @Jordan
**Context:** ...
**Asset:** XXX
**Command:** ...
**Next:** @Jordan execute
```

### Casey — En attente

```markdown
## [HH:MM] [WAITING] @Casey
**En attente de:** @Jordan (run) | @Sam (validation)
**Timeout:** 60 min max
```

### Casey — Verdict final

```markdown
## [HH:MM] [DECISION] @Casey
**Asset:** XXX
**Verdict:** PROD | BLOCKED | RETEST
**Raison:** ...
**Action:** Mise a jour status/project-state.md
```

### Jordan — Run complete

```markdown
## [HH:MM] [RUN_COMPLETE] @Jordan -> @Sam
**Asset:** XXX
**Mode:** baseline | medium_distance_volume
**Duration:** X min
**Outputs:**
- outputs/multiasset_scan_YYYYMMDD_HHMMSS.csv
- outputs/guards/XXX_guard_results.json
**Next:** @Sam valide
```

### Sam — Validation

```markdown
## [HH:MM] [VALIDATION] @Sam -> @Casey
**Asset:** XXX

| Guard | Seuil | Valeur | Status |
|-------|-------|--------|--------|
| guard001 | < 0.05 | 0.02 | PASS |
| guard002 | < 10% | 8.5% | PASS |
| ... | ... | ... | ... |

**Verdict:** 7/7 PASS
**Recommendation:** PROD
**Next:** @Casey verdict final
```

---

## Regles critiques

### 7 Guards (tous obligatoires)

| Guard | ID | Seuil |
|-------|:---|-------|
| MC p-value | guard001 | < 0.05 |
| Sensitivity variance | guard002 | < 10% |
| Bootstrap CI lower | guard003 | > 1.0 |
| Top10 trades % | guard005 | < 40% |
| Stress1 Sharpe | guard006 | > 1.0 |
| Regime mismatch | guard007 | < 1% |
| WFE | - | > 0.6 |

### Seuils additionnels

- OOS Sharpe > 1.0 (target > 2.0)
- OOS Trades > 60
- TP Progression: tp1 < tp2 < tp3, gaps >= 0.5

### Resultats suspects

**CHALLENGER** si:
- Sharpe > 4.0
- WFE > 2.0
- MaxDD < 1%

---

## Arbres de decision

### Choix du displacement

```
Asset type?
├── Majeur (BTC, ETH) ──────────> d52
├── L2/Infrastructure (OP) ─────> d78
├── Meme/Fast (DOGE, JOE) ──────> d26
└── Inconnu ────────────────────> d52, ajuster si WFE < 0.6
```

### Si guard FAIL

```
Quel guard?
├── WFE < 0.6 ──────────> Tester autre displacement
├── MC p > 0.05 ────────> Plus de trials (200+)
├── Sensitivity > 10% ──> Filter mode (medium_distance_volume)
├── Bootstrap CI < 1 ───> Donnees insuffisantes
├── Top10 > 40% ────────> Trop peu de trades
└── Autre ──────────────> BLOCKED, documenter raison
```

### Filter modes

| Mode | Usage |
|:-----|:------|
| baseline | Premier test (defaut) |
| medium_distance_volume | Winner ETH, reduit sensitivity |
| light_kama / light_distance | Tests intermediaires |
| conservative | Dernier recours |

---

## Troubleshooting

### Agent bloque (pas d'update > 5 min)

1. Verifie si le run est encore en cours (terminal actif?)
2. Relis le dernier message dans comms/ pour comprendre l'etat
3. Relance l'agent avec le meme prompt

### Race condition (2 agents ecrivent en meme temps)

Symptome: Messages melanges ou perdus dans comms/*.md

Solution:
- En mode semi-auto, un seul agent agit a la fois
- Casey attend que Jordan finisse avant de donner nouvelle tache
- Sam attend que Jordan documente avant de valider

### Run trop long (> 2h)

1. Verifie si le pipeline est vraiment bloque ou juste lent
2. Si bloque: Ctrl+C et relance avec moins de trials
3. Documente le timeout dans jordan-dev.md

### Resultats incoherents

1. Verifie la date du run (post 2026-01-22 12H00?)
2. Verifie que `--enforce-tp-progression` etait actif
3. Compare avec les scans precedents dans outputs/

---

## Commandes utiles

### Lancer un pipeline

```bash
python scripts/run_full_pipeline.py \
  --assets XXX \
  --workers 6 \
  --trials-atr 150 \
  --trials-ichi 150 \
  --enforce-tp-progression \
  --run-guards
```

### Avec filter mode

```bash
--optimization-mode medium_distance_volume
```

### Avec displacement fixe

```bash
--fixed-displacement 78
```

### Download data

```bash
python scripts/download_data.py --assets XXX YYY ZZZ
```

### Verifier derniers outputs

```bash
ls -lt outputs/multiasset_scan_*.csv | head -5
ls -lt outputs/multiasset_guards_summary_*.csv | head -5
```

---

## Checklist demarrage

- [ ] Fichiers .mdc ont frontmatter correct (`---` pas `***`)
- [ ] Fichiers comms/ existent (casey-quant.md, jordan-dev.md, sam-qa.md)
- [ ] status/project-state.md est a jour
- [ ] Data disponible pour l'asset (sinon download first)
- [ ] 3 fenetres Cursor pretes avec prompts

---

## Exemples de cycles complets

### Cycle reussi (AVAX -> PROD)

1. Casey: `[TASK] AVAX medium_distance_volume`
2. Jordan: `[RUN_COMPLETE] 45 min, Sharpe 2.31, WFE 0.74`
3. Sam: `[VALIDATION] 7/7 PASS, recommande PROD`
4. Casey: `[DECISION] AVAX -> PROD, maj project-state.md`

### Cycle echec (UNI -> BLOCKED)

1. Casey: `[TASK] UNI medium_distance_volume`
2. Jordan: `[RUN_COMPLETE] 52 min, Sharpe 1.12, WFE 0.42`
3. Sam: `[VALIDATION] 5/7 FAIL (WFE, bootstrap, stress)`
4. Casey: `[DECISION] UNI -> BLOCKED, WFE insuffisant meme avec filtres`

### Cycle retest (HBAR disp=78)

1. Casey: `[TASK] HBAR baseline d52`
2. Jordan: `[RUN_COMPLETE] sens 13% > 10%`
3. Sam: `[VALIDATION] 5/7 FAIL, recommande RETEST d78`
4. Casey: `[TASK] HBAR disp=78`
5. Jordan: `[RUN_COMPLETE] sens 7%`
6. Sam: `[VALIDATION] 7/7 PASS`
7. Casey: `[DECISION] HBAR -> PROD`

---

## Notes finales

### Ce qui marche bien

- Communication par fichiers = tracabilite complete
- Agents specialises = moins d'erreurs
- Boucle autonome = moins de micro-management

### Limitations actuelles

- Pas de vrai parallelisme (agents sequentiels)
- Pas de lockfile (race condition possible)
- Cursor agents s'arretent apres reponse (pas de vraie boucle infinie)

### Evolutions possibles

- CrewAI/LangGraph pour orchestration Python native
- Lockfiles dans comms/locks/ anti-race-condition
- Dashboard monitoring temps reel

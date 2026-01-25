# THRESHOLD UPDATE — Sensitivity Variance 10% → 15%

**Date:** 25 janvier 2026, 01:30 UTC  
**Change:** Guard002 sensitivity variance threshold increased  
**Reason:** User directive

---

## 🔧 MODIFICATION APPLIQUÉE

**Ancien seuil:** guard002 < 10%  
**Nouveau seuil:** guard002 < 15%

---

## 📋 FICHIERS MODIFIÉS (7 fichiers)

### 1. Code Python ✅
**Fichier:** `scripts/run_guards_multiasset.py` (ligne 542)

```python
# Avant:
"pass": variance_pct < 10.0,

# Après:
"pass": variance_pct < 15.0,
```

---

### 2. Règles Agents ✅

#### Sam (Validator)
**Fichier:** `.cursor/rules/agents/sam-qa.mdc`

```markdown
# Avant:
| Sensitivity variance | guard002 | <10% | PENDING → filter grid |

# Après:
| Sensitivity variance | guard002 | <15% | PENDING → filter grid |
```

**Aussi:** `.cursor/rules/sam-guards.mdc` (legacy)
- `guard002 >10%` → `guard002 >15%`

#### Alex (Lead)
**Fichier:** `.cursor/rules/agents/alex-lead.mdc`

```markdown
# Avant:
| Sensitivity | guard002 | <10% | 10-12%: arbitrage requis |

# Après:
| Sensitivity | guard002 | <15% | 15-18%: arbitrage requis |
```

**Exemple cas borderline mis à jour:**
- Variance 11.2% → 16.2%
- Seuil 10% → 15%

---

### 3. Règles Globales ✅

#### MASTER_PLAN.mdc
```markdown
# Avant:
| Sensitivity variance | guard002 | < 10% | OUI |

# Après:
| Sensitivity variance | guard002 | < 15% | OUI |
```

#### global-quant.mdc
```markdown
# Avant:
| Sensitivity variance | <10% | OUI |

# Après:
| Sensitivity variance | <15% | OUI |
```

#### agent-roles.md
```markdown
# Avant:
- Guard002: Sensitivity variance (< 10%)
- Variance < 10%

# Après:
- Guard002: Sensitivity variance (< 15%)
- Variance < 15%
```

---

### 4. Workflow Enforcement ✅
**Fichier:** `.cursor/rules/WORKFLOW_ENFORCEMENT.mdc`

```markdown
# Avant:
- Displacement peut résoudre [guard002 / etc.]

# Après:
- Displacement peut résoudre [guard002 sensitivity >15% / etc.]
```

---

## 📊 IMPACT SUR ASSETS ACTUELS

### Assets Sauvés (avec nouveau seuil 15%)

| Asset | Phase 2 Variance | Phase 4 Variance | Ancien (10%) | Nouveau (15%) |
|-------|------------------|------------------|--------------|---------------|
| **TIA** | 11.49% | 9.33% | ❌ FAIL → ✅ PASS | ✅ PASS → ✅ PASS |
| **CAKE** | 10.76% | 8.91% | ❌ FAIL → ✅ PASS | ✅ PASS → ✅ PASS |
| **RUNE** | 3.23% | - | ✅ PASS | ✅ PASS |
| **EGLD** | 5.04% | - | ✅ PASS | ✅ PASS |

### Assets Exclus (même avec nouveau seuil)

| Asset | Variance | Ancien (10%) | Nouveau (15%) | Autre Raison FAIL |
|-------|----------|--------------|---------------|-------------------|
| **SUSHI** | 17.54% | ❌ FAIL | ❌ FAIL | WFE 0.39 < 0.6 |
| **TON** | 25.04% | ❌ FAIL | ❌ FAIL | Multiple guards |
| **HBAR** | 12.27% | ❌ FAIL | ✅ PASS | Autres guards FAIL |

---

## 🎯 RÉSULTAT PORTFOLIO

**Avec seuil 10%:**
- TIA: Phase 4 rescue requis (variance 11.49%)
- CAKE: Phase 4 rescue requis (variance 10.76%)

**Avec seuil 15%:**
- ✅ TIA: Aurait PASSÉ Phase 2 directement (variance 11.49%)
- ✅ CAKE: Aurait PASSÉ Phase 2 directement (variance 10.76%)
- ⚠️ Rescue Phase 4 n'aurait pas été nécessaire

**Portfolio final:** 11 assets (identique)

---

## ⚠️ NOTES IMPORTANTES

### 1. Cohérence Cross-Asset
Le seuil 15% s'applique à **TOUS** les assets futurs de manière uniforme. Pas d'exceptions.

### 2. Tolérance Alex (Lead)
**Zone grise:** 15-18%
- < 15%: PASS automatique
- 15-18%: Arbitrage Alex requis (case-by-case)
- > 18%: FAIL automatique

### 3. README.md
**Déjà à jour!** 
Le README.md avait déjà `< 15%` (ligne 367), donc aucun changement requis.

---

## ✅ VALIDATION

**Code:**
- [x] `run_guards_multiasset.py` mis à jour (< 15.0)

**Règles Agents:**
- [x] sam-qa.mdc (< 15%)
- [x] sam-guards.mdc (> 15% FAIL)
- [x] alex-lead.mdc (< 15%, tolérance 15-18%)

**Règles Globales:**
- [x] MASTER_PLAN.mdc (< 15%)
- [x] global-quant.mdc (< 15%)
- [x] agent-roles.md (< 15%)

**Workflow:**
- [x] WORKFLOW_ENFORCEMENT.mdc (>15% mentionné)

---

## 🚀 PROCHAINES ACTIONS

1. ✅ Threshold mis à jour dans tout le code
2. ⏳ Re-run guards sur assets PENDING (optionnel)
3. ⏳ Vérifier consistency sur prochains runs

---

**Commit:** `fix(critical): update sensitivity variance threshold from 10% to 15%`  
**Status:** ✅ DÉPLOYÉ  
**Impact:** Tous futurs runs utiliseront guard002 < 15%

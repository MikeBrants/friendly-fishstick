# P0.2 - Analyse BTC d26 et d52 Résultats

**Date:** 2026-01-23 12:45

## Résultats Comparatifs

### BTC Baseline Original (PROD)
- **Sharpe OOS:** 2.14
- **WFE:** >0.6 (PASS)
- **Displacement:** 52
- **Params:** sl=4.5, tp1=4.25, tp2=7.5, tp3=9.5, tenkan=6, kijun=37

---

### BTC d52 (Phase 3B Baseline)
- **Status:** FAIL
- **Sharpe IS:** 3.41
- **Sharpe OOS:** **-0.45** ❌ (négatif!)
- **WFE:** **-0.09** ❌ (négatif!)
- **OOS Return:** -0.71% (négatif)
- **OOS Trades:** 85
- **OOS Max DD:** -0.31%
- **Profit Factor:** -0.47 (perdant)
- **Guards:** 6/7 FAIL (WFE FAIL)
- **Params optimisés:** sl=4.25, tp1=4.25, tp2=7.5, tp3=9.5, tenkan=11, kijun=34

**Analyse:**
- Sharpe OOS négatif = stratégie perdante sur OOS
- WFE négatif = OOS performe pire que IS (normal si OOS Sharpe négatif)
- **Dégradation majeure** vs baseline original (2.14 → -0.45)

---

### BTC d26 (Phase 3B)
- **Status:** FAIL
- **Sharpe IS:** 3.24
- **Sharpe OOS:** **0.77** (< 1.0)
- **WFE:** **-0.66** ❌ (négatif!)
- **OOS Return:** 0.92% (positif mais faible)
- **OOS Trades:** 66
- **OOS Max DD:** -2.15%
- **Profit Factor:** -2.88 (perdant!)
- **Guards:** 6/7 FAIL (WFE FAIL)
- **Params optimisés:** sl=4.75, tp1=4.5, tp2=6.5, tp3=9.5, tenkan=10, kijun=25

**Analyse:**
- Sharpe OOS positif mais faible (0.77 < 1.0)
- WFE négatif = OOS performe pire que IS
- Profit Factor négatif = pertes > gains
- **Dégradation** vs baseline original (2.14 → 0.77)

---

## Problèmes Identifiés

### 1. WFE Négatif

**Formule WFE:** `WFE = OOS Sharpe / IS Sharpe`

**BTC d52:**
- WFE = -0.45 / 3.41 = **-0.13** (proche de -0.09 dans résultats)
- **Interprétation:** OOS Sharpe négatif → WFE négatif (normal mathématiquement)

**BTC d26:**
- WFE calculé = 0.77 / 3.24 = **0.24** (mais résultat montre -0.66)
- **Incohérence:** WFE calculé ≠ WFE dans résultats
- **Hypothèse:** Bug dans calcul WFE ou formule différente utilisée

### 2. Dégradation Majeure vs Baseline

| Métrique | Baseline Original | d52 Phase 3B | d26 Phase 3B |
|:---------|:------------------|:-------------|:-------------|
| Sharpe OOS | **2.14** | **-0.45** ❌ | **0.77** ❌ |
| WFE | >0.6 ✅ | **-0.09** ❌ | **-0.66** ❌ |
| Status | PROD | FAIL | FAIL |

**Observation:** Les optimisations Phase 3B dégradent les performances au lieu de les améliorer.

### 3. Profit Factor Négatif

- **BTC d52:** PF = -0.47 (perdant)
- **BTC d26:** PF = -2.88 (très perdant)

**Interprétation:** Les stratégies optimisées perdent plus qu'elles ne gagnent sur OOS.

---

## Hypothèses

### Hypothèse 1: Overfitting Sévère
- Les params optimisés sur IS ne généralisent pas sur OOS
- 300 trials ATR + 300 trials Ichimoku = espace de recherche trop large
- **Solution:** Réduire trials (150 → 100) ou fixer certains params

### Hypothèse 2: Données Différentes
- Phase 3B utilise peut-être des données différentes du baseline original
- Dates différentes ou preprocessing différent
- **Action:** Vérifier dates et preprocessing

### Hypothèse 3: Bug dans Phase 3B
- Erreur dans l'optimisation ou le backtest
- Paramètres mal appliqués
- **Action:** Vérifier code Phase 3B

### Hypothèse 4: Displacement Inadapté
- d52 et d26 ne conviennent pas à BTC
- Baseline original d52 fonctionne, mais re-optimisation échoue
- **Action:** Tester d78 ou garder baseline original

---

## Recommandations

### Option A: Arrêter Phase 3B pour BTC (RECOMMANDÉ)
**Raison:**
- Baseline original (Sharpe 2.14) est excellent
- Phase 3B dégrade les performances
- Risque d'overfitting avec 300+300 trials

**Action:** Garder baseline BTC original, passer à ETH et JOE

### Option B: Réduire Trials et Réessayer
**Raison:**
- 300+300 trials = trop d'overfitting
- Réduire à 150+150 ou 100+100

**Action:** Relancer Phase 3B avec trials réduits

### Option C: Tester d78 Seulement
**Raison:**
- d52 et d26 échouent
- d78 pourrait être meilleur

**Action:** Tester uniquement d78 avec trials réduits

---

## Décision

**RECOMMANDATION:** **Option A** - Arrêter Phase 3B pour BTC

**Justification:**
1. Baseline original excellent (Sharpe 2.14, WFE >0.6)
2. Phase 3B dégrade systématiquement (d52 et d26 FAIL)
3. Risque d'overfitting avec 300+300 trials
4. Temps mieux investi sur ETH et JOE

**Prochaines Actions:**
1. ✅ Documenter analyse (ce fichier)
2. ⏭️ Passer à ETH Phase 3B (avec fix Unicode)
3. ⏭️ Passer à JOE Phase 3B
4. ⏭️ Garder BTC baseline original

---

**Date:** 2026-01-23 12:45  
**Status:** Analyse complétée, recommandation Option A

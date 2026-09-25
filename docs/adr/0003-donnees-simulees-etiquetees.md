# ADR-0003 — Données simulées : étiquetées, jamais substituées en silence

**Statut** : acceptée

## Contexte
En v1, un connecteur sans identifiants retombait sur un générateur aléatoire, et l'extraction Google Ads « réelle » retournait une liste vide sans erreur. Des chiffres inventés pouvaient donc se mêler à des chiffres réels sans que rien ne les distingue.

## Décision
- Le mode est explicite (`--mode simulated|real`, défaut `simulated`) ; `real` sans identifiants, ou pour Google Ads (non implémenté), **échoue**.
- Chaque ligne raw porte `data_mode`, propagé jusqu'aux marts et testé (`accepted_values`).
- Le générateur est **déterministe** (graine, campagne, jour) : mêmes lignes à chaque exécution, donc ingestion reproductible et tests stables.

## Conséquence
Tout tableau de bord public doit filtrer `data_mode = 'real'` ou l'afficher. La documentation dit ce qui est simulé (Google Ads) au lieu de le sous-entendre.

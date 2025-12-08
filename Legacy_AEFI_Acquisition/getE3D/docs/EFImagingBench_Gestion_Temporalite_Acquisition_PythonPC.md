MOC :
Source : [[Luis Saluden]]
Projets : [[PROJET ASSOCE]] [[PROJET Banc de Test Python]]
Simulation :
Tags : #NoteAtomique
Date : 2025-07-04
***

# Contexte / Problème

Dans les systèmes d'acquisition pilotés par Python sur PC, la gestion du temps est cruciale pour :
- Reconstituer précisément la série temporelle des données acquises
- Détecter les pertes ou irrégularités d'échantillonnage
- Synchroniser l'acquisition avec d'autres équipements (ex : moteurs)

Problèmes rencontrés :
- Les timestamps logiciels classiques (`datetime.now()`) manquent de précision et peuvent être affectés par des changements système.
- L'utilisation d'un simple index d'échantillon + fréquence ne permet pas de détecter les pertes ou irrégularités (suppose un flux parfait).
- L'absence de timestamp hardware rend la reconstruction temporelle dépendante de la méthode logicielle.

# Développement / Solution

**Méthode recommandée pour une gestion temporelle robuste et précise côté PC :**

1. **Utiliser `time.perf_counter()`**
   - Fournit une mesure monotone et très précise du temps (résolution microseconde).
   - Indépendant de l'horloge système (pas d'impact des changements d'heure).

2. **Prendre le timestamp au plus près de la réception effective du sample**
   - Juste après la lecture du hardware, dans le thread d'acquisition.
   - Permet de refléter toute perte ou latence dans la série temporelle.

3. **Stocker pour chaque sample :**
   - Un index d'échantillon (incrémenté à chaque réception)
   - Le timestamp relatif (ex : `t_sample = time.perf_counter() - t0`)
   - Les valeurs ADC

4. **Exporter dans le CSV**
   - Inclure les colonnes `index` et `timestamp` en plus des données.
   - Exemple :
     ```
     index,timestamp,ADC1_Ch1,ADC1_Ch2,...
     0,0.000000,100,200,...
     1,0.001002,101,201,...
     ```

5. **Avantages :**
   - Toute perte ou irrégularité d'échantillonnage est visible dans la colonne `timestamp`.
   - Permet une analyse post-traitement fiable (détection de pertes, calcul du débit effectif, etc.).
   - Synchronisation facile avec d'autres équipements pilotés par le même script.

**Conclusion :**
Cette méthode est la plus robuste et précise côté PC en l'absence de timestamp hardware. Elle doit être privilégiée pour toute acquisition scientifique nécessitant une traçabilité temporelle fiable. 
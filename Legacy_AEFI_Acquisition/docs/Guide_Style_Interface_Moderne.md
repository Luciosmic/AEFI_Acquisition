MOC :
Source : [[Luis Saluden]]
Projets : [[PROJET ASSOCE]] [[PROJET Banc de Test Python]]
Simulation :
Tags : #NoteAtomique
Date : 2025-06-10
***

# Guide de Style pour Interfaces Graphiques Modernes et Élégantes

## 🎨 Philosophie Générale

Créer des interfaces **modernes, élégantes et fonctionnelles** avec une approche **Dark Mode** et des éléments visuels **intuitifs**.

---

## 🌟 Principes de Base

### 1. **Thème Sombre (Dark Theme)**
```python
# Utiliser le style Fusion de PyQt5
app.setStyle('Fusion')

# Palette de couleurs sombres
palette = QPalette()
palette.setColor(QPalette.Window, QColor(53, 53, 53))           # Fond principal gris foncé
palette.setColor(QPalette.WindowText, QColor(255, 255, 255))    # Texte blanc
palette.setColor(QPalette.Base, QColor(25, 25, 25))             # Fond des champs très sombre
palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))    # Fond alternatif
palette.setColor(QPalette.Text, QColor(255, 255, 255))          # Texte blanc
palette.setColor(QPalette.Button, QColor(53, 53, 53))           # Boutons gris foncé
palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))    # Texte des boutons blanc
palette.setColor(QPalette.Highlight, QColor(42, 130, 218))      # Sélection bleu moderne
```

### 2. **Emojis et Iconographie**
- **TOUJOURS** utiliser des emojis pertinents pour rendre l'interface plus visuelle
- Exemples : 🔴 Temps Réel, 📈 Graphiques, 🧲 Magnétomètre, 📐 Accéléromètre, 🌀 Gyroscope, 📏 LIDAR
- Les emojis doivent être **cohérents** et **descriptifs**

### 3. **Organisation en Onglets**
```python
tab_widget = QTabWidget()
tab_widget.addTab(realtime_tab, "🔴 Temps Réel")
tab_widget.addTab(graphs_tab, "📈 Graphiques")
```

---

## 🎯 Couleurs et Cohérence Visuelle

### 1. **Palette de Couleurs Modernes**
```python
COLORS = {
    'primary_blue': '#2E86AB',      # Bleu principal
    'accent_red': '#E63946',        # Rouge accent  
    'success_green': '#2A9D8F',     # Vert succès
    'warning_orange': '#F77F00',    # Orange attention
    'info_purple': '#A23B72',       # Violet information
    'axis_x': '#0000FF',           # X = Bleu
    'axis_y': '#FFA500',           # Y = Orange/Jaune
    'axis_z': '#FF0000'            # Z = Rouge
}
```

### 2. **Cohérence des Axes (pour capteurs 3D)**
- **X = Bleu (#0000FF)**
- **Y = Jaune/Orange (#FFA500)**  
- **Z = Rouge (#FF0000)**
- Appliquer cette convention partout : graphiques, labels, valeurs

---

## 🏗️ Structure et Composants

### 1. **Groupes Logiques (QGroupBox)**
```python
group = QGroupBox(f"{emoji} {nom}")
group.setStyleSheet(f"""
    QGroupBox {{
        font-weight: bold;
        border: 2px solid {couleur_theme};
        border-radius: 8px;
        margin-top: 10px;
        padding-top: 10px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
    }}
""")
```

### 2. **Boutons Expressifs**
```python
# Boutons avec emojis et états clairs
connect_btn = QPushButton("🔌 Connecter")  # État disconnecté
connect_btn = QPushButton("🔌 Déconnecter")  # État connecté
stream_btn = QPushButton("▶️ Démarrer")
stream_btn = QPushButton("⏸️ Arrêter")
```

### 3. **Barre de Contrôle Horizontale**
- Placer les contrôles principaux dans une barre horizontale en haut
- Ordre logique : Connexion → Configuration → Actions → Réglages

---

## 📊 Graphiques et Visualisation

### 1. **Style pyqtgraph**
```python
plot_widget = pg.PlotWidget(title=title)
plot_widget.setBackground('w')  # Fond blanc pour contraste
plot_widget.setLabel('left', 'Valeur')
plot_widget.setLabel('bottom', 'Temps (s)')
plot_widget.showGrid(x=True, y=True)  # Grille pour lisibilité

# Ajouter une légende
plot_widget.addLegend(offset=(10, 10))
```

### 2. **Courbes avec Couleurs Cohérentes**
```python
curve_x = plot_widget.plot(pen=pg.mkPen('b', width=2), name='X (Bleu)')
curve_y = plot_widget.plot(pen=pg.mkPen('y', width=2), name='Y (Jaune)')
curve_z = plot_widget.plot(pen=pg.mkPen('r', width=2), name='Z (Rouge)')
```

---

## ✨ Détails d'Élégance

### 1. **Typographie**
```python
# Valeurs importantes en gras et plus grandes
value_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #couleur;")

# Labels descriptifs colorés
label.setStyleSheet("color: #couleur; font-weight: bold;")
```

### 2. **Feedback Utilisateur**
```python
# Barre de statut pour les messages
status_bar = QStatusBar()
status_bar.showMessage("État: Message informatif")

# Messages contextuels lors des actions
```

### 3. **Bordures Arrondies**
```css
border-radius: 8px;  /* Angles arrondis modernes */
```

---

## 🔧 Fonctionnalités UX Essentielles

### 1. **États Visuels Clairs**
- Boutons qui changent de texte/couleur selon l'état
- Désactivation logique des contrôles non disponibles
- Feedback immédiat des actions

### 2. **Organisation Logique**
- **Onglet "Temps Réel"** : Valeurs actuelles + Informations système
- **Onglet "Graphiques"** : Visualisation temporelle + Contrôles avancés
- **Panneau de Contrôle** : Actions principales toujours visibles

### 3. **Contrôles Intuitifs**
- Spinboxes pour valeurs numériques
- ComboBox pour sélections multiples
- Boutons toggle avec états visuels clairs

---

## 📱 Layout et Responsive

### 1. **Grilles Équilibrées**
```python
# Pour 4 éléments : grille 2x2
layout.addWidget(widget1, 0, 0)
layout.addWidget(widget2, 0, 1)
layout.addWidget(widget3, 1, 0)
layout.addWidget(widget4, 1, 1)
```

### 2. **Espacement et Padding**
- Marges cohérentes (10px standard)
- Groupement logique des éléments
- Espacement vertical pour la respiration

---

## 🎭 Exemples d'Application

### Capteurs 3D
```python
# Widget avec couleur thématique et emoji
sensor_widget = SensorWidget("Magnétomètre", "#E63946", "🧲")

# Valeurs colorées selon les axes
x_value.setStyleSheet("color: #0000FF; font-weight: bold;")  # Bleu
y_value.setStyleSheet("color: #FFA500; font-weight: bold;")  # Orange
z_value.setStyleSheet("color: #FF0000; font-weight: bold;")  # Rouge
```

### Contrôles d'Actions
```python
# Boutons avec progression logique
init_btn = QPushButton("🚀 Initialiser")
stream_btn = QPushButton("▶️ Démarrer")
clear_btn = QPushButton("🗑️ Effacer")
```

---

## ✅ Checklist de Style

- [ ] **Thème sombre** appliqué avec palette cohérente
- [ ] **Emojis pertinents** dans tous les titres/boutons
- [ ] **Couleurs d'axes cohérentes** (X=Bleu, Y=Orange, Z=Rouge)
- [ ] **QGroupBox** avec bordures colorées et arrondies
- [ ] **Onglets** pour organiser les fonctionnalités
- [ ] **Barre de statut** pour le feedback
- [ ] **Graphiques** avec fond blanc et légendes
- [ ] **Boutons expressifs** avec états visuels
- [ ] **Typographie** hiérarchisée (tailles, gras)
- [ ] **Layout équilibré** en grilles ou lignes logiques

---

## 🚀 Philosophie Finale

> **"Modernité, Élégance, Fonctionnalité"**
> 
> Chaque élément doit être :
> - **Visuellement attrayant** (couleurs, emojis, bordures)
> - **Intuitivement compréhensible** (labels clairs, organisation logique)  
> - **Fonctionnellement efficace** (actions directes, feedback immédiat)

L'interface doit donner l'impression d'être un **outil professionnel moderne** tout en restant **accessible et agréable** à utiliser. 
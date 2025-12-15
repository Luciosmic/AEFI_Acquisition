#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script minimal pour visualiser les données de corrélation Interface Python vs Oscilloscope
Usage: python correlation_mesures.py
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

def main():
    # Données de mesure
    mesures = [1, 2, 3, 4, 5]
    interface_python = [90, 70, 50, 35, 15]  # mV
    oscilloscope = [600, 490, 370, 260, 140]  # mV
    
    # Calcul des écarts
    ecarts = [abs(osc - interf) for osc, interf in zip(oscilloscope, interface_python)]
    ecarts_pourcent = [(ecart/osc)*100 for ecart, osc in zip(ecarts, oscilloscope)]
    
    # Régression linéaire
    slope, intercept, r_value, p_value, std_err = stats.linregress(interface_python, oscilloscope)
    
    # Création du graphique
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # Graphique 1: Corrélation avec droite de régression
    ax1.scatter(interface_python, oscilloscope, color='blue', s=100, alpha=0.7, label='Données mesurées')
    
    # Droite de régression
    x_reg = np.linspace(min(interface_python), max(interface_python), 100)
    y_reg = slope * x_reg + intercept
    ax1.plot(x_reg, y_reg, 'r-', linewidth=2, label=f'Régression: y = {slope:.2f}x + {intercept:.1f}')
    
    ax1.set_xlabel('Interface Python (mV)')
    ax1.set_ylabel('Oscilloscope (mV)')
    ax1.set_title('Corrélation Interface Python vs Oscilloscope')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Graphique 2: Écarts en pourcentage
    ax2.bar(mesures, ecarts_pourcent, color='red', alpha=0.7)
    ax2.set_xlabel('Numéro de mesure')
    ax2.set_ylabel('Écart (%)')
    ax2.set_title('Écart relatif par mesure')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # Affichage des statistiques
    print(f"Écart moyen: {np.mean(ecarts):.1f} mV")
    print(f"Écart relatif moyen: {np.mean(ecarts_pourcent):.1f} %")
    print(f"Rapport moyen oscilloscope/interface: {np.mean([osc/interf for osc, interf in zip(oscilloscope, interface_python)]):.2f}")
    
    # Statistiques de régression
    print(f"\n=== Statistiques de régression ===")
    print(f"Pente (slope): {slope:.3f}")
    print(f"Ordonnée à l'origine (intercept): {intercept:.1f} mV")
    print(f"Coefficient de corrélation (R): {r_value:.3f}")
    print(f"R²: {r_value**2:.3f}")
    print(f"P-value: {p_value:.3e}")
    print(f"Erreur standard: {std_err:.3f}")

if __name__ == "__main__":
    main()
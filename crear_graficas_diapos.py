"""Genera figuras optimizadas para diapositivas con tema oscuro y estilo Spotify."""
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT_FIGS = ROOT / "outputs" / "figures"
OUT_FIGS.mkdir(parents=True, exist_ok=True)

# Estilo visual Spotify oscuro
plt.style.use('dark_background')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['text.color'] = '#FFFFFF'
plt.rcParams['axes.labelcolor'] = '#B3B3B3'
plt.rcParams['xtick.color'] = '#B3B3B3'
plt.rcParams['ytick.color'] = '#B3B3B3'

# 1. Gráfica de "El Ritmo del Éxito": Perfil Enérgico (Cluster 0) vs Acústico (Cluster 1)
fig, ax = plt.subplots(figsize=(8, 5.5), facecolor='#1E1E1E')
ax.set_facecolor('#1E1E1E')

features_norm = ['Bailabilidad\n(0-1)', 'Energía\n(0-1)', 'Valencia / Ánimo\n(0-1)', 'Carácter Acústico\n(0-1)', 'Popularidad\n(/100)']
c0_vals = [0.61, 0.76, 0.53, 0.08, 0.35]
c1_vals = [0.47, 0.30, 0.26, 0.82, 0.28]

x = np.arange(len(features_norm))
width = 0.35

rects1 = ax.bar(x - width/2, c0_vals, width, label='Cluster 0: Éxito Streaming (125 BPM, -6 dB)', color='#1DB954', edgecolor='#121212', alpha=0.95)
rects2 = ax.bar(x + width/2, c1_vals, width, label='Cluster 1: Acústico / Suave (108 BPM, -13 dB)', color='#50C8FF', edgecolor='#121212', alpha=0.9)

ax.set_title('El Ritmo del Éxito: Huella Acústica de los Perfiles', fontsize=14, fontweight='bold', pad=15, color='#FFFFFF')
ax.set_xticks(x)
ax.set_xticklabels(features_norm, fontsize=10)
ax.set_ylim(0, 1.05)
ax.grid(axis='y', linestyle='--', alpha=0.2, color='#FFFFFF')
ax.legend(frameon=True, facecolor='#282828', edgecolor='#1DB954', fontsize=9, loc='upper right')

for rect in rects1:
    h = rect.get_height()
    ax.annotate(f'{h:.2f}', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1DB954')
for rect in rects2:
    h = rect.get_height()
    ax.annotate(f'{h:.2f}', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#50C8FF')

plt.tight_layout()
p1 = OUT_FIGS / "diapo_ritmo_exito.png"
fig.savefig(p1, dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
plt.close(fig)

# 2. Gráfica comparativa de modelos: Silhouette en Espacio Común y Estabilidad
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4.5), facecolor='#1E1E1E')
ax1.set_facecolor('#1E1E1E')
ax2.set_facecolor('#1E1E1E')

models = ['K-Means\nOriginal', 'K-Means\nPCA', 'GMM\nOriginal', 'GMM\nPCA']
sil_scores = [0.2460, 0.2477, -0.0119, 0.0243]
colors = ['#1DB954', '#1ED760', '#FF5555', '#FF7777']

bars1 = ax1.bar(models, sil_scores, color=colors, width=0.55, edgecolor='#121212')
ax1.set_title('Silhouette en Espacio Común (Mayor es Mejor)', fontsize=11, fontweight='bold', color='#FFFFFF')
ax1.set_ylim(-0.05, 0.30)
ax1.axhline(0, color='#888888', linewidth=1)
ax1.grid(axis='y', linestyle='--', alpha=0.2)
for b in bars1:
    h = b.get_height()
    y_pos = h + 0.008 if h >= 0 else h - 0.025
    ax1.annotate(f'{h:.3f}', xy=(b.get_x() + b.get_width()/2, y_pos), ha='center', va='bottom', fontsize=9, fontweight='bold')

stability_models = ['K-Means\nSemillas', 'K-Means\nSubmuestras', 'GMM\nSemillas', 'GMM\nSubmuestras']
ari_scores = [1.000, 0.994, 0.566, 0.552]
ari_colors = ['#1DB954', '#1ED760', '#FFAA00', '#FF8800']

bars2 = ax2.bar(stability_models, ari_scores, color=ari_colors, width=0.55, edgecolor='#121212')
ax2.set_title('Estabilidad (ARI entre Réplicas)', fontsize=11, fontweight='bold', color='#FFFFFF')
ax2.set_ylim(0, 1.15)
ax2.grid(axis='y', linestyle='--', alpha=0.2)
for b in bars2:
    h = b.get_height()
    ax2.annotate(f'{h*100:.1f}%', xy=(b.get_x() + b.get_width()/2, h + 0.02), ha='center', va='bottom', fontsize=9, fontweight='bold')

plt.tight_layout()
p2 = OUT_FIGS / "diapo_comparativa_modelos.png"
fig.savefig(p2, dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
plt.close(fig)

print(f"Gráficas generadas exitosamente en:\n- {p1}\n- {p2}")

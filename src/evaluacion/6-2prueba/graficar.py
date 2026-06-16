import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 1. Carga y limpieza de datos reales
ficheros = {
    1: "latencia_carga_baja_1nodo.csv",
    4: "latencia_carga_media_4nodo.csv",
    8: "latencia_carga_alta_8nodo.csv",
    12: "latencia_carga_maxima_12nodo.csv"
}

escenarios = ['1 Nodo', '4 Nodos', '8 Nodos', '12 Nodos']
lat_red, lat_fog, lat_blockchain = [], [], []

for nodos, path in ficheros.items():
    df = pd.read_csv("resultados/" + path)
    lat_red.append(df['latencia_red'].clip(lower=0).mean())
    lat_fog.append(df['latencia_fog'].mean())
    lat_blockchain.append(df['latencia_blockchain'].mean())

# Convertir a arrays numéricos
lat_red = np.array(lat_red)
lat_fog = np.array(lat_fog)
lat_blockchain = np.array(lat_blockchain)

# -------------------------------------------------------------
# FIGURA COMPUESTA: PANEL DOBLE (TOTAL vs OVERHEAD LOCAL)
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# --- GRÁFICA 1: Latencia E2E Total (Barras Apiladas) ---
bars1 = ax1.bar(escenarios, lat_red, label='Red (Edge-to-Fog)', color='#3498db')
bars2 = ax1.bar(escenarios, lat_fog, bottom=lat_red, label='Procesamiento Fog', color='#e67e22')
bars3 = ax1.bar(escenarios, lat_blockchain, bottom=lat_red+lat_fog, label='Consenso Blockchain', color='#2ecc71')

ax1.set_title('A. Ciclo de Vida Completo E2E (ms)', fontsize=12, fontweight='bold', pad=10)
ax1.set_ylabel('Tiempo Total (Milisegundos)', fontsize=10)
ax1.grid(axis='y', linestyle='--', alpha=0.5)

# Añadir etiquetas de texto con el valor exacto solo a la Blockchain (ya que las otras son muy pequeñas)
for bar in bars3:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, bar.get_y() + yval/2, f'{int(yval)} ms', 
             ha='center', va='center', color='white', fontweight='bold', fontsize=9)

# --- GRÁFICA 2: Zoom de la Infraestructura Local (Sin Blockchain) ---
# Esto permite ver el impacto real de la concurrencia en tu pasarela Raspberry Pi
ax2.bar(escenarios, lat_red, label='Red (Edge-to-Fog)', color='#3498db', width=0.5)
ax2.bar(escenarios, lat_fog, bottom=lat_red, label='Procesamiento Fog', color='#e67e22', width=0.5)

ax2.set_title('B. Zoom: Sobrecarga en Capa Local (ms)', fontsize=12, fontweight='bold', pad=10)
ax2.set_ylabel('Tiempo Local (Milisegundos)', fontsize=10)
ax2.grid(axis='y', linestyle='--', alpha=0.5)
ax2.legend(loc='upper left')

# Añadir etiquetas con los valores numéricos exactos en la gráfica de Zoom
for i in range(len(escenarios)):
    # Etiqueta de Red
    ax2.text(i, lat_red[i]/2, f'{lat_red[i]:.1f} ms', ha='center', va='center', color='white', fontweight='bold', fontsize=9)
    # Etiqueta de Fog
    ax2.text(i, lat_red[i] + lat_fog[i] + 2, f'{lat_fog[i]:.1f} ms', ha='center', va='bottom', color='#d35400', fontweight='bold', fontsize=9)

plt.suptitle('Análisis de Escalabilidad y Latencia de la Arquitectura', fontsize=14, fontweight='bold', y=0.98)
plt.tight_layout()
plt.savefig('analisis_latencia_profesional.png', dpi=300)
plt.close()

print("Nueva gráfica compuesta generada en 'analisis_latencia_profesional.png'")

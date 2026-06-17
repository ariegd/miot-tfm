import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Rutas de los archivos del escenario propuesto (Fog)
ficheros_fog = {
    1: "latencia_carga_baja_1nodo.csv",
    4: "latencia_carga_media_4nodo.csv",
    8: "latencia_carga_alta_8nodo.csv",
    12: "latencia_carga_maxima_12nodo.csv"
}

# Cargar medias del escenario propuesto
escenarios_fog = ['Propuesto (1 Nodo)', 'Propuesto (4 Nodos)', 'Propuesto (8 Nodos)', 'Propuesto (12 Nodos)']
lat_red = []
lat_fog = []
lat_blockchain = []

for nodos, path in ficheros_fog.items():
    df = pd.read_csv("resultados/" + path)
    lat_red.append(df['latencia_red'].clip(lower=0).mean())
    lat_fog.append(df['latencia_fog'].mean())
    lat_blockchain.append(df['latencia_blockchain'].mean())

lat_red = np.array(lat_red)
lat_fog = np.array(lat_fog)
lat_blockchain = np.array(lat_blockchain)

# Cargar datos del escenario clásico directo (HTTP)
df_directo = pd.read_csv("resultados/latencia_directo_base.csv")
media_directo_e2e = df_directo['latencia_e2e_base'].mean()

# Configuración del gráfico comparativo
todos_los_escenarios = escenarios_fog + ['Clásico (11 Nodos Directos)']

plt.figure(figsize=(10, 6))

# Pintar las barras de la arquitectura propuesta (Apiladas)
plt.bar(escenarios_fog, lat_red, label='Red (Edge-to-Fog)', color='#3498db', width=0.5)
plt.bar(escenarios_fog, lat_fog, bottom=lat_red, label='Procesamiento Fog', color='#e67e22', width=0.5)
plt.bar(escenarios_fog, lat_blockchain, bottom=lat_red+lat_fog, label='Consenso Blockchain (EVM)', color='#2ecc71', width=0.5)

# Pintar la barra de la arquitectura clásica (Directa)
plt.bar(['Clásico (11 Nodos Directos)'], [media_directo_e2e], label='Latencia Directa Edge-to-Cloud', color='#e74c3c', width=0.5)

# Añadir etiquetas de texto con los valores totales sobre cada barra
totales_fog = lat_red + lat_fog + lat_blockchain
for i, total in enumerate(totales_fog):
    plt.text(i, total + 100, f'{int(total)} ms', ha='center', va='bottom', fontweight='bold', fontsize=9)

plt.text(4, media_directo_e2e + 100, f'{int(media_directo_e2e)} ms', ha='center', va='bottom', fontweight='bold', fontsize=9, color='#c0392b')

# Configuración estética formal
plt.title('Comparativa Global de Latencia E2E: Modelo Clásico vs Modelo Propuesto con Red Fog', fontsize=12, fontweight='bold', pad=15)
plt.xlabel('Configuración del Entorno de Pruebas', fontsize=10, labelpad=10)
plt.ylabel('Tiempo Total de Confirmación (Milisegundos)', fontsize=10, labelpad=10)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.legend(loc='upper left', frameon=True)
plt.ylim(0, max(max(totales_fog), media_directo_e2e) + 700)

plt.tight_layout()
plt.savefig('comparativa_modelos_latencia.png', dpi=300)
plt.close()

print("Gráfica comparativa guardada con éxito en 'comparativa_modelos_latencia.png'")

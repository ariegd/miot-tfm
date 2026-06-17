import pandas as pd
import matplotlib.pyplot as plt

# 1. Carga de los ficheros de datos
ficheros = {
    "1 Nodo": "latencia_carga_baja_1nodo.csv",
    "4 Nodos": "latencia_carga_media_4nodo.csv",
    "8 Nodos": "latencia_carga_alta_8nodo.csv",
    "12 Nodos": "latencia_carga_maxima_12nodo.csv"
}

datos_red = []
etiquetas = []

# 2. Extracción y filtrado de la columna de latencia de red
for escenario, path in ficheros.items():
    df = pd.read_csv("resultados/" + path)
    # Conservamos los valores reales incluyendo las fluctuaciones experimentales
    datos_red.append(df['latencia_red'])
    etiquetas.append(escenario)

# 3. Configuración del diagrama de cajas estadístico (Boxplot)
plt.figure(figsize=(9, 6))
# Se cambia 'labels' por 'tick_labels' debido a la actualización de Matplotlib
plt.boxplot(datos_red, tick_labels=etiquetas, patch_artist=True,
            boxprops=dict(facecolor='#3498db', color='#2c3e50', alpha=0.7),
            capprops=dict(color='#2c3e50', linewidth=1.5),
            whiskerprops=dict(color='#2c3e50', linestyle='--'),
            flierprops=dict(marker='o', markerfacecolor='#e74c3c', markersize=4, markeredgecolor='none'),
            medianprops=dict(color='#2ecc71', linewidth=2))

# 4. Ajuste de escala logarítmica debido a los picos severos de 14 y 18 segundos
plt.yscale('symlog', linthresh=100)

plt.title('Figura 6.3: Dispersión Estadística y Jitter en el Tramo de Red (Log Scale)', fontsize=11, fontweight='bold', pad=15)
plt.xlabel('Carga del Sistema (Nodos IoT Concurrentes)', fontsize=10)
plt.ylabel('Latencia de Red (Milisegundos)', fontsize=10)
plt.grid(True, which="both", linestyle='--', alpha=0.4)

# 5. Exportación del recurso gráfico para Overleaf
plt.tight_layout()
plt.savefig('jitter_red_boxplot.png', dpi=300)
plt.close()

print("Archivo 'jitter_red_boxplot.png' exportado correctamente para su inserción.")


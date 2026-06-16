# 6.2. Latencia del Canal de Red y Análisis Extremo a Extremo(E2E)

* **Métrica:** Latencia Acumulada E2E en milisegundos. Mide el ciclo de vida completo del dato: desde que el ESP32 genera la lectura de $eCO_2$, pasando por el envío CoAP, el procesamiento asíncrono en la Raspberry Pi 4, el consenso en la Blockchain, hasta que  un cliente web en el PC lee el dato indexado.


* **Enfoque Comparativo:** No midas solo el RTT de red. Compara la arquitectura propuesta con una arquitectura clásica descentralizada donde cada nodo IoT enviara directamente a la Blockchain mediante HTTP/HTTPS (Edge-to-Cloud directo).


* **Gráfica Recomendada:** Gráfico de áreas apiladas (Stacked Area Chart) que muestre qué porcentaje del tiempo total E2E se pierde en cada etapa (Red, Fog, Blockchain) a medida que aumenta la carga.

---
### Primer paso: Preparación del entorno hardware (Sincronización)
1. Antes de alterar líneas de código, es obligatorio mitigar el desfase de los relojes (clock drift) en tu banco de pruebas de 4 equipos (2 RPis, Portátil Validador y Portátil Edge).
```
sudo timedatectl set-ntp true
```
2. Inicializar el fichero CSV en la Raspberry Pi
```
echo "latencia_red,latencia_fog,latencia_blockchain" > resultados_latencia.csv
```
3. Para evitar que la siguiente prueba (Carga Media con 4 nodos) escriba encima o mezcle las filas, renombra el CSV del test de carga baja:
```
mv resultados_latencia.csv latencia_carga_baja_1nodo.csv
```

### Siguiente paso: Ejecución de las pruebas de carga
Con los scripts listos, ya se puede proceder a iniciar tus 4 fases experimentales de 5 minutos consecutivas para recopilar los registros limpios en el archivo `.csv`:  
1. Baja: Únicamente tu ESP32-C3 físico encendido.  
2. Media: ESP32-C3 físico + 3 terminales de `simular_sensor.py` corriendo en paralelo.  
3. Alta: ESP32-C3 físico + 7 terminales concurrentes de simulación.  
4. Máxima: ESP32-C3 físico + las 11 instancias simuladas.  

 

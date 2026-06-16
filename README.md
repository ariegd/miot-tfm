# 6.2. Latencia del Canal de Red y Análisis Extremo a Extremo(E2E)

* **Métrica:** Latencia Acumulada E2E en milisegundos. Mide el ciclo de vida completo del dato: desde que el ESP32 genera la lectura de $eCO_2$, pasando por el envío CoAP, el procesamiento asíncrono en la Raspberry Pi 4, el consenso en la Blockchain, hasta que  un cliente web en el PC lee el dato indexado.


* **Enfoque Comparativo:** No midas solo el RTT de red. Compara la arquitectura propuesta con una arquitectura clásica descentralizada donde cada nodo IoT enviara directamente a la Blockchain mediante HTTP/HTTPS (Edge-to-Cloud directo).


* **Gráfica Recomendada:** Gráfico de áreas apiladas (Stacked Area Chart) que muestre qué porcentaje del tiempo total E2E se pierde en cada etapa (Red, Fog, Blockchain) a medida que aumenta la carga.

 

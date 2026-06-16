import asyncio
import random
import sys
import time
import json
from aiocoap import Message, Code, Context

# Uso: python3 simular_sensor.py <IP_DE_LA_RASPBERRY>
IP_FOG = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
URI_COAP = f"coap://{IP_FOG}/co2"

async def enviar_dato(context, valor_co2):
    # Captura el tiempo exacto en milisegundos de origen
    t_origen = int(time.time() * 1000) 
    
    # Estructuramos el payload exigido por la metodología
    payload_dict = {
        "co2": valor_co2,
        "t_origen": t_origen
    }
    payload = json.dumps(payload_dict).encode('utf-8')
    
    request = Message(code=Code.POST, payload=payload, uri=URI_COAP)
    try:
        response = await context.request(request).response
        print(f"[{time.strftime('%H:%M:%S')}] Enviado a {IP_FOG}: {valor_co2} ppm (t_origen={t_origen})")
    except Exception as e:
        print(f"Error de red: {e}")

async def main():
    print(f"Iniciando simulación orientada a la IP Fog: {IP_FOG}")
    print(f"URL CoAP objetivo: {URI_COAP}")
    
    # Creamos un único contexto cliente para reutilizarlo en el envío
    context = await Context.create_client_context()
    
    try:
        while True:
            # Genera valores normales de CO2 simulando aire urbano limpio (p.ej., entre 390 y 440 ppm)
            valor_simulado = random.randint(390, 440)
            
            # Llama a la función de envío pasándole el contexto y el dato
            await enviar_dato(context, valor_simulado)
            
            # Espera 2 segundos antes de la siguiente medición del sensor
            await asyncio.sleep(2)
            
    except KeyboardInterrupt:
        print("\nSimulación finalizada por el usuario.")

if __name__ == "__main__":
    asyncio.run(main())


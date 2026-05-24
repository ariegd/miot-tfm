import asyncio
import random
import sys
import time
from aiocoap import Message, Code, Context

# Uso: python3 simular_sensor.py <IP_DE_LA_RASPBERRY>
IP_FOG = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
URI_COAP = f"coap://{IP_FOG}/co2"

async def enviar_dato(context, valor_co2):
    payload = str(valor_co2).encode('utf-8')
    request = Message(code=Code.POST, payload=payload, uri=URI_COAP)
    try:
        response = await context.request(request).response
        print(f"[{time.strftime('%H:%M:%S')}] Enviado a {IP_FOG}: {valor_co2} ppm")
    except Exception as e:
        print(f"Error de red (¿Está la IP correcta y el Fog encendido?): {e}")

async def main():
    print(f"Iniciando ESP32. Destino Fog: {URI_COAP}")
    protocol = await Context.create_client_context()
    try:
        while True:
            # Rango normal para probar
            await enviar_dato(protocol, random.randint(400, 450))
            await asyncio.sleep(2) 
    except KeyboardInterrupt:
        print("\nDetenido.")

if __name__ == "__main__":
    asyncio.run(main())

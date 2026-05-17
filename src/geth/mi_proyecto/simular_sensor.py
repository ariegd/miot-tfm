import asyncio
import random
import time
from aiocoap import Message, Code, Context

# IP de la máquina donde corre nodo_fog_coap.py (Si es local, 127.0.0.1)
IP_NODO_FOG = "10.114.27.143" #"127.0.0.1" 
URI_COAP = f"coap://{IP_NODO_FOG}/co2"

async def enviar_dato(context, valor_co2):
    # Preparamos el payload (el número en formato bytes)
    payload = str(valor_co2).encode('utf-8')
    
    # Construimos un mensaje tipo POST (equivalente ligero a HTTP POST)
    request = Message(code=Code.POST, payload=payload, uri=URI_COAP)
    
    try:
        # Enviamos y esperamos el acuse de recibo del Fog
        response = await context.request(request).response
        print(f"[{time.strftime('%H:%M:%S')}] ⬆️ Enviado: {valor_co2} ppm | ⬇️ Respuesta Fog: {response.code}")
    except Exception as e:
        print(f"❌ Error al enviar dato: {e}")

async def main():
    print(f"🚀 Iniciando ESP32 Simulado (CoAP) enviando a {URI_COAP}...")
    protocol = await Context.create_client_context()
    
    try:
        while True:
            co2_actual = random.randint(380, 800)
            await enviar_dato(protocol, co2_actual)
            # En un entorno real el ESP32 entraría en Deep Sleep aquí
            await asyncio.sleep(2) 
            
    except KeyboardInterrupt:
        print("\n🛑 Simulación detenida.")

if __name__ == "__main__":
    asyncio.run(main())

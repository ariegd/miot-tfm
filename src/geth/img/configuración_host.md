##  **Solución Definitiva: Hotspot Estático Puro**

Ejecuta estos comandos en tu terminal como root para limpiar el entorno y forzar el encendido de la antena:

## **1\. Eliminar el perfil conflictivo actual**

`nmcli connection delete "Lab_Movil_Hotspot"`

## **2\. Crear la red en modo "Manual" (Sin DHCP automático)**

Cambiando el método a manual, obligamos a NetworkManager a levantar la antena de inmediato sin intentar buscar o reservar rangos dinámicos:

`nmcli connection add type wifi ifname wlxccbabd6179b5 con-name "Lab_Movil_Hotspot" ssid "Lab_Movil" mode ap wifi.cloned-mac-address preserve wifi-sec.key-mgmt wpa-psk wifi-sec.psk "hogz7998" ipv4.addresses 10.42.0.1/24 ipv4.method manual ipv6.method ignore`

## **3\. Levantar la conexión**

`nmcli connection up "Lab_Movil_Hotspot"`

## ---

**Comprobación de éxito**

Una vez que ejecutes el comando up, revisa el estado de tu antena USB con:

`ip a show dev wlxccbabd6179b5`

El estado debe cambiar finalmente a **UP** o **UNKNOWN** (pero ya no dirá DOWN) y verás la línea fija inet 10.42.0.1/24. La red Lab\_Movil ya estará transmitiendo en el aire.


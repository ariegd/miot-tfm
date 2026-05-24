// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract RegistroCO2 {
    
    // Variables de estado (se guardan permanentemente en la blockchain)
    uint256 public nivelCO2;        // Nivel de CO2 en ppm
    uint256 public ultimaLectura;   // Timestamp (fecha y hora en formato Unix)
    address public sensorId;        // La dirección de la cuenta (ESP32) que envió el dato

    // Un "Evento" sirve para guardar un registro histórico barato en la blockchain
    // Es muy útil para que un frontend (web) escuche cuando hay un nuevo dato
    event NuevaLectura(uint256 co2PPM, uint256 timestamp, address sensor);

    // Función principal que llamará el ESP32 para guardar un nuevo dato
    function registrarCO2(uint256 _co2PPM) public {
        nivelCO2 = _co2PPM;
        ultimaLectura = block.timestamp; // La hora exacta de la red en este bloque
        sensorId = msg.sender;           // Quien ejecuta la transacción (el ESP32)

        // Emitimos el evento para el historial
        emit NuevaLectura(_co2PPM, block.timestamp, msg.sender);
    }

    // Función auxiliar para leer el último estado rápidamente
    function obtenerUltimaLectura() public view returns (uint256, uint256, address) {
        return (nivelCO2, ultimaLectura, sensorId);
    }
}

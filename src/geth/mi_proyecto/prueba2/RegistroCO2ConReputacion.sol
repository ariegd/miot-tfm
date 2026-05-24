// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract RegistroCO2ConReputacion {
    
    address public admin;

    // 1. Añadimos la variable "reputacion" (Nuestro Token de mentira)
    struct Entidad {
        string barrio;
        string calle;
        bool estaRegistrada;
        uint256 reputacion; // <-- NUEVO: Contador de tokens/puntos
    }

    struct LecturaPendiente {
        uint256 valorCO2;
        address idSensor;
        uint256 timestamp;
    }

    mapping(address => Entidad) public directorioEntidades;
    mapping(string => LecturaPendiente) private bufferBarrio;
    mapping(string => uint256) public co2OficialBarrio;
    mapping(string => uint256) public ultimaActualizacionBarrio;

    // Nuevo evento para trazar cuándo alguien gana tokens
    event ReputacionGanada(address entidad, uint256 tokensGanados, uint256 reputacionTotal);
    event EntidadRegistrada(address entidad, string barrio, string calle);
    event LecturaEnEspera(string barrio, uint256 co2, address sensor);
    event ConsensoAlcanzado(string barrio, uint256 co2Promediado, uint256 timestamp);

    constructor() {
        admin = msg.sender;
    }

    modifier soloAdmin() {
        require(msg.sender == admin, "Solo el administrador puede registrar entidades.");
        _;
    }

    modifier soloEntidadAutorizada() {
        require(directorioEntidades[msg.sender].estaRegistrada, "Tu SoC no esta registrado en el sistema.");
        _;
    }

    // Al registrar, la entidad empieza con 0 tokens de reputación
    function registrarEntidad(address _cuentaSoC, string memory _barrio, string memory _calle) public soloAdmin {
        directorioEntidades[_cuentaSoC] = Entidad({
            barrio: _barrio,
            calle: _calle,
            estaRegistrada: true,
            reputacion: 0 // Inician desde cero
        });
        emit EntidadRegistrada(_cuentaSoC, _barrio, _calle);
    }

    function reportarCO2(uint256 _co2PPM) public soloEntidadAutorizada {
        string memory barrioActual = directorioEntidades[msg.sender].barrio;
        LecturaPendiente memory pendiente = bufferBarrio[barrioActual];

        // LÓGICA DE CONSENSO
        if (pendiente.idSensor != address(0) && pendiente.idSensor != msg.sender) {
            
            // 1. Puesta en común (Promedio)
            uint256 co2Consensuado = (pendiente.valorCO2 + _co2PPM) / 2;
            co2OficialBarrio[barrioActual] = co2Consensuado;
            ultimaActualizacionBarrio[barrioActual] = block.timestamp;

            // 2. SISTEMA DE RECOMPENSAS (Tokens de Reputación)
            // Se le dan 10 puntos al SoC que dejó el dato en espera (el pionero)
            directorioEntidades[pendiente.idSensor].reputacion += 10;
            // Se le dan 10 puntos al SoC actual que cerró y validó el consenso
            directorioEntidades[msg.sender].reputacion += 10;

            // Emitimos los eventos para la web/historial
            emit ConsensoAlcanzado(barrioActual, co2Consensuado, block.timestamp);
            emit ReputacionGanada(pendiente.idSensor, 10, directorioEntidades[pendiente.idSensor].reputacion);
            emit ReputacionGanada(msg.sender, 10, directorioEntidades[msg.sender].reputacion);

            // 3. Vaciamos el buffer
            delete bufferBarrio[barrioActual];

        } else {
            // Si no hay consenso aún, se queda en espera.
            // OJO: Aquí NO se ganan tokens, para evitar que hagan spam de datos.
            bufferBarrio[barrioActual] = LecturaPendiente({
                valorCO2: _co2PPM,
                idSensor: msg.sender,
                timestamp: block.timestamp
            });

            emit LecturaEnEspera(barrioActual, _co2PPM, msg.sender);
        }
    }

    // --- NUEVAS FUNCIONES DE CONSULTA ---

    // Permite consultar cuántos tokens/respeto tiene un nodo específico
    function consultarReputacion(address _entidad) public view returns (uint256) {
        require(directorioEntidades[_entidad].estaRegistrada, "La entidad no existe.");
        return directorioEntidades[_entidad].reputacion;
    }

    function consultarBarrio(string memory _barrio) public view returns (uint256 nivelCO2, uint256 timestamp) {
        return (co2OficialBarrio[_barrio], ultimaActualizacionBarrio[_barrio]);
    }
}

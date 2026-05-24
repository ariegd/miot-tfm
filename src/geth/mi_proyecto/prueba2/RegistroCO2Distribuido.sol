// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract RegistroCO2Distribuido {
    
    // El administrador es quien despliega el contrato (tú)
    address public admin;

    // 1. Diseño de la Entidad (Identidad Espacial)
    struct Entidad {
        string barrio;
        string calle;
        bool estaRegistrada; // Actúa como lista blanca (Whitelist)
    }

    // Estructura temporal para gestionar el consenso
    struct LecturaPendiente {
        uint256 valorCO2;
        address idSensor;
        uint256 timestamp;
    }

    // 2. Mapeos (Bases de datos internas del contrato)
    mapping(address => Entidad) public directorioEntidades;         // Qué dirección Ethereum pertenece a qué calle/barrio
    mapping(string => LecturaPendiente) private bufferBarrio;       // Guarda la 1ra lectura esperando la 2da para el consenso
    mapping(string => uint256) public co2OficialBarrio;             // El valor final agregado y público del barrio
    mapping(string => uint256) public ultimaActualizacionBarrio;    // Cuándo se logró el último consenso

    // Eventos para trazar todo en la red
    event EntidadRegistrada(address entidad, string barrio, string calle);
    event LecturaEnEspera(string barrio, uint256 co2, address sensor);
    event ConsensoAlcanzado(string barrio, uint256 co2Promediado, uint256 timestamp);

    constructor() {
        admin = msg.sender;
    }

    // Modificador: Solo el admin puede ejecutar ciertas funciones
    modifier soloAdmin() {
        require(msg.sender == admin, "Solo el administrador puede registrar entidades.");
        _;
    }

    // Modificador: Solo los 10 nodos SoC autorizados pueden enviar datos
    modifier soloEntidadAutorizada() {
        require(directorioEntidades[msg.sender].estaRegistrada, "Tu SoC no esta registrado en el sistema.");
        _;
    }

    // --- FUNCIONES ---

    // Función para dar de alta a tus 10 entidades distintas
    function registrarEntidad(address _cuentaSoC, string memory _barrio, string memory _calle) public soloAdmin {
        directorioEntidades[_cuentaSoC] = Entidad(_barrio, _calle, true);
        emit EntidadRegistrada(_cuentaSoC, _barrio, _calle);
    }

    // Función principal de ingesta y consenso
    function reportarCO2(uint256 _co2PPM) public soloEntidadAutorizada {
        // Buscamos de qué barrio es el sensor que está enviando el dato
        string memory barrioActual = directorioEntidades[msg.sender].barrio;
        
        // Revisamos si ya hay un dato esperando validación en ese barrio
        LecturaPendiente memory pendiente = bufferBarrio[barrioActual];

        // LÓGICA DE CONSENSO: 
        // ¿Hay un dato pendiente Y fue enviado por un SoC DISTINTO al actual?
        if (pendiente.idSensor != address(0) && pendiente.idSensor != msg.sender) {
            
            // ¡CONSENSO ALCANZADO! Ponemos en común las dos lecturas (Promedio)
            uint256 co2Consensuado = (pendiente.valorCO2 + _co2PPM) / 2;
            
            // Registramos el valor oficial del barrio
            co2OficialBarrio[barrioActual] = co2Consensuado;
            ultimaActualizacionBarrio[barrioActual] = block.timestamp;

            emit ConsensoAlcanzado(barrioActual, co2Consensuado, block.timestamp);

            // Vaciamos el buffer para que inicie un nuevo ciclo de validación
            delete bufferBarrio[barrioActual];

        } else {
            // Si el buffer estaba vacío, o si el MISMO sensor envió el dato dos veces seguidas,
            // simplemente lo dejamos en espera en el buffer. No hay consenso aún.
            bufferBarrio[barrioActual] = LecturaPendiente({
                valorCO2: _co2PPM,
                idSensor: msg.sender,
                timestamp: block.timestamp
            });

            emit LecturaEnEspera(barrioActual, _co2PPM, msg.sender);
        }
    }

    // Función para que un panel web o sistema consulte el valor oficial de un barrio
    function consultarBarrio(string memory _barrio) public view returns (uint256 nivelCO2, uint256 timestamp) {
        return (co2OficialBarrio[_barrio], ultimaActualizacionBarrio[_barrio]);
    }
}

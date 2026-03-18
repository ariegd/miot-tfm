pragma solidity ^0.8.13;

contract BloqueNotas {
    string public nota;

    function escribir(string memory _nuevaNota) public {
        nota = _nuevaNota;
    }
}


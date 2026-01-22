// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AccessControl {

    mapping(string => string) private fileHashes;
    mapping(string => mapping(address => bool)) private access;

    event RecordStored(string patientId, string fileHash);
    event AccessGranted(string patientId, address hospital);

    function addRecord(string memory patientId, string memory fileHash) public {
        fileHashes[patientId] = fileHash;
        emit RecordStored(patientId, fileHash);
    }

    function grantAccess(string memory patientId, address hospital) public {
        access[patientId][hospital] = true;
        emit AccessGranted(patientId, hospital);
    }

    function checkAccess(string memory patientId, address hospital)
        public view returns (bool)
    {
        return access[patientId][hospital];
    }

    function getFileHash(string memory patientId)
        public view returns (string memory)
    {
        return fileHashes[patientId];
    }
}

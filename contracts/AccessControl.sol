// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AccessControl {

    struct Record {
        string fileHash;
        address owner;
        bool exists;
    }

    mapping(string => Record) public records;
    mapping(string => mapping(address => bool)) public permissions;

    event RecordStored(string patientId, string fileHash);
    event AccessGranted(string patientId, address hospital);

    function addRecord(string memory patientId, string memory fileHash) public {
        records[patientId] = Record(fileHash, msg.sender, true);
        emit RecordStored(patientId, fileHash);
    }

    function grantAccess(string memory patientId, address hospital) public {
        require(records[patientId].owner == msg.sender, "Only owner can grant");
        permissions[patientId][hospital] = true;
        emit AccessGranted(patientId, hospital);
    }

    function checkAccess(string memory patientId, address hospital) public view returns (bool) {
        return permissions[patientId][hospital];
    }

    function getFileHash(string memory patientId) public view returns (string memory) {
        return records[patientId].fileHash;
    }
}

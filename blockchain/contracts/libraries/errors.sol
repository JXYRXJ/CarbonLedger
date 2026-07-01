// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

error Unauthorized(address account, bytes32 role);
error BatchAlreadyExists(string batchId);
error BatchNotFound(string batchId);
error TransferNotFound(string transferId);
error RetirementNotFound(string retirementId);
error InvalidCredits();
error InvalidCompany();
error ContractPaused();

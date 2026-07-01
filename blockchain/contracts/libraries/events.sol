// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

event BatchRegistered(
    string indexed batchId,
    string projectId,
    string registryId,
    uint256 totalCredits,
    uint256 vintageYear,
    address indexed caller,
    uint256 timestamp
);

event OwnershipTransferred(
    string indexed transferId,
    string indexed batchId,
    string fromCompany,
    string toCompany,
    uint256 credits,
    address indexed caller,
    uint256 timestamp
);

event CreditsRetired(
    string indexed retirementId,
    string indexed batchId,
    string companyId,
    uint256 creditsRetired,
    string certificateNumber,
    address indexed caller,
    uint256 timestamp
);

event AuditRecorded(
    string indexed auditId,
    string indexed entityId,
    string entityType,
    string action,
    string performedBy,
    address indexed caller,
    uint256 timestamp
);

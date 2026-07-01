// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

struct BatchRecord {
    string batchId;
    string projectId;
    uint256 totalCredits;
    uint256 vintageYear;
    string registryId;
    uint256 registeredAt;
    bool active;
}

struct TransferRecord {
    string transferId;
    string batchId;
    string fromCompany;
    string toCompany;
    uint256 credits;
    uint256 timestamp;
    string transactionHashReference;
}

struct RetirementRecord {
    string retirementId;
    string batchId;
    string companyId;
    uint256 creditsRetired;
    string certificateNumber;
    uint256 timestamp;
}

struct AuditRecord {
    string auditId;
    string entityId;
    string entityType;
    string action;
    string performedBy;
    uint256 timestamp;
}

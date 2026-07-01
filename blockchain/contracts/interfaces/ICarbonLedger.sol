// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../libraries/structs.sol";

interface ICarbonLedger {
    // State modifying functions
    function registerBatch(
        string calldata batchId,
        string calldata projectId,
        uint256 totalCredits,
        uint256 vintageYear,
        string calldata registryId
    ) external;

    function recordTransfer(
        string calldata transferId,
        string calldata batchId,
        string calldata fromCompany,
        string calldata toCompany,
        uint256 credits,
        string calldata transactionHashReference
    ) external;

    function recordRetirement(
        string calldata retirementId,
        string calldata batchId,
        string calldata companyId,
        uint256 creditsRetired,
        string calldata certificateNumber
    ) external;

    function recordAudit(
        string calldata auditId,
        string calldata entityId,
        string calldata entityType,
        string calldata action,
        string calldata performedBy
    ) external;

    function pause() external;
    
    function unpause() external;

    // View functions
    function getBatch(string calldata batchId) external view returns (BatchRecord memory);
    
    function getTransfer(string calldata transferId) external view returns (TransferRecord memory);
    
    function getRetirement(string calldata retirementId) external view returns (RetirementRecord memory);
    
    function getAudit(string calldata auditId) external view returns (AuditRecord memory);

    function batchExists(string calldata batchId) external view returns (bool);
    
    function transferExists(string calldata transferId) external view returns (bool);
    
    function retirementExists(string calldata retirementId) external view returns (bool);
    
    // Note: The prompt requests auditExists() too:
    function auditExists(string calldata auditId) external view returns (bool);
    
    function verifyBatch(string calldata batchId) external view returns (bool);
    
    function verifyTransfer(string calldata transferId) external view returns (bool);
    
    function verifyRetirement(string calldata retirementId) external view returns (bool);
    
    function verifyAudit(string calldata auditId) external view returns (bool);
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

import "./interfaces/ICarbonLedger.sol";
import "./libraries/structs.sol";
import "./libraries/errors.sol";
import "./libraries/events.sol";

contract CarbonLedger is ICarbonLedger, AccessControl, Pausable, ReentrancyGuard {
    // Role Definitions
    bytes32 public constant REGISTRY_ROLE = keccak256("REGISTRY_ROLE");
    bytes32 public constant MARKETPLACE_ROLE = keccak256("MARKETPLACE_ROLE");
    bytes32 public constant RETIREMENT_ROLE = keccak256("RETIREMENT_ROLE");
    bytes32 public constant AUDITOR_ROLE = keccak256("AUDITOR_ROLE");

    // Storage Mappings
    mapping(string => BatchRecord) private _batches;
    mapping(string => TransferRecord) private _transfers;
    mapping(string => RetirementRecord) private _retirements;
    mapping(string => AuditRecord) private _audits;

    // Track total cumulative retired credits per batch
    mapping(string => uint256) private _batchTotalRetired;

    // Existence tracking helpers
    mapping(string => bool) private _batchExists;
    mapping(string => bool) private _transferExists;
    mapping(string => bool) private _retirementExists;
    mapping(string => bool) private _auditExists;

    // Custom modifiers for cleaner errors
    modifier onlyRoleCustom(bytes32 role) {
        if (!hasRole(role, msg.sender)) {
            revert Unauthorized(msg.sender, role);
        }
        _;
    }

    modifier whenNotPausedCustom() {
        if (paused()) {
            revert ContractPaused();
        }
        _;
    }

    constructor() {
        // Assign deployer as default admin
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    // --- State Modifying Functions ---

    function registerBatch(
        string calldata batchId,
        string calldata projectId,
        uint256 totalCredits,
        uint256 vintageYear,
        string calldata registryId
    ) external override onlyRoleCustom(REGISTRY_ROLE) whenNotPausedCustom nonReentrant {
        if (bytes(batchId).length == 0 || bytes(projectId).length == 0 || bytes(registryId).length == 0) {
            revert InvalidCompany(); // generic invalid check or empty parameter
        }
        if (totalCredits == 0) {
            revert InvalidCredits();
        }
        if (_batchExists[batchId]) {
            revert BatchAlreadyExists(batchId);
        }

        _batches[batchId] = BatchRecord({
            batchId: batchId,
            projectId: projectId,
            totalCredits: totalCredits,
            vintageYear: vintageYear,
            registryId: registryId,
            registeredAt: block.timestamp,
            active: true
        });

        _batchExists[batchId] = true;

        emit BatchRegistered(
            batchId,
            projectId,
            registryId,
            totalCredits,
            vintageYear,
            msg.sender,
            block.timestamp
        );
    }

    function recordTransfer(
        string calldata transferId,
        string calldata batchId,
        string calldata fromCompany,
        string calldata toCompany,
        uint256 credits,
        string calldata transactionHashReference
    ) external override onlyRoleCustom(MARKETPLACE_ROLE) whenNotPausedCustom nonReentrant {
        if (bytes(transferId).length == 0 || bytes(fromCompany).length == 0 || bytes(toCompany).length == 0) {
            revert InvalidCompany();
        }
        if (!_batchExists[batchId]) {
            revert BatchNotFound(batchId);
        }
        if (credits == 0 || credits > _batches[batchId].totalCredits) {
            revert InvalidCredits();
        }
        if (_transferExists[transferId]) {
            revert InvalidCompany(); // duplicate transfer identifier
        }

        _transfers[transferId] = TransferRecord({
            transferId: transferId,
            batchId: batchId,
            fromCompany: fromCompany,
            toCompany: toCompany,
            credits: credits,
            timestamp: block.timestamp,
            transactionHashReference: transactionHashReference
        });

        _transferExists[transferId] = true;

        emit OwnershipTransferred(
            transferId,
            batchId,
            fromCompany,
            toCompany,
            credits,
            msg.sender,
            block.timestamp
        );
    }

    function recordRetirement(
        string calldata retirementId,
        string calldata batchId,
        string calldata companyId,
        uint256 creditsRetired,
        string calldata certificateNumber
    ) external override onlyRoleCustom(RETIREMENT_ROLE) whenNotPausedCustom nonReentrant {
        if (bytes(retirementId).length == 0 || bytes(companyId).length == 0 || bytes(certificateNumber).length == 0) {
            revert InvalidCompany();
        }
        if (!_batchExists[batchId]) {
            revert BatchNotFound(batchId);
        }
        if (creditsRetired == 0) {
            revert InvalidCredits();
        }
        if (_batchTotalRetired[batchId] + creditsRetired > _batches[batchId].totalCredits) {
            revert InvalidCredits();
        }
        if (_retirementExists[retirementId]) {
            revert InvalidCompany(); // duplicate retirement identifier
        }

        _batchTotalRetired[batchId] += creditsRetired;

        _retirements[retirementId] = RetirementRecord({
            retirementId: retirementId,
            batchId: batchId,
            companyId: companyId,
            creditsRetired: creditsRetired,
            certificateNumber: certificateNumber,
            timestamp: block.timestamp
        });

        _retirementExists[retirementId] = true;

        emit CreditsRetired(
            retirementId,
            batchId,
            companyId,
            creditsRetired,
            certificateNumber,
            msg.sender,
            block.timestamp
        );
    }

    function recordAudit(
        string calldata auditId,
        string calldata entityId,
        string calldata entityType,
        string calldata action,
        string calldata performedBy
    ) external override onlyRoleCustom(AUDITOR_ROLE) whenNotPausedCustom nonReentrant {
        if (bytes(auditId).length == 0 || bytes(entityId).length == 0 || bytes(entityType).length == 0) {
            revert InvalidCompany();
        }
        if (_auditExists[auditId]) {
            revert InvalidCompany(); // duplicate audit identifier
        }

        _audits[auditId] = AuditRecord({
            auditId: auditId,
            entityId: entityId,
            entityType: entityType,
            action: action,
            performedBy: performedBy,
            timestamp: block.timestamp
        });

        _auditExists[auditId] = true;

        emit AuditRecorded(
            auditId,
            entityId,
            entityType,
            action,
            performedBy,
            msg.sender,
            block.timestamp
        );
    }

    function pause() external override onlyRoleCustom(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    function unpause() external override onlyRoleCustom(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    // --- View/Verification Functions ---

    function getBatch(string calldata batchId) external view override returns (BatchRecord memory) {
        if (!_batchExists[batchId]) {
            revert BatchNotFound(batchId);
        }
        return _batches[batchId];
    }

    function getTransfer(string calldata transferId) external view override returns (TransferRecord memory) {
        if (!_transferExists[transferId]) {
            revert TransferNotFound(transferId);
        }
        return _transfers[transferId];
    }

    function getRetirement(string calldata retirementId) external view override returns (RetirementRecord memory) {
        if (!_retirementExists[retirementId]) {
            revert RetirementNotFound(retirementId);
        }
        return _retirements[retirementId];
    }

    function getAudit(string calldata auditId) external view override returns (AuditRecord memory) {
        if (!_auditExists[auditId]) {
            revert InvalidCompany(); // or generic failure
        }
        return _audits[auditId];
    }

    function batchExists(string calldata batchId) external view override returns (bool) {
        return _batchExists[batchId];
    }

    function transferExists(string calldata transferId) external view override returns (bool) {
        return _transferExists[transferId];
    }

    function retirementExists(string calldata retirementId) external view override returns (bool) {
        return _retirementExists[retirementId];
    }

    function auditExists(string calldata auditId) external view override returns (bool) {
        return _auditExists[auditId];
    }

    function verifyBatch(string calldata batchId) external view override returns (bool) {
        return _batchExists[batchId] && _batches[batchId].active;
    }

    function verifyTransfer(string calldata transferId) external view override returns (bool) {
        return _transferExists[transferId];
    }

    function verifyRetirement(string calldata retirementId) external view override returns (bool) {
        return _retirementExists[retirementId];
    }

    function verifyAudit(string calldata auditId) external view override returns (bool) {
        return _auditExists[auditId];
    }
    
    // Helper to get total cumulative retired credits for a batch
    function getBatchTotalRetired(string calldata batchId) external view returns (uint256) {
        if (!_batchExists[batchId]) {
            revert BatchNotFound(batchId);
        }
        return _batchTotalRetired[batchId];
    }
}

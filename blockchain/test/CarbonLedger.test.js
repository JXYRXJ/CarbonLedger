const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("CarbonLedger Smart Contract", function () {
  let CarbonLedger;
  let carbonLedger;
  
  let owner;
  let registryAdmin;
  let marketplaceAdmin;
  let retirementAdmin;
  let auditorAdmin;
  let unauthorizedUser;

  let DEFAULT_ADMIN_ROLE;
  let REGISTRY_ROLE;
  let MARKETPLACE_ROLE;
  let RETIREMENT_ROLE;
  let AUDITOR_ROLE;

  beforeEach(async function () {
    // Get accounts
    [owner, registryAdmin, marketplaceAdmin, retirementAdmin, auditorAdmin, unauthorizedUser] = await ethers.getSigners();

    // Deploy contract
    CarbonLedger = await ethers.getContractFactory("CarbonLedger");
    carbonLedger = await CarbonLedger.deploy();
    await carbonLedger.waitForDeployment();

    // Retrieve roles
    DEFAULT_ADMIN_ROLE = await carbonLedger.DEFAULT_ADMIN_ROLE();
    REGISTRY_ROLE = await carbonLedger.REGISTRY_ROLE();
    MARKETPLACE_ROLE = await carbonLedger.MARKETPLACE_ROLE();
    RETIREMENT_ROLE = await carbonLedger.RETIREMENT_ROLE();
    AUDITOR_ROLE = await carbonLedger.AUDITOR_ROLE();

    // Grant roles to respective accounts
    await carbonLedger.grantRole(REGISTRY_ROLE, registryAdmin.address);
    await carbonLedger.grantRole(MARKETPLACE_ROLE, marketplaceAdmin.address);
    await carbonLedger.grantRole(RETIREMENT_ROLE, retirementAdmin.address);
    await carbonLedger.grantRole(AUDITOR_ROLE, auditorAdmin.address);
  });

  describe("1. Deployment & Roles", function () {
    it("Should assign the deployer as DEFAULT_ADMIN_ROLE", async function () {
      expect(await carbonLedger.hasRole(DEFAULT_ADMIN_ROLE, owner.address)).to.be.true;
    });

    it("Should initialize roles with correct states", async function () {
      expect(await carbonLedger.hasRole(REGISTRY_ROLE, registryAdmin.address)).to.be.true;
      expect(await carbonLedger.hasRole(MARKETPLACE_ROLE, marketplaceAdmin.address)).to.be.true;
      expect(await carbonLedger.hasRole(RETIREMENT_ROLE, retirementAdmin.address)).to.be.true;
      expect(await carbonLedger.hasRole(AUDITOR_ROLE, auditorAdmin.address)).to.be.true;
      expect(await carbonLedger.hasRole(REGISTRY_ROLE, unauthorizedUser.address)).to.be.false;
    });

    it("Should allow DEFAULT_ADMIN_ROLE to revoke roles", async function () {
      await carbonLedger.revokeRole(REGISTRY_ROLE, registryAdmin.address);
      expect(await carbonLedger.hasRole(REGISTRY_ROLE, registryAdmin.address)).to.be.false;
    });

    it("Should reject role revokes or grants from unauthorized callers", async function () {
      // AccessControl defaults to reverting with standard OZ access control errors, but let's test that it reverts
      await expect(
        carbonLedger.connect(unauthorizedUser).grantRole(REGISTRY_ROLE, unauthorizedUser.address)
      ).to.be.reverted;
    });
  });

  describe("2. Batch Registration", function () {
    const batchId = "batch-uuid-1111";
    const projectId = "project-uuid-2222";
    const registryId = "registry-uuid-3333";
    const totalCredits = 10000;
    const vintageYear = 2024;

    it("Should register a batch successfully from a REGISTRY_ROLE account", async function () {
      const tx = await carbonLedger.connect(registryAdmin).registerBatch(
        batchId,
        projectId,
        totalCredits,
        vintageYear,
        registryId
      );

      // Verify event emission
      await expect(tx)
        .to.emit(carbonLedger, "BatchRegistered")
        .withArgs(batchId, projectId, registryId, totalCredits, vintageYear, registryAdmin.address, anyTimestamp => true);

      // Verify mapping state
      expect(await carbonLedger.batchExists(batchId)).to.be.true;
      expect(await carbonLedger.verifyBatch(batchId)).to.be.true;

      const record = await carbonLedger.getBatch(batchId);
      expect(record.batchId).to.equal(batchId);
      expect(record.projectId).to.equal(projectId);
      expect(record.totalCredits).to.equal(totalCredits);
      expect(record.vintageYear).to.equal(vintageYear);
      expect(record.registryId).to.equal(registryId);
      expect(record.active).to.be.true;
    });

    it("Should reject batch registration from unauthorized caller", async function () {
      await expect(
        carbonLedger.connect(unauthorizedUser).registerBatch(
          batchId,
          projectId,
          totalCredits,
          vintageYear,
          registryId
        )
      ).to.be.revertedWithCustomError(carbonLedger, "Unauthorized");
    });

    it("Should reject batch registration with zero credits", async function () {
      await expect(
        carbonLedger.connect(registryAdmin).registerBatch(
          batchId,
          projectId,
          0,
          vintageYear,
          registryId
        )
      ).to.be.revertedWithCustomError(carbonLedger, "InvalidCredits");
    });

    it("Should reject batch registration with empty parameters", async function () {
      await expect(
        carbonLedger.connect(registryAdmin).registerBatch(
          "",
          projectId,
          totalCredits,
          vintageYear,
          registryId
        )
      ).to.be.revertedWithCustomError(carbonLedger, "InvalidCompany");
    });

    it("Should reject registering duplicate batches", async function () {
      await carbonLedger.connect(registryAdmin).registerBatch(
        batchId,
        projectId,
        totalCredits,
        vintageYear,
        registryId
      );

      await expect(
        carbonLedger.connect(registryAdmin).registerBatch(
          batchId,
          projectId,
          totalCredits,
          vintageYear,
          registryId
        )
      ).to.be.revertedWithCustomError(carbonLedger, "BatchAlreadyExists").withArgs(batchId);
    });

    it("Should revert on non-existent batch lookup", async function () {
      await expect(
        carbonLedger.getBatch("non-existent")
      ).to.be.revertedWithCustomError(carbonLedger, "BatchNotFound").withArgs("non-existent");
    });
  });

  describe("3. Ownership Transfer Recording", function () {
    const batchId = "batch-uuid-1111";
    const projectId = "project-uuid-2222";
    const registryId = "registry-uuid-3333";
    const totalCredits = 10000;
    const vintageYear = 2024;

    const transferId = "tx-uuid-4444";
    const fromCompany = "company-uuid-seller";
    const toCompany = "company-uuid-buyer";
    const credits = 3000;
    const dbTxRef = "db-postgres-reference";

    beforeEach(async function () {
      await carbonLedger.connect(registryAdmin).registerBatch(
        batchId,
        projectId,
        totalCredits,
        vintageYear,
        registryId
      );
    });

    it("Should record a transfer successfully from a MARKETPLACE_ROLE account", async function () {
      const tx = await carbonLedger.connect(marketplaceAdmin).recordTransfer(
        transferId,
        batchId,
        fromCompany,
        toCompany,
        credits,
        dbTxRef
      );

      await expect(tx)
        .to.emit(carbonLedger, "OwnershipTransferred")
        .withArgs(transferId, batchId, fromCompany, toCompany, credits, marketplaceAdmin.address, anyTimestamp => true);

      expect(await carbonLedger.transferExists(transferId)).to.be.true;
      expect(await carbonLedger.verifyTransfer(transferId)).to.be.true;

      const record = await carbonLedger.getTransfer(transferId);
      expect(record.transferId).to.equal(transferId);
      expect(record.batchId).to.equal(batchId);
      expect(record.fromCompany).to.equal(fromCompany);
      expect(record.toCompany).to.equal(toCompany);
      expect(record.credits).to.equal(credits);
      expect(record.transactionHashReference).to.equal(dbTxRef);
    });

    it("Should reject recording a transfer from unauthorized callers", async function () {
      await expect(
        carbonLedger.connect(unauthorizedUser).recordTransfer(
          transferId,
          batchId,
          fromCompany,
          toCompany,
          credits,
          dbTxRef
        )
      ).to.be.revertedWithCustomError(carbonLedger, "Unauthorized");
    });

    it("Should reject recording a transfer for a non-existent batch", async function () {
      await expect(
        carbonLedger.connect(marketplaceAdmin).recordTransfer(
          transferId,
          "non-existent-batch",
          fromCompany,
          toCompany,
          credits,
          dbTxRef
        )
      ).to.be.revertedWithCustomError(carbonLedger, "BatchNotFound").withArgs("non-existent-batch");
    });

    it("Should reject recording a transfer exceeding total batch credits", async function () {
      await expect(
        carbonLedger.connect(marketplaceAdmin).recordTransfer(
          transferId,
          batchId,
          fromCompany,
          toCompany,
          totalCredits + 1,
          dbTxRef
        )
      ).to.be.revertedWithCustomError(carbonLedger, "InvalidCredits");
    });

    it("Should reject recording a transfer of zero credits", async function () {
      await expect(
        carbonLedger.connect(marketplaceAdmin).recordTransfer(
          transferId,
          batchId,
          fromCompany,
          toCompany,
          0,
          dbTxRef
        )
      ).to.be.revertedWithCustomError(carbonLedger, "InvalidCredits");
    });

    it("Should reject duplicate transfer ID recordings", async function () {
      await carbonLedger.connect(marketplaceAdmin).recordTransfer(
        transferId,
        batchId,
        fromCompany,
        toCompany,
        credits,
        dbTxRef
      );

      await expect(
        carbonLedger.connect(marketplaceAdmin).recordTransfer(
          transferId,
          batchId,
          fromCompany,
          toCompany,
          credits,
          dbTxRef
        )
      ).to.be.revertedWithCustomError(carbonLedger, "InvalidCompany");
    });

    it("Should revert on non-existent transfer lookup", async function () {
      await expect(
        carbonLedger.getTransfer("non-existent")
      ).to.be.revertedWithCustomError(carbonLedger, "TransferNotFound").withArgs("non-existent");
    });
  });

  describe("4. Retirement Recording", function () {
    const batchId = "batch-uuid-1111";
    const projectId = "project-uuid-2222";
    const registryId = "registry-uuid-3333";
    const totalCredits = 10000;
    const vintageYear = 2024;

    const retirementId = "ret-uuid-5555";
    const companyId = "company-uuid-retirer";
    const creditsRetired = 4000;
    const certNum = "CERT-VER-9999";

    beforeEach(async function () {
      await carbonLedger.connect(registryAdmin).registerBatch(
        batchId,
        projectId,
        totalCredits,
        vintageYear,
        registryId
      );
    });

    it("Should record a retirement successfully from a RETIREMENT_ROLE account", async function () {
      const tx = await carbonLedger.connect(retirementAdmin).recordRetirement(
        retirementId,
        batchId,
        companyId,
        creditsRetired,
        certNum
      );

      await expect(tx)
        .to.emit(carbonLedger, "CreditsRetired")
        .withArgs(retirementId, batchId, companyId, creditsRetired, certNum, retirementAdmin.address, anyTimestamp => true);

      expect(await carbonLedger.retirementExists(retirementId)).to.be.true;
      expect(await carbonLedger.verifyRetirement(retirementId)).to.be.true;

      const record = await carbonLedger.getRetirement(retirementId);
      expect(record.retirementId).to.equal(retirementId);
      expect(record.batchId).to.equal(batchId);
      expect(record.companyId).to.equal(companyId);
      expect(record.creditsRetired).to.equal(creditsRetired);
      expect(record.certificateNumber).to.equal(certNum);

      expect(await carbonLedger.getBatchTotalRetired(batchId)).to.equal(creditsRetired);
    });

    it("Should block retirement recording if cumulative retired credits exceeds batch cap", async function () {
      // Retire first 6000
      await carbonLedger.connect(retirementAdmin).recordRetirement(
        retirementId,
        batchId,
        companyId,
        6000,
        certNum
      );

      // Attempt to retire another 5000 (total = 11000 > 10000)
      await expect(
        carbonLedger.connect(retirementAdmin).recordRetirement(
          "ret-uuid-second",
          batchId,
          companyId,
          5000,
          "CERT-VER-NEXT"
        )
      ).to.be.revertedWithCustomError(carbonLedger, "InvalidCredits");
    });

    it("Should reject recording a retirement from unauthorized callers", async function () {
      await expect(
        carbonLedger.connect(unauthorizedUser).recordRetirement(
          retirementId,
          batchId,
          companyId,
          creditsRetired,
          certNum
        )
      ).to.be.revertedWithCustomError(carbonLedger, "Unauthorized");
    });

    it("Should reject duplicate retirement ID recordings", async function () {
      await carbonLedger.connect(retirementAdmin).recordRetirement(
        retirementId,
        batchId,
        companyId,
        creditsRetired,
        certNum
      );

      await expect(
        carbonLedger.connect(retirementAdmin).recordRetirement(
          retirementId,
          batchId,
          companyId,
          creditsRetired,
          certNum
        )
      ).to.be.revertedWithCustomError(carbonLedger, "InvalidCompany");
    });

    it("Should revert on non-existent retirement lookup", async function () {
      await expect(
        carbonLedger.getRetirement("non-existent")
      ).to.be.revertedWithCustomError(carbonLedger, "RetirementNotFound").withArgs("non-existent");
    });
  });

  describe("5. Audit Logs Recording", function () {
    const auditId = "audit-uuid-6666";
    const entityId = "entity-uuid-7777";
    const entityType = "CarbonProject";
    const action = "CREATE";
    const performedBy = "user-uuid-admin";

    it("Should record an audit log successfully from an AUDITOR_ROLE account", async function () {
      const tx = await carbonLedger.connect(auditorAdmin).recordAudit(
        auditId,
        entityId,
        entityType,
        action,
        performedBy
      );

      await expect(tx)
        .to.emit(carbonLedger, "AuditRecorded")
        .withArgs(auditId, entityId, entityType, action, performedBy, auditorAdmin.address, anyTimestamp => true);

      expect(await carbonLedger.auditExists(auditId)).to.be.true;
      expect(await carbonLedger.verifyAudit(auditId)).to.be.true;

      const record = await carbonLedger.getAudit(auditId);
      expect(record.auditId).to.equal(auditId);
      expect(record.entityId).to.equal(entityId);
      expect(record.entityType).to.equal(entityType);
      expect(record.action).to.equal(action);
      expect(record.performedBy).to.equal(performedBy);
    });

    it("Should reject recording audit log from unauthorized callers", async function () {
      await expect(
        carbonLedger.connect(unauthorizedUser).recordAudit(
          auditId,
          entityId,
          entityType,
          action,
          performedBy
        )
      ).to.be.revertedWithCustomError(carbonLedger, "Unauthorized");
    });

    it("Should reject duplicate audit ID recordings", async function () {
      await carbonLedger.connect(auditorAdmin).recordAudit(
        auditId,
        entityId,
        entityType,
        action,
        performedBy
      );

      await expect(
        carbonLedger.connect(auditorAdmin).recordAudit(
          auditId,
          entityId,
          entityType,
          action,
          performedBy
        )
      ).to.be.revertedWithCustomError(carbonLedger, "InvalidCompany");
    });

    it("Should reject recording audit log with empty parameters", async function () {
      await expect(
        carbonLedger.connect(auditorAdmin).recordAudit(
          "",
          entityId,
          entityType,
          action,
          performedBy
        )
      ).to.be.revertedWithCustomError(carbonLedger, "InvalidCompany");
    });

    it("Should revert on non-existent audit lookup", async function () {
      await expect(
        carbonLedger.getAudit("non-existent")
      ).to.be.revertedWithCustomError(carbonLedger, "InvalidCompany");
    });

    it("Should revert on getBatchTotalRetired for non-existent batch", async function () {
      await expect(
        carbonLedger.getBatchTotalRetired("non-existent")
      ).to.be.revertedWithCustomError(carbonLedger, "BatchNotFound").withArgs("non-existent");
    });
  });

  describe("6. Contract Pausing & Security Operations", function () {
    const batchId = "batch-uuid-pause";
    const projectId = "project-uuid-pause";
    const registryId = "registry-uuid-pause";
    const totalCredits = 5000;
    const vintageYear = 2024;

    it("Should allow DEFAULT_ADMIN_ROLE to pause and unpause the contract", async function () {
      // Pause
      await expect(carbonLedger.connect(owner).pause())
        .to.emit(carbonLedger, "Paused")
        .withArgs(owner.address);
      expect(await carbonLedger.paused()).to.be.true;

      // Unpause
      await expect(carbonLedger.connect(owner).unpause())
        .to.emit(carbonLedger, "Unpaused")
        .withArgs(owner.address);
      expect(await carbonLedger.paused()).to.be.false;
    });

    it("Should reject pausing / unpausing calls from unauthorized callers", async function () {
      await expect(
        carbonLedger.connect(unauthorizedUser).pause()
      ).to.be.revertedWithCustomError(carbonLedger, "Unauthorized");
      
      await expect(
        carbonLedger.connect(unauthorizedUser).unpause()
      ).to.be.revertedWithCustomError(carbonLedger, "Unauthorized");
    });

    it("Should restrict state-modifying actions when the contract is paused", async function () {
      // Pause contract
      await carbonLedger.connect(owner).pause();

      // Attempt to register batch
      await expect(
        carbonLedger.connect(registryAdmin).registerBatch(
          batchId,
          projectId,
          totalCredits,
          vintageYear,
          registryId
        )
      ).to.be.revertedWithCustomError(carbonLedger, "ContractPaused");
    });
  });
});

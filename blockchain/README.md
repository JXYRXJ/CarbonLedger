# CarbonLedger Blockchain Verification Layer

This directory contains the **Hardhat** project, smart contracts, unit tests, and deployment configurations for the blockchain verification layer of the **CarbonLedger** platform.

The smart contract acts as an **immutable proof-of-state verification registry**. It stores hashes, UUID keys, totals, and signatures for validation, without storing corporate details or transaction settings.

---

## 🏛️ Smart Contract Architecture

The contract design separates concern definitions into custom library folders:

```text
contracts/
│
├── interfaces/
│   └── ICarbonLedger.sol        # Interface declaration of public functions
│
├── libraries/
│   ├── errors.sol               # Custom error definitions for gas efficiency
│   ├── events.sol               # Core events emitted on state-modifying actions
│   └── structs.sol              # Data models of records logged to storage
│
└── CarbonLedger.sol             # Core implementation contract
```

---

## 🔐 Access Control Matrix

Only authorized backend services holding the appropriate keys may invoke the record logging operations:

| Role Name | Granted To | Allowed Functions |
| :--- | :--- | :--- |
| **DEFAULT_ADMIN_ROLE** | Deployer | `pause()`, `unpause()`, `grantRole()`, `revokeRole()` |
| **REGISTRY_ROLE** | Registry Service | `registerBatch()` |
| **MARKETPLACE_ROLE** | Marketplace Order Service | `recordTransfer()` |
| **RETIREMENT_ROLE** | Retirement Service | `recordRetirement()` |
| **AUDITOR_ROLE** | Logging Service | `recordAudit()` |

---

## 📦 Data Structures & Mappings

### 1. Batch Record (`registerBatch`)
Logs credit vintage details and sets the initial issuance credits cap.
* Validates that the batch does not already exist.
* Requires credits count to be greater than zero.

### 2. Transfer Record (`recordTransfer`)
Logs marketplace asset trades.
* Validates that the credit amount does not exceed the registered batch credits.

### 3. Retirement Record (`recordRetirement`)
Logs credit retired counts.
* Tracks cumulative retired credits on-chain to guarantee the sum of retirements never exceeds the initial batch credits cap.

### 4. Audit Record (`recordAudit`)
Stores tamper-proof log hash hashes of CRUD modifications.

---

## ⚙️ Project Setup & Local Compilation

Ensure you are inside the `blockchain/` folder:

```bash
# Verify virtual files and compile Solidity contracts
npx hardhat compile
```

### Environment Settings (`.env`)
Copy `.env.example` to `.env` and fill in:
* `PRIVATE_KEY`: Private key of the deployer wallet on Polygon Amoy.
* `POLYGON_AMOY_RPC_URL`: Infura or Alchemy JSON-RPC node provider URL.
* `POLYGONSCAN_API_KEY`: Etherscan api-key to verify source code on Amoy.

---

## 🚀 Deployment & Verification

### 1. Deploying to Local Node
Run a local Hardhat node in a separate terminal:
```bash
npx hardhat node
```
Deploy the contract to localhost:
```bash
npx hardhat run scripts/deploy.js --network localhost
```

### 2. Deploying to Polygon Amoy Testnet
Execute the deploy script pointing to the `amoy` network config:
```bash
npx hardhat run scripts/deploy.js --network amoy
```

### 3. Verification on Polygonscan
Export the deployed contract address and execute the verification task:
```bash
# Windows
set CONTRACT_ADDRESS=0x...
npx hardhat run scripts/verify.js --network amoy

# Unix/macOS
CONTRACT_ADDRESS=0x... npx hardhat run scripts/verify.js --network amoy
```

---

## 🧪 Unit Testing & Coverage

The test suite in `test/CarbonLedger.test.js` covers deployment, role management, duplicate prevention checks, cumulative caps calculations, pausing operations, and unauthorized access attempts.

```bash
# Run Mocha tests
npx hardhat test

# Check code coverage
npx hardhat coverage
```

---

## 🛡️ Security Protections

* **ReentrancyGuard**: Applied to all state-changing writes.
* **Pausable**: Admins can freeze logging in case of security compromises.
* **AccessControl**: Explicitly verifies caller role credentials.
* **Custom Errors**: Utilizes gas-optimized custom revert checks (e.g. `error Unauthorized(address account, bytes32 role)`) instead of standard message strings.
* **Validation Bounds**: Validates parameters on all write operations.

const { buildModule } = require("@nomicfoundation/hardhat-ignition/modules");

module.exports = buildModule("CarbonLedgerModule", (m) => {
  const carbonLedger = m.contract("CarbonLedger");

  return { carbonLedger };
});

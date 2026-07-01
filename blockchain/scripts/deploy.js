const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("=========================================");
  console.log("Deploying contracts with account:", deployer.address);
  
  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", hre.ethers.formatEther(balance), "ETH");
  console.log("=========================================");

  const CarbonLedger = await hre.ethers.getContractFactory("CarbonLedger");
  const carbonLedger = await CarbonLedger.deploy();

  await carbonLedger.waitForDeployment();
  const contractAddress = await carbonLedger.getAddress();
  
  // Get receipt to find the exact block number
  const txHash = carbonLedger.deploymentTransaction().hash;
  const receipt = await hre.ethers.provider.getTransactionReceipt(txHash);
  const deploymentBlock = receipt.blockNumber;

  console.log("CarbonLedger deployed successfully!");
  console.log(`Contract Address: ${contractAddress}`);
  console.log(`Network:          ${hre.network.name}`);
  console.log(`Deployment Block: ${deploymentBlock}`);
  console.log(`Transaction Hash: ${txHash}`);
  console.log("=========================================");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

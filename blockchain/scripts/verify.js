const hre = require("hardhat");

async function main() {
  const contractAddress = process.env.CONTRACT_ADDRESS;
  if (!contractAddress) {
    console.error("=========================================");
    console.error("ERROR: CONTRACT_ADDRESS environment variable is required.");
    console.error("Usage: CROSS-ENV CONTRACT_ADDRESS=0x... npx hardhat run scripts/verify.js --network amoy");
    console.error("=========================================");
    process.exit(1);
  }

  console.log("=========================================");
  console.log(`Verifying CarbonLedger contract at: ${contractAddress}`);
  console.log("=========================================");

  try {
    await hre.run("verify:verify", {
      address: contractAddress,
      constructorArguments: []
    });
    console.log("Contract verified successfully!");
  } catch (error) {
    if (error.message.toLowerCase().includes("already verified")) {
      console.log("Contract is already verified!");
    } else {
      console.error("Verification failed:", error);
    }
  }
  console.log("=========================================");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

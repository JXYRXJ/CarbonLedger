require("dotenv").config({ path: require("path").resolve(__dirname, "../.env") });

module.exports = {
  hardhat: {
    chainId: 1337
  },
  localhost: {
    url: "http://127.0.0.1:8545",
    chainId: 1337
  },
  amoy: {
    url: process.env.POLYGON_AMOY_RPC_URL || "https://rpc-amoy.polygon.technology",
    accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
    chainId: 80002
  }
};

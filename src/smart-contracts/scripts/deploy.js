const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contract with account:", deployer.address);

  // Load the contract factory
  const VODSubscription = await hre.ethers.getContractFactory("VODSubscription");
  
  // Deploy the contract
  console.log("Deploying VODSubscription...");
  const contract = await VODSubscription.deploy();

  // Wait for it to finish
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("-----------------------------------------");
  console.log("VOD Smart Contract Deployed!");
  console.log("Address:", address);
  console.log("-----------------------------------------");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
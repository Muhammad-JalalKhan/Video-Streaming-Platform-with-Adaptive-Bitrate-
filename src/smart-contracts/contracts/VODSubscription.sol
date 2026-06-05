// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VODSubscription {
    address public owner;
    uint256 public subscriptionFee = 0.01 ether;
    mapping(address => bool) public isSubscribed;

    constructor() {
        owner = msg.sender;
    }

    function subscribe() public payable {
        require(msg.value == subscriptionFee, "Exact fee required");
        isSubscribed[msg.sender] = true;
    }

    function checkSubscription(address user) public view returns (bool) {
        return isSubscribed[user];
    }
}
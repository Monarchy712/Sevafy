// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Sevafy {

    // ---------------- STRUCTS ----------------

    struct donorPayment {
        uint donationId; 
        uint donorUID;
        uint ngoUID;
        uint amount;
        uint timeStamp;
    }

    struct ngoPayment {
        uint donationId;
        uint ngoUID;
        uint studentUID;
        uint amount;
        uint timeStamp;
        uint purpose;
    }

    struct stdPayment {
        uint purpose; //100 for purpose means its NULL, purpose only exist for NGO-> student, not for donor -> NGO
        uint donationId;
        uint senderUID;
        uint receiverUID;
        uint amount;
        uint timeStamp;
    }

    

    // ---------------- STATE ----------------

    address public owner;
    uint public donationCounter;

    mapping(uint => uint) public remainingFunds;

    donorPayment[] public donorPaymentData;
    ngoPayment[] public ngoPaymentData;

    // ---------------- MODIFIER ----------------

    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    // ---------------- EVENTS ----------------

    event donorPaymentEvent(uint donationId, uint donorUID, uint ngoUID, uint amount);
    event ngoPaymentEvent(uint donationId, uint ngoUID, uint studentUID, uint amount);
    event fApprovalEvent(uint donationId, uint ngoUID, uint studentUID, uint amount);

    event VerificationRecorded(
        uint studentUID,
        string verificationType,
        bool status,
        uint timestamp
    );

    // ---------------- FUNCTIONS ----------------

    // Record Donation
    function donorPaymentCall(uint _donorUID, uint _ngoUID, uint _amount) public onlyOwner {
        donationCounter++;

        donorPaymentData.push(donorPayment(
            donationCounter,
            _donorUID,
            _ngoUID,
            _amount,
            block.timestamp
        ));

        remainingFunds[donationCounter] = _amount;

        emit donorPaymentEvent(donationCounter, _donorUID, _ngoUID, _amount);
    }

    // Record NGO -> Student Payment (with linkage)
    function ngoPaymentCall(
        uint _donationId,
        uint _ngoUID,
        uint _studentUID,
        uint _amount,
        uint _purpose
    ) public onlyOwner {
        require(_donationId > 0 && _donationId <= donationCounter, "Invalid donationId");
        require(remainingFunds[_donationId] >= _amount, "Insufficient funds");

        remainingFunds[_donationId] -= _amount;

        ngoPaymentData.push(ngoPayment(
            _donationId,
            _ngoUID,
            _studentUID,
            _amount,
            block.timestamp,
            _purpose
        ));

        emit ngoPaymentEvent(_donationId, _ngoUID, _studentUID, _amount);
    }

    // Approval + Transfer
    function fundTransfer(
        uint _donationId,
        uint _ngoUID,
        uint _studentUID,
        uint _amount,
        uint _purpose
    ) public onlyOwner {
        require(_donationId > 0 && _donationId <= donationCounter, "Invalid donationId");
        emit fApprovalEvent(_donationId, _ngoUID, _studentUID, _amount);

        ngoPaymentCall(
            _donationId,
            _ngoUID,
            _studentUID,
            _amount,
            _purpose
        );
    }

    // ---------------- VIEW FUNCTIONS ----------------

    function getDonorPaymentData() public view returns (donorPayment[] memory) {
        return donorPaymentData;
    }

    function getNgoPaymentData() public view returns (ngoPayment[] memory) {
        return ngoPaymentData;
    }

    function getUIDPaymentData(
        uint _uid,
        string memory _clientType,
        string memory _operation
    ) public view returns (stdPayment[] memory) {

        uint max;
        uint resultCount = 0;

        bytes32 clientHash = keccak256(bytes(_clientType));
        bytes32 opHash = keccak256(bytes(_operation));

        stdPayment[] memory temp;

        if (
            (opHash == keccak256("D") && clientHash == keccak256("NGO")) ||
            (clientHash == keccak256("STUDENT"))
        ) {
            max = ngoPaymentData.length;
            temp = new stdPayment[](max);

            for (uint i = 0; i < max; i++) {

                if (
                    clientHash == keccak256("NGO") &&
                    ngoPaymentData[i].ngoUID == _uid
                ) {
                    temp[resultCount++] = stdPayment(
                        ngoPaymentData[i].purpose,
                        ngoPaymentData[i].donationId,
                        ngoPaymentData[i].ngoUID,
                        ngoPaymentData[i].studentUID,
                        ngoPaymentData[i].amount,
                        ngoPaymentData[i].timeStamp
                    );
                }

                else if (
                    clientHash == keccak256("STUDENT") &&
                    ngoPaymentData[i].studentUID == _uid
                ) {
                    temp[resultCount++] = stdPayment(
                        ngoPaymentData[i].purpose,
                        ngoPaymentData[i].donationId,
                        ngoPaymentData[i].ngoUID,
                        ngoPaymentData[i].studentUID,
                        ngoPaymentData[i].amount,
                        ngoPaymentData[i].timeStamp
                    );
                }
            }
        }

        else if (
            (opHash == keccak256("R") && clientHash == keccak256("NGO")) ||
            (clientHash == keccak256("DONOR"))
        ) {
            max = donorPaymentData.length;
            temp = new stdPayment[](max);

            for (uint i = 0; i < max; i++) {

                if (
                    clientHash == keccak256("NGO") &&
                    donorPaymentData[i].ngoUID == _uid
                ) {
                    temp[resultCount++] = stdPayment(
                        100, // purpose is NULL for donor -> NGO payments
                        donorPaymentData[i].donationId,
                        donorPaymentData[i].donorUID,
                        donorPaymentData[i].ngoUID,
                        donorPaymentData[i].amount,
                        donorPaymentData[i].timeStamp
                    );
                }

                else if (
                    clientHash == keccak256("DONOR") &&
                    donorPaymentData[i].donorUID == _uid
                ) {
                    temp[resultCount++] = stdPayment(
                        100, // purpose is NULL for donor -> NGO payments
                        donorPaymentData[i].donationId,
                        donorPaymentData[i].donorUID,
                        donorPaymentData[i].ngoUID,
                        donorPaymentData[i].amount,
                        donorPaymentData[i].timeStamp
                    );
                }
            }
        }

        else {
            revert("Invalid client type or operation");
        }

        stdPayment[] memory result = new stdPayment[](resultCount);

        for (uint i = 0; i < resultCount; i++) {
            result[i] = temp[i];
        }

        return result;
    }

    function getStudentsFundedByDonation(uint _donationId)
    public
    view
    returns (stdPayment[] memory)
    {
        uint max = ngoPaymentData.length;
        stdPayment[] memory temp = new stdPayment[](max);
        uint count = 0;

        for (uint i = 0; i < max; i++) {
            if (ngoPaymentData[i].donationId == _donationId) {
                temp[count++] = stdPayment(
                    ngoPaymentData[i].purpose,
                    ngoPaymentData[i].donationId,
                    ngoPaymentData[i].ngoUID,
                    ngoPaymentData[i].studentUID,
                    ngoPaymentData[i].amount,
                    ngoPaymentData[i].timeStamp
                );
            }
        }

        stdPayment[] memory result = new stdPayment[](count);
        for (uint i = 0; i < count; i++) {
            result[i] = temp[i];
        }

        return result;
    }

    function isDonationFullyUsed(uint _donationId) public view returns (bool) {
        return remainingFunds[_donationId] == 0;
    }

    // Last 50 transactions (merged)
    function last50Transactions() public view onlyOwner returns (stdPayment[] memory) {
        uint donorLen = donorPaymentData.length;
        uint ngoLen = ngoPaymentData.length;

        uint i = donorLen;
        uint j = ngoLen;

        uint count = 0;
        uint max = 50;

        if (donorLen + ngoLen < 50) {
            max = donorLen + ngoLen;
        }

        stdPayment[] memory last50Payments = new stdPayment[](max);

        while (count < max) {

            if (i == 0) {
                j--;
                last50Payments[count] = stdPayment(
                    ngoPaymentData[j].purpose,
                    ngoPaymentData[j].donationId,
                    ngoPaymentData[j].ngoUID,
                    ngoPaymentData[j].studentUID,
                    ngoPaymentData[j].amount,
                    ngoPaymentData[j].timeStamp
                );
            }

            else if (j == 0) {
                i--;
                last50Payments[count] = stdPayment(
                    100, // purpose is NULL for donor -> NGO payments
                    donorPaymentData[i].donationId,
                    donorPaymentData[i].donorUID,
                    donorPaymentData[i].ngoUID,
                    donorPaymentData[i].amount,
                    donorPaymentData[i].timeStamp
                );
            }

            else if (donorPaymentData[i - 1].timeStamp > ngoPaymentData[j - 1].timeStamp) {
                i--;
                last50Payments[count] = stdPayment(
                    100, // purpose is NULL for donor -> NGO payments
                    donorPaymentData[i].donationId,
                    donorPaymentData[i].donorUID,
                    donorPaymentData[i].ngoUID,
                    donorPaymentData[i].amount,
                    donorPaymentData[i].timeStamp
                );
            } 
            
            else {
                j--;
                last50Payments[count] = stdPayment(
                    ngoPaymentData[j].purpose,
                    ngoPaymentData[j].donationId,
                    ngoPaymentData[j].ngoUID,
                    ngoPaymentData[j].studentUID,
                    ngoPaymentData[j].amount,
                    ngoPaymentData[j].timeStamp
                );
            }

            count++;
        }

        return last50Payments;
    }

    // Verification Logging
    function recordVerification(
        uint _studentUID,
        string memory _type,
        bool _status
    ) public onlyOwner {
        emit VerificationRecorded(_studentUID, _type, _status, block.timestamp);
    }
}
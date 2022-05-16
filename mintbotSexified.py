from cmath import inf
import enum
from web3 import Web3
import json
import time


class MintBot:
    def __init__(self) -> None:
        self.CHAIN_ID = 4
        self.GAS_AMOUNT=300000
        self.CONTRACT_ADDRESS="0x94b219956788598f6BDD11894480AAEa5a6870A6" # change to input for final version
        self.ABI=json.loads(open("./contractAbi.json").read()) # allow user to enter an abi
        self.w3 = Web3(Web3.HTTPProvider("https://rinkeby.infura.io/v3/59ef45cbe2674f43a7672339c2e76a0f")) # initialise eth node
        self.gweiC = self.w3.eth.gas_price / 1e9 # current gas 
        self.contract = self.w3.eth.contract(address=self.CONTRACT_ADDRESS, abi=self.ABI) # initialise contract instance
        ### inputs
        self.amount_wanted = int(input("Enter amount you want in total: "))
        self.amount_per_wallet = int(input("Enter amount you can have per wallet: "))
        self.gwei = int(input(f"Enter gwei to use (current network suggests {self.gweiC} enter 0 to use {self.gweiC * 1.2} (current gwei *1.2)): "))
        self.price = float(input("Enter cost of 1 nft: "))
        self.live_time = int(input("Enter time it starts (unix time): "))
        self.num_mint = float("inf") # infinite initialise
        self.private_keys = [i for i in open("fundedwalls.txt").read().split("\n") if len(i) > 30] # load priv keys from file ignoring blank lines

    def getWalletEth(self, pub: str) -> float:
        """Gets a wallets bal in eth
        @param pub: The wallet to check public key
        """
        return self.w3.eth.getBalance(pub)/1e18
    
    def getMaxMints(self, pub: str) -> int:
        """Get max amount a user can mint
        @param pub: The wallet to check public key
        """
        bal = self.getWalletEth(pub)
        if self.price == 0:
            return self.amount_per_wallet
        else:
            return int(bal//self.price)
    
    def mint(self) -> None:
        """Main mint function
        """
        amount_mint = self.amount_wanted # idk why i assigned to var
        print("\n\n") # formatting
        if time.time() < self.live_time: # check if time of mint is same as now
            tts = self.live_time - int(time.time()) # time to wait til mint
            for ticker in range(tts, 0, -1):
                print(f"Minting will begin in {ticker} seconds", end="\r") # print out wait time
                time.sleep(1) # wait
        for i in self.private_keys: # loop thru possible wallets
            
            pub = self.w3.eth.account.privateKeyToAccount(i).address # gets the priv key pub key
            maxUser = self.getMaxMints(pub) 
            if amount_mint <= self.amount_wanted: # if we have minted more than we wanted already
                
                num_mint = amount_mint
                if maxUser < num_mint:
                    print(f"We can only mint {maxUser} from {pub}...")
                    num_mint = maxUser
                    amount_mint -= maxUser
                else:
                    print(f"We are minting {num_mint} from {pub}")
                    amount_mint = 0
            else:
                num_mint = self.amount_per_wallet
                if maxUser < num_mint:
                    print(f"We can only mint {maxUser} from {pub}...")
                    num_mint = maxUser
                    amount_mint -= maxUser
                else:
                    print(f"We are minting {num_mint} from {pub}")

                    amount_mint -= self.amount_per_wallet
            if int(num_mint) != 0:    
                priv = i

                nonce = self.w3.eth.getTransactionCount(pub) # tx nonce num
                cost = 0 # initalise cost 
                if self.price==0: # bugs out without this
                    cost = 0
                else:
                    cost = Web3.toWei(self.price, "ether") # convert eth to wei
                tx = self.contract.functions.mint(num_mint).buildTransaction({
                        'chainId': self.CHAIN_ID, # 1 = main 4 = dev
                        'gas': self.GAS_AMOUNT, # defaults to 300000, should only need half max
                        'gasPrice': Web3.toWei(self.gwei, 'gwei'), # gas to send with
                        'from': pub,
                        'nonce': nonce,
                        "value":cost # cost of mint
                })
                signed_txn = self.w3.eth.account.signTransaction(tx, private_key=i)
                tx_hash = self.w3.toHex(self.w3.keccak(signed_txn.rawTransaction)) # pre determine txn (wowsers)
                self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
                print(f"Sent tx to mint {num_mint} from {pub}\nTxn: {tx_hash}")
            else:
                print(f"Not enough bal to mint from {pub}...") # no moneys :(
class FundSplitter:
    def __init__(self) -> None:
        self.w3 = Web3(Web3.HTTPProvider("https://rinkeby.infura.io/v3/59ef45cbe2674f43a7672339c2e76a0f"))
        todo = int(input("Funds Menu\nCheck balances of private keys you have supplied (1)\nSplit from supplied private key to generated wallets (2)\nTo check for NFTs in privkeys enter (3)\nChoice: "))
        if todo == 1:
            self.checkPrivateKeyBals()
        elif todo == 2:
            self.setup_splitter()
            self.split()
        elif todo ==3:
            self.checkForNFT()
        else:
            print("Invalid option supplied")
            quit()
    
    def setup_splitter(self):
        self.parentkey = input("Enter your private key to send funds from: ")
        self.amnt_send = float(input("Enter amount you would like to send: "))
        self.gwei = int(input("Enter gwei to send with: "))
        self.pub = self.w3.eth.account.privateKeyToAccount(self.parentkey).address
        self.split()

    def generate_wallets(self) -> list:
        """Generate priv keys to split to
        """
        keys = []
        for i in range(self.amnt_split):
            acc = self.w3.eth.account.create()
            keys.append(acc)
        #print(self.w3.toHex(acc.privateKey), acc.address)
        return keys

    def entered_to_obj(self, keylist: list) -> list:
        """Takes priv keys and makes private key objects out of them
        """
        keys = []
        for i in keylist:
            acc = self.w3.eth.account.privateKeyToAccount(i)
            keys.append(acc)
        return keys

    def split(self) -> bool:
        """Main split function
        """
        _type = int(input("To generate x random wallets to split to enter (1)\nTo supply wallets enter (2)\nChoice: "))
        if _type == 1:
            self.amnt_split = int(input("Enter amount of wallets you want to split to: "))
            keys_split = self.generate_wallets()
        elif _type == 2:
            keys_split_entered = input("Enter privatekeys to send to (space seperated): ").split(" ")
            keys_split = self.entered_to_obj(keys_split_entered) # Convert priv key list to object
            self.amnt_split = len(keys_split) # How many to split between
        
        if self.checkHasBal():
            pass # If they have enough for this we do nothing
        else:
            quit()
        
        print("We will be splitting to these addresses: (address:privatekey)")
        [print(f"{i.address}:{self.w3.toHex(i.privateKey)}") for i in keys_split]
        vals = [i.lower() for i in open("fundedwalls.txt", "r").read().split("\n")]
        towrite = []
        for v in keys_split:
            # Check for dupes in txt file
            priv = str(self.w3.toHex(v.privateKey)).lower()
            if priv in vals or priv[2:] in vals:
                pass
            else:
                towrite.append(self.w3.toHex(v.privateKey))
        #towrite = [self.w3.toHex(v.privateKey) for v in keys_split if v not in vals ]
        with open("fundedwalls.txt", "a") as f:
            f.write("\n" + "\n".join(towrite)) # write new keys

        for i, v in enumerate(keys_split):
            nonce = self.w3.eth.getTransactionCount(self.pub)
            to_addy = v.address
            tx = {
                'nonce': nonce+i , # so we dont send with same nonce we add index to nonce
                'to': to_addy ,
                'value': self.w3.toWei(self.amnt_send, 'ether'),
                'gas': 21000,
                'gasPrice': self.w3.toWei(f'{self.gwei}', 'gwei'),
                "chainId": 4# change to mainnet in prod
            }
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.parentkey)
            tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
            print(f"Sent {self.amnt_send} to {to_addy}\nTxn: {self.w3.toHex(tx_hash)}") # tell user
        quit()

    def checkHasBal(self) -> bool:
        total_cost = (((self.gwei * 1e9 * 21000) / 1e18) * self.amnt_send) + self.amnt_send * self.amnt_split # total eth cost 21000 gas is constant for sending eth
        
        pub = self.w3.eth.account.privateKeyToAccount(self.parentkey).address
        bal = self.w3.eth.getBalance(pub)/1e18

        if bal < total_cost:
            print(f"Your balance is: {bal}eth, this split would cost: {total_cost}eth, we cannot do this") # user feedback
            return False
        return True
    
    def checkPrivateKeyBals(self):
        privs = open("fundedwalls.txt", "r").read().split("\n")
        for i in privs:
            if len(i) < 32:
                pass
            else: 
                pub = self.w3.eth.account.privateKeyToAccount(i).address
                bal = self.w3.eth.getBalance(pub)/1e18 # gives bal in wei so divide by 1*10**18 (1e18 shorthand)
                print(f"{i} has a balance of {bal}eth")
    def checkForNFT(self):
        contract_address = input("Enter contract address to check for nft : ")
        contract = self.w3.eth.contract(address=contract_address, abi=json.loads(open("erc721.json").read())) # initialise contract instance
        private_keys = [i for i in open("fundedwalls.txt").read().split("\n") if len(i) > 30] # load priv keys from file ignoring blank lines
        for i in private_keys:
            acc = self.w3.eth.account.privateKeyToAccount(i)
            bal = contract.functions.balanceOf(acc.address).call()
            if (bal > 0):
                print(f"{acc.address} owns {bal} of this nft")
            else:
                print(f"{acc.address} none found in this wallet")

class Parent:
    def __init__(self) -> None:
        todo = int(input("To start mintbot enter 1\nTo access wallets menu enter 2\nChoice: "))
        if todo == 1:
            mintbot = MintBot()
            mintbot.mint()
        elif todo==2:
            splitter = FundSplitter()
        else:
            print("Invalid option supplied")
            quit()

Parent()
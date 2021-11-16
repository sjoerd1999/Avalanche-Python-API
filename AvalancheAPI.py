# -------------------------------- LIBRARIES -------------------------------- #
from web3 import Web3
import AvalancheConfig as config
import time

# ------------------------------- MAIN CLASS -------------------------------- #
class AvalancheAPI(object):
# ------------------------------- INITIALIZE -------------------------------- #
    def __init__(self):
        self.web3 = Web3(Web3.HTTPProvider(config.RPC_URL))
        self.spend = self.web3.toChecksumAddress(config.WAVAX_ADDRESS)
        self.start_balance = self.getBalance()
        self.contract = self.web3.eth.contract(address=self.web3.toChecksumAddress(config.PANGOLIN_ROUTER_CONTRACT_ADDRESS), abi=config.AVA_ABI)
        print('Starting Balance (AVAX): ', self.start_balance)

# ---------------------------------- UTILS ---------------------------------- #
    def getBalance(self):  # Get AVAX balance
        return self.web3.fromWei(self.web3.eth.get_balance(config.SENDER_ADDRESS), 'ether')

    def getNonce(self):  # Get address nonce
        return self.web3.eth.get_transaction_count(config.SENDER_ADDRESS)

    def get_token_info(self, token_address): # Get symbol and decimal count from contract address
        contract_id = self.web3.toChecksumAddress(token_address)
        sell_token_contract = self.web3.eth.contract(contract_id, abi=config.SELL_ABI)
        symbol = sell_token_contract.functions.symbol().call()
        decimals = sell_token_contract.functions.decimals().call()
        return symbol, decimals

    def get_token_holdings(self, token_address): # Get amount of tokens hold and value(in AVAX) of these tokens
        contract_id = self.web3.toChecksumAddress(token_address)
        sell_token_contract = self.web3.eth.contract(contract_id, abi=config.SELL_ABI)

        balance = sell_token_contract.functions.balanceOf(config.SENDER_ADDRESS).call()  # How many tokens do we have?
        value = self.contract.functions.getAmountsOut(balance,
                                                      [self.web3.toChecksumAddress(token_address),
                                                       self.web3.toChecksumAddress(config.WAVAX_ADDRESS)]).call()
        return balance, value[1]

# ----------------------------------- BUY ----------------------------------- #
    def buy(self, token_address, token_to_spend):
        token_to_buy = self.web3.toChecksumAddress(token_address)
        txn = self.contract.functions.swapExactAVAXForTokensSupportingFeeOnTransferTokens(
            1,  # MinAmountOut, risk of getting frontrun by setting to 1, but saves us from having to calculate it
            [self.spend, token_to_buy],  # Path, which token to spend, which to get
            config.SENDER_ADDRESS,  # Our own (metamask) wallet address
            (int(time.time()) + 10000)  # Deadline
        ).buildTransaction({
            'from': config.SENDER_ADDRESS,
            'value': self.web3.toWei(token_to_spend, 'ether'),
            'gas': 200000,
            'gasPrice': self.web3.toWei('100', 'gwei'),  # minimum is 85 gwei
            'nonce': self.web3.eth.get_transaction_count(config.SENDER_ADDRESS),
        })
        signed_txn = self.web3.eth.account.sign_transaction(txn, private_key=config.PRIVATE_KEY)
        tx_token = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx = self.web3.toHex(tx_token)
        return tx

# --------------------------------- APPROVE --------------------------------- #
    def approve(self, token_address):
        contract_id = self.web3.toChecksumAddress(token_address)
        sellTokenContract = self.web3.eth.contract(contract_id, abi=config.SELL_ABI)
        approve = sellTokenContract.functions.approve(self.web3.toChecksumAddress(config.PANGOLIN_ROUTER_CONTRACT_ADDRESS), 2 ** 256 - 1).buildTransaction({
            'from': self.web3.toChecksumAddress(config.SENDER_ADDRESS),
            'nonce': self.web3.eth.get_transaction_count(config.SENDER_ADDRESS),
        })
        signed_txn = self.web3.eth.account.sign_transaction(approve, private_key=config.PRIVATE_KEY)
        tx_token = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx = self.web3.toHex(tx_token)
        return tx

# ----------------------------------- SELL ---------------------------------- #
    def sell(self, token_address, sell_prcnt=100):
        balance, value = self.get_token_holdings(token_address)
        sell_amt = int(balance * sell_prcnt/100)

        # return
        txn = self.contract.functions.swapExactTokensForAVAXSupportingFeeOnTransferTokens(
            sell_amt,
            1,  # Front-running risk, potential to lose all your money, keep that in mind
            [self.web3.toChecksumAddress(token_address), self.spend],
            config.SENDER_ADDRESS,
            int(time.time()) + 10000
        ).buildTransaction({
            'from': config.SENDER_ADDRESS,
            'gas': 200000,
            'maxFeePerGas': self.web3.toWei('150', 'gwei'),
            'maxPriorityFeePerGas': self.web3.toWei('15', 'gwei'),
            'nonce': self.web3.eth.get_transaction_count(config.SENDER_ADDRESS),
        })
        print(f'Estimated gas for transaction is {self.web3.eth.estimate_gas(txn)}.')
        signed_txn = self.web3.eth.account.sign_transaction(txn, private_key=config.PRIVATE_KEY)
        tx_token = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx = self.web3.toHex(tx_token)
        return tx

# ---------------------------- WAIT FOR RECEIPT ----------------------------- #
    def awaitReceipt(self, tx):
        try:
            return self.web3.eth.wait_for_transaction_receipt(tx, timeout=30)
        except Exception as ex:
            print('Failed to wait for receipt: ', ex)
            return None

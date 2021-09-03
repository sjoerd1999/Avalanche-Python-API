# Avalanche-Python-API
Avalanche C-Chain buy/sell bot in Python using web3


# Example code:

```
from AvalancheAPI import AvalancheAPI

avapi = AvalancheAPI()

address = '0x60781C2586D68229fde47564546784ab3fACA982' # PNG token address
AVAX_TO_SPEND = 0.02 # How many AVAX to spend on buying the token

# Buy the token
buy_tx = avapi.buy(address, AVAX_TO_SPEND)
print(buy_tx)
buy_receipt = avapi.awaitReceipt(buy_tx) # Wait for transaction to finish
print(buy_receipt)

if buy_receipt.status == 1: # Check if the transaction went through
    print('bought successfully!')
else:
    print('buy failed,  exiting...')
    exit()

# Approve the token, must be done once before selling
approve_tx = avapi.approve(address)
print(approve_tx)
approve_receipt = avapi.awaitReceipt(approve_tx)
print(approve_receipt)

# Get info about the token, and get current token value. 
# Useful if we want to sell when we for example hit 2x the value we bought at
balance, value = avapi.get_token_holdings(address)
symbol, decimals = avapi.get_token_info(address)
print(f'We have {balance/(10**decimals)} {symbol}, worth {value/(10**18)} AVAX')

# Sell the token, we can set a percentage to sell
sell_tx = avapi.sell(address, sell_prcnt=50) # Here we sell half of our tokens (50%)
print(sell_tx)
sell_receipt = avapi.awaitReceipt(sell_tx)
print(sell_receipt)
```

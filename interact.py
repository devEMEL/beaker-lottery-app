
from lottery import Players, Lottery

from beaker import sandbox, client
from beaker.client import ApplicationClient
from beaker.client.api_providers import AlgoNode, Network
from algosdk.atomic_transaction_composer import AccountTransactionSigner, TransactionWithSigner
from algosdk.abi import ABIType
from algosdk.transaction import PaymentTxn
from algosdk.encoding import decode_address, encode_address

player_codec = ABIType.from_string(str(Players().type_spec()))

client = sandbox.get_algod_client()
accts = sandbox.get_accounts()
creator_acct = accts[0]
acct1 = accts[1]
acct2 = accts[2]

def print_boxes(app_client):
  boxes = app_client.get_box_names()
  print(f"{len(boxes)} boxes found")
  for box_name in boxes:
    contents = app_client.get_box_contents(box_name)
    if box_name == b"winners":
      print(contents)
    else:
      player = player_codec.decode(contents)
      print(f"\t{encode_address(box_name)} => {player} ")

def demo():
  # APP CLIENTS
  app_client = ApplicationClient(client=client, app=Lottery(), signer=creator_acct.signer)
  

  # CREATE APP
  app_id, app_addr, tx_id = app_client.create()
  print(f"App created with id: {app_id}\nWith app address: {app_addr}\nWith app id: {tx_id}")


  # FUND APP ADDRESS
  app_client.fund(Lottery._min_balance)
  # app_client.fund(10000, creator_acct.address)

  app_client.call(
    method=Lottery.create_start_lottery, 
    boxes=[[app_client.app_id, "winners"]] * 8
  )
  app_client.call(method=Lottery.setup)

#########################################################

  app_client_1 = app_client.prepare(signer=acct1.signer)
  app_client_1.call(
    method=Lottery.register,
    boxes=[(app_client.app_id, decode_address(acct1.address))] * 8
  )

  app_client_2 = app_client.prepare(signer=acct2.signer)
  app_client_2.call(
    method=Lottery.register,
    boxes=[(app_client.app_id, decode_address(acct2.address))] * 8
  )
  print_boxes(app_client)

  sp = app_client.get_suggested_params()
  sp.flat_fee = True
  sp.fee = 3000
  ptxn1 = PaymentTxn(acct1.address, sp, app_client.app_addr, 100)
  ptxn2 = PaymentTxn(acct2.address, sp, app_client.app_addr, 100)

  app_client_1.call(
    method=Lottery.play,
    payment=TransactionWithSigner(ptxn1, acct1.signer),
    boxes=[(app_client.app_id, decode_address(acct1.address))] * 8
  )

  app_client_2.call(
    method=Lottery.play,
    payment=TransactionWithSigner(ptxn2, acct2.signer),
    boxes=[(app_client.app_id, decode_address(acct2.address))] * 8
  )
  print_boxes(app_client)



demo()
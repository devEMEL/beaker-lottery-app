
#from beaker import (
#     Application, ApplicationStateValue, internal, external, Authorize,
# )
# from pyteal import (
#     Assert, Int, Seq, TealType, Txn, Pop, Not, Global,
# )
from beaker import *
from pyteal import *
from typing import Literal
from pyteal.ast import abi
from beaker.lib.storage import Mapping, List


class Players(abi.NamedTuple):
    player_id: abi.Field[abi.Uint64]
    amount_deposited: abi.Field[abi.Uint64]
    has_played: abi.Field[abi.Uint64]


class Lottery(Application):
    lotteryPlayers = Mapping(abi.Address, Players)

    winners = List(abi.StaticBytes[Literal[64]], 10)
    winnersId =  ApplicationStateValue(stack_type=TealType.uint64, default=Int(0))
    totalDepositedAmount = ApplicationStateValue(stack_type=TealType.uint64, default=Int(0))
    lotteryPlayId = ApplicationStateValue(stack_type=TealType.uint64, default=Int(0))
    start_lottery = ApplicationStateValue(stack_type=TealType.uint64, default=Int(0))

    BoxFlatMinBalance = 2500
    BoxByteMinBalance = 400
    AssetMinBalance = 100000

       # Math for determining min balance based on expected size of boxes
    _max_members = 10
    _player_box_size = abi.size_of(Players)
    _min_balance = (
        AssetMinBalance  # Not necessary though since we are not creating a token
        + (BoxFlatMinBalance + (_player_box_size * BoxByteMinBalance))
        * _max_members  # cover min bal for player boxes we might create
        + (
            BoxFlatMinBalance + (winners._box_size * BoxByteMinBalance)
        )  # cover min bal for winners box
    )
    ####

    @external(authorize=Authorize.only(Global.creator_address()))
    def create_start_lottery(self):
        return Seq(
            Pop(self.winners.create()),
        )
    
    @external(authorize=Authorize.only(Global.creator_address()))
    def setup(self):
        return Seq(
            self.start_lottery.set(Int(1)),
            
        )

    @external
    def register(self):
        return Seq(
            Assert(
                self.start_lottery == Int(1),
                Not(self.lotteryPlayers[Txn.sender()].exists())
            ),

            (idx := abi.Uint64()).set(Int(0)),
            (amount := abi.Uint64()).set(Int(0)),
            (played := abi.Uint64()).set(Int(0)),
            (pl := Players()).set(idx, amount, played),

            self.lotteryPlayers[Txn.sender()].set(pl)

        )

    @internal
    def can_play(self):
        return Seq(
            Assert(
                self.start_lottery == Int(1),
                self.lotteryPlayers[Txn.sender()].exists()
            ),
        )

    @external
    def play(self, payment: abi.PaymentTransaction):
        return Seq(
            self.can_play(),

            # Make sure he has not played before

            (pl := Players()).decode(self.lotteryPlayers[Txn.sender()].get()),

            (hp := abi.Uint64()).set(pl.has_played), 
            Assert(hp.get() == Int(0)),

            # Go ahead and play by making deposit and creating a box and setting the properties
            Assert(
                payment.get().amount() == Int(100),
                payment.get().receiver() == self.address
            ),
           
            self.lotteryPlayId.increment(),

            (idx := abi.Uint64()).set(self.lotteryPlayId),
            (amount := abi.Uint64()).set(payment.get().amount()),
            (played := abi.Uint64()).set(Int(1)),

            pl.set(idx, amount, played),
            self.lotteryPlayers[Txn.sender()].set(pl),      
    
        )
    

    @external(authorize=Authorize.only(Global.creator_address()))
    def get_winner(self):
        pass

    # @external()
    # def get_play(self, player: abi.Address, *, output: Players):
    #     return self.lotteryPlayers[player].store_into(output)


    # @external
    # def reset(self):
    # delete all boxes except for the list and set everything to 0
    #     pass

Lottery().dump()
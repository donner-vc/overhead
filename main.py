from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.script import Script
from identity import Id
from helper import print_tx

from typing import List

def main():
    print('Computing the transactions and off-chain communication costs of the Donner virtual channel construction')
    # Following the overhead evaluation of https://eprint.iacr.org/2021/176.pdf
    id_u0 = Id(
        'e120477e329a0f15bcf975c86181828f2e015bfe34e2efe9af6362c8d53a13e2')  # addr: mxiFd6G7RbpJY6sdUhMknT78hTDPJUdE3e
    print(id_u0.addr)
    id_u0_stealth = Id(
        'e12049bc238a0f15bcf576c86171828f3e0363cb2ac2efe9af6362c8d53a22c5')  # addr: mzRZKnpNRshmi6pNUaHc1gxrpnp4UVpdX5
    print(id_u0_stealth.addr)
    id_u1 = Id(
        'e12046ad146a0f15bcf974c86181828f1e0472ea1bd2efe9af6362c8d53a41a7')  # addr: mwhZnxZYLJQa6uPWn2qLF9J3jDiauH4BwT
    print(id_u1.addr)
    id_u1_stealth = Id(
        'e12046ad146a0f15bcf973c86181828f1e0472ea1bd2efe9af6362c8d54b42b7')  # addr: mxDNMmPPgpXEwVw9HZoF2Zck9UjGW9cnDp
    print(id_u1_stealth.addr)
    id_multi_01 = Id(
        'e12046ad246a0f15bef982c86181828f1e0472ea1bd2efe9af6362c8d53a41b8')  # addr: mp3X5j5adS6XnwrfBJ4JB4QMzFetMMXKCd
    print(id_multi_01.addr)
    id_u2 = Id(
        'e12046ad146a0f15bcf975c86181828f1e0472ea1bd2e3a3af6362c8d53a71e5')  # addr: muRD4ggRmuLNZYzW6tfBoHJHRKyk4KstCy
    print(id_u2.addr)
    id_multi_12 = Id(
        'e12046ad246a0f15bcf982c86181828f1d0372ea1bd2efe9af6362c8d53a82c1')  # addr: mozySLpwxEpzGt5RDumEG8uRVqWaA2RGRt
    print(id_multi_12.addr)
    id_u2_stealth = Id(
        'e12046ad146a0f15bcf973c86172828f1e0472ea1be2efe9bc2743c8d54b42b7')  # addr: mpRJrRQcVQSNxoYZ6dQ9uf1gtHSiZp7G77
    print(id_u2_stealth.addr)
    id_multi_02 = Id(
        'e12046ad146a0f15bcf973c86181828f1e0472ea1bd2efe9af6362c8d52f38c5')  # addr: moBBWFJtD1cHTFadoKRfhuAk56GKJ1FEPj
    print(id_multi_02.addr)

    tx_state_in = TxInput('98f209d606ea0e5222ae2296e310fc0f96741f083eb0fe6ca5ff3c6a277217bf', 0) # 0.01 BTC = 1000000 satoshi
    tx_vc_in = TxInput('ad38ac30504e7a6c08f9ec20b2544ab9be24172617e5724dc69c27481d4a3719', 1) # 0.00022 BTC = 22000 satoshi

    fee = 100
    eps = 1
    n=2
    t=10
    delta=2
    a=100000
    balLeft=500000
    balRight=500000
    vc_amount = 50000

    txvcintx = get_txvc_in_tx(tx_vc_in, id_u0, id_u0_stealth, 2*fee+n*eps)
    print_tx(txvcintx, 'Input tx of tx_vc')
    txvc = get_txvc(tx_vc_in, id_u0, [id_u0_stealth], id_multi_02, vc_amount, fee, eps)
    print_tx(txvc, 'tx_vc 1 intermediary')
    txvc = get_txvc(tx_vc_in, id_u0, [id_u0_stealth, id_u1_stealth], id_multi_02, vc_amount, fee, eps)
    print_tx(txvc, 'tx_vc 2 intermediaries')
    txvc = get_txvc(tx_vc_in, id_u0, [id_u0_stealth, id_u1_stealth, id_u2_stealth], id_multi_02, vc_amount, fee, eps)
    print_tx(txvc, 'tx_vc 3 intermediaries')
    tx_state = get_state(tx_state_in, id_multi_01, id_u0, id_u1, a, balLeft, balRight, fee, t, delta)
    print_tx(tx_state, 'State transaction holding the collateral conract: tx_state')
    tx_refund = get_tx_refund(TxInput(txvc.get_hash(), 0), TxInput(tx_state.get_hash(), 0), id_u0, id_u0_stealth, id_multi_01, 100000, 2*fee)
    print_tx(tx_refund, 'tx_refund')
    tx_pay = get_tx_pay(TxInput(tx_state.get_hash(), 0), id_u1, a, 2*fee)
    print_tx(tx_pay, 'tx_pay')
    print(f'from https://eprint.iacr.org/2020/476.pdf we know that updating a channel takes 2 transactions of 695 bytes')


def get_state(tx_in0: TxInput, id_multisig: Id, id_l: Id, id_r: Id, a: float, x_left: float, x_right: float,
              fee: float, t: int, delta: int = 0x02) -> Transaction:
    script = Script(['OP_IF',
            id_multisig.pk.to_hex(), 'OP_CHECKSIGVERIFY', delta, 'OP_CHECKSEQUENCEVERIFY',
            'OP_ELSE',
            id_r.pk.to_hex(), 'OP_CHECKSIGVERIFY', t, 'OP_CHECKLOCKTIMEVERIFY',
            'OP_ENDIF', 0x1]) # requires scriptsig: multisig, 0x1 or r_sig, 0x0

    tx_out0 = TxOutput(a, script)
    tx_out1 = TxOutput(x_left - a - fee, id_l.p2pkh)
    tx_out2 = TxOutput(x_right, id_r.p2pkh)

    tx = Transaction([tx_in0], [tx_out0, tx_out1, tx_out2])

    sig_multisig = id_multisig.sk.sign_input(tx, 0, id_multisig.p2pkh)

    tx_in0.script_sig = Script([sig_multisig, id_multisig.pk.to_hex()])

    return tx

def get_txvc_in_tx(tx_in: TxInput, id_sender: Id, id_sender_stealth: Id, a: float) -> Transaction:
    # tx_in must hold at least n times eps coins plus a fee
    tx_out0 = TxOutput(a, id_sender_stealth.p2pkh)

    tx_vc_in = Transaction([tx_in], [tx_out0])

    sig_sender = id_sender.sk.sign_input(tx_vc_in, 0, id_sender.p2pkh)

    tx_in.script_sig = Script([sig_sender, id_sender.pk.to_hex()])

    return tx_vc_in

def get_txvc(tx_in: TxInput, id_sender: Id, id_list: List[Id], id_multisig: Id, vc_amount:float, fee: float, eps: float = 1) -> Transaction:
    # tx_in must hold at least n times eps coins plus a fee
    # tx_out0 = TxOutput(eps, id_sender.p2pkh)
    out_list = [TxOutput(vc_amount, id_multisig.p2pkh)]
    for id in id_list:
        out_list.append(TxOutput(eps, id.p2pkh))

    txvc = Transaction([tx_in], out_list)

    sig_sender = id_sender.sk.sign_input(txvc, 0, id_sender.p2pkh)

    tx_in.script_sig = Script([sig_sender, id_sender.pk.to_hex()])

    return txvc

def get_tx_refund(tx_in_txvc: TxInput, tx_in_state: TxInput, id_left: Id, id_left_stealth: Id, id_multisig: Id, a: float, fee: float, eps: float = 1) -> Transaction:
    # tx_in must hold at least n times eps coins plus a fee
    tx_out0 = TxOutput(a+eps-fee, id_left.p2pkh)

    tx = Transaction([tx_in_txvc, tx_in_state], [tx_out0])

    sig_left_stealth = id_left_stealth.sk.sign_input(tx, 0, id_left_stealth.p2pkh)
    sig_multi = id_multisig.sk.sign_input(tx, 0, id_multisig.p2pkh)

    tx_in_txvc.script_sig = Script([sig_left_stealth, id_left_stealth.pk.to_hex()])
    tx_in_state.script_sig = Script([sig_multi, 0x1])

    return tx

def get_tx_pay(tx_in_state: TxInput, id_right: Id, a: float, fee: float) -> Transaction:
    # tx_in must hold at least n times eps coins plus a fee
    tx_out0 = TxOutput(a-fee, id_right.p2pkh)

    tx = Transaction([tx_in_state], [tx_out0])

    sig_right = id_right.sk.sign_input(tx, 0, id_right.p2pkh)

    tx_in_state.script_sig = Script([sig_right, 0x0])

    return tx

if __name__ == "__main__":
    main()

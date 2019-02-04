#https://github.com/pytransitions/transitions/issues/249
def state0(asks, bids, th_spread=0.05):
    # idle and check spread
    satoshi = Decimal('0.00000001')
    test_ask = find_price(asks, th_ask, start_tsize_ask)
    test_bid = find_price(bids, th_bid, start_tsize_bid)
    spread = (test_ask - test_bid)/test_bid
    spread = spread.quantize(satoshi)



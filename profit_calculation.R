wd = paste0(Sys.getenv('USERPROFILE'), '/Downloads')
setwd(wd)

library('data.table')
dat = read.csv('data.csv')
setDT(dat)

calculate_profit = function(dat, blacklist = c('OPEN.BTC', 'XMR', 'BCO')) {

    sub = dat[!Asset.bought %in% blacklist & !Asset.sold %in% blacklist]

    buy = sub[, .('btcbought' = sum(Amount.in.BTC), 'quotebought' = sum(Amount.received), 'meanprice' = mean(Price)), Asset.bought]
    sell = sub[, .('btcsold' = sum(Amount.in.BTC), 'quotesold' = sum(Amount.paid)), Asset.sold]

    m = merge(buy, sell, by.x = 'Asset.bought', by.y = 'Asset.sold')
    m[, 'inventory' := quotebought - quotesold]
    m[, 'inventory_value' := inventory * meanprice]

    mm = m[Asset.bought != 'BTC']

    outl = list(
                # Values in Bitcoin
                'sold' = mm[, sum(btcsold)],
                'bought' = mm[, sum(btcbought)],
                'inventory_value' = mm[, sum(inventory_value)]
                )

    outl$profit = outl$sold - outl$bought + outl$inventory_value

    return(outl)
}

calculate_profit(dat)


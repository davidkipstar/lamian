wd = paste0(Sys.getenv('USERPROFILE'), '/Downloads')
setwd(wd)

library('data.table')
dat = read.csv('data.csv')
setDT(dat)

calculate_profit = function(dat, blacklist = c('OPEN.BTC', 'XMR', 'BCO')) {

    sub = dat[!Asset.bought %in% blacklist & !Asset.sold %in% blacklist]

    outl = list(
                'sold' = sub[Asset.sold == 'BTC', sum(Amount.in.BTC)],
                'bought' = sub[Asset.bought == 'BTC', sum(Amount.in.BTC)]
                )

    return(outl)
}

calculate_profit(dat)


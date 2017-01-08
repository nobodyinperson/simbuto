#!/usr/bin/Rscript
# simbuto

#### functions ####
read_budget_from_text <- function(text) {
    BUDGET <- read.csv2(text=text, stringsAsFactors = F, na.strings = c("NA"),comment.char="#")
    BUDGET$amount <- as.numeric(BUDGET$amount)
    BUDGET$start <- as.Date(BUDGET$start,format="%F")
    BUDGET$end <- as.Date(BUDGET$end,format="%F")
    return(BUDGET)
}

timeseries_from_budget <- function(budget, start = Sys.Date(), end = Sys.Date() + 365) {
    # create empty frame with day series
    all.days <- seq.Date(from = start, to = end, by = "days")
    MONEY <- data.frame(day = all.days, amount = 0)
    
    for (factnr in 1:nrow(budget)) { # loop over all facts
        fact <- budget[factnr,] # current fact
        # create sequence of occurence days
        # print(fact)
        fact.start <- if(is.na(fact$start)){start}else{fact$start}
        fact.end   <- if(is.na(fact$end)){end}else{fact$end}
        # cat("fact ",fact$title," occurs ",fact$frequency," from ",fact.start," to ",fact.end,"\n")
        number.occurences <- NULL
        if(fact$frequency == "once") {
            number.occurences <- 1
            interval <- NULL
        } else if(fact$frequency == "monthly") {
            interval <- "month"
        } else if(fact$frequency == "yearly") {
            interval <- "year"
        } else if(fact$frequency == "weekly") {
            interval <- "week"
        } else {
            interval <- fact$frequency
        }
        
        
        # cat("from=",fact.start," to=",fact.end," by=",interval," length.out=",number.occurences,"\n")
        if(fact.start < fact.end) {
            if(is.numeric(number.occurences)){
                occurences <- seq.Date(from = fact.start, to = fact.end, length.out = number.occurences)
            } else {
                occurences <- seq.Date(from = fact.start, to = fact.end, by = interval)
            }
        }
        
        # add to time series
        indices <- na.omit(match(x = occurences, table = MONEY$day))
        # cat("indices: ",indices)
        MONEY[indices,"amount"] = MONEY[indices,"amount"] + fact$amount
    }
    MONEY$amount = cumsum(MONEY$amount)
    # empty data frame
    return(MONEY)
}

plot_budget_timeseries <- function(timeseries) {
    # base plot
    plot(timeseries,type="n",xaxt="n",yaxt="n"
         ,ylab="",xlab="",main=paste(timeseries$day[2]," - ",timeseries$day[length(timeseries$day)]))
    
    axismoney <- axis(side = 2,las=1)
    axisdates <- axis.Date(side = 1, x = timeseries$day)
    abline(v = axisdates, h = axismoney, lty = 2, col = "darkgray")
    abline(h = 0, col = "black")
    
    # rectangle arguments
    pu <- as.list(par("usr"))
    names(pu) <- c("xleft","xright","ybottom","ytop")
    pu$border = NA
    bad <- good <- middle <- pu
    good$ybottom = 500
    good$col = "#00ff0033"
    middle$ytop = good$ybottom 
    middle$ybottom = 0
    middle$col = "#ffff0033"
    bad$ytop = 0
    bad$col = "#ff000099"
    
    do.call(rect, good)
    do.call(rect, middle)
    do.call(rect, bad)
    
    lines(x = timeseries$day, y = timeseries$amount
          ,lwd = 4
          )
}

plot_budget_timeseries_to_png <- function(timeseries,filename,width=600,height=400) {
    png(file=filename,width=width, height=height)
    plot_budget_timeseries(timeseries)
    dev.off()
}


#### read data ####
# BUDGET <- read_budget_from_text(readLines("budget.simbuto"))
# MONEY <- timeseries_from_budget(budget = BUDGET)
# plot_budget_timeseries(MONEY)


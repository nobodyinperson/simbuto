#!/usr/bin/Rscript
# simbuto

#### functions ####
read_budget_from_text <- function(text) {
    BUDGET <- read.csv2(text=text, stringsAsFactors = F, na.strings = c("NA"),comment.char="#")
    BUDGET$amount <- as.numeric(BUDGET$amount)
    if(!is.null(BUDGET$tolerance))
        BUDGET$tolerance <- as.numeric(BUDGET$tolerance)
    BUDGET$start <- as.Date(BUDGET$start,format="%F")
    BUDGET$end <- as.Date(BUDGET$end,format="%F")
    return(BUDGET)
}

timeseries_from_budget <- function(
    budget, 
    start = Sys.Date(), end = Sys.Date() + 365,
    with_tolerance = FALSE,
    random_tolerance = FALSE
    ) {
    # create empty frame with day series
    all.days <- seq.Date(from = start, to = end, by = "days")
    MONEY <- data.frame(day = all.days, amount = 0)
    if(with_tolerance) 
        MONEY$mincase <- MONEY$maxcase <- 0
    
    for (factnr in 1:nrow(budget)) { # loop over all facts
        fact <- budget[factnr,] # current fact
        # create sequence of occurence days
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
        } else if(fact$frequency == "dayly") {
            interval <- "day"
        } else {
            interval <- fact$frequency
        }
        
        
        # cat("from=",fact.start," to=",fact.end," by=",interval," length.out=",number.occurences,"\n")
        occurences <- c()
        if(fact.start < fact.end) {
            if(is.numeric(number.occurences)){
                occurences <- seq.Date(from = fact.start, to = fact.end, length.out = number.occurences)
            } else {
                occurences <- seq.Date(from = fact.start, to = fact.end, by = interval)
            }
        }
        
        # get the indices
        indices <- na.omit(match(x = occurences, table = MONEY$day))
        # cat("indices: ",indices)
        
        # generate random sequence
        fact.amount = fact$amount
        amounts <- fact.amount
        fact.mincase <- fact.maxcase <- fact.amount
        if(with_tolerance) { # only if specified
            if(any(is.finite(fact$tolerance))) { # only if tolerance is given
                fact.tolerance = abs(as.numeric(fact["tolerance"]))
                if(random_tolerance) {
                    # cat("tolerance: ",fact.tolerance,"\n")
                    amounts <- runif(length(indices),
                                    min = fact.amount - fact.tolerance,
                                    max = fact.amount + fact.tolerance)
                } else {
                    fact.mincase <- fact.amount - fact.tolerance
                    fact.maxcase <- fact.amount + fact.tolerance
                }
            }
            MONEY[indices,"mincase"] = MONEY[indices,"mincase"] + fact.mincase
            MONEY[indices,"maxcase"] = MONEY[indices,"maxcase"] + fact.maxcase
        }
        
        # add to time series
        MONEY[indices,"amount"] = MONEY[indices,"amount"] + amounts
    }
    MONEY$amount = cumsum(MONEY$amount)
    MONEY$mincase = cumsum(MONEY$mincase)
    MONEY$maxcase = cumsum(MONEY$maxcase)
    # empty data frame
    return(MONEY)
}

budget_ensemble<- function( budget,  
    start = Sys.Date(), end = Sys.Date() + 365,
    ensemble_size = 100
    ) {
    # run without tolerance
    timeseries_without_tolerance <- timeseries_from_budget(
        budget = budget, start = start, end = end, with_tolerance = TRUE, 
        random_tolerance = FALSE)
    # the ensemble out starts with the bare run
    ENSEMBLE_OUT <- timeseries_without_tolerance
    if(any(is.finite(budget$tolerance))) {
        # create ensemble matrix
        ENSEMBLE <- matrix(NA,nrow=ensemble_size, ncol = nrow(ENSEMBLE_OUT))
        # do the runs
        # cat("create members...")
        for(i in 1:ensemble_size) {
            ENSEMBLE[i,] <- timeseries_from_budget( budget = budget, 
                        start = start, end = end, 
                        with_tolerance = TRUE, random_tolerance=TRUE)$amount
        }
        cat("done!\n")
        # calculate statistics
        # cat("calculate statistics...")
        ENSEMBLE_OUT$ensmean <- apply(X = ENSEMBLE,MARGIN = 2, FUN = mean)
        ENSEMBLE_OUT$ensmedian <- apply(X = ENSEMBLE,MARGIN = 2, FUN = median)
        ENSEMBLE_OUT$ensquant25 <- apply(X = ENSEMBLE,MARGIN = 2, FUN = function(x)quantile(x,probs = c(0.25)))
        ENSEMBLE_OUT$ensquant75 <- apply(X = ENSEMBLE,MARGIN = 2, FUN = function(x)quantile(x,probs = c(0.75)))
        ENSEMBLE_OUT$ensmin <- apply(X = ENSEMBLE,MARGIN = 2, FUN = min)
        ENSEMBLE_OUT$ensmax <- apply(X = ENSEMBLE,MARGIN = 2, FUN = max)
        # cat("done!\n")
    }
    return(ENSEMBLE_OUT)
}

plot_budget_timeseries <- function(timeseries) {
    plotrange <- range(c(timeseries$amount,timeseries$mincase,
                         timeseries$maxcase,timeseries$ensmin,timeseries$ensmax))
    # base plot
    plot(timeseries$day,timeseries$amount,type="n",xaxt="n",yaxt="n"
         ,ylab="",xlab="",ylim=plotrange,
         main=paste(timeseries$day[1]," - ",timeseries$day[length(timeseries$day)]))
    
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
    
    # worst/best cases
    if(!is.null(timeseries$mincase) & !is.null(timeseries$maxcase)) {
        polygon(x = c(timeseries$day,rev(timeseries$day)), 
                y = c(timeseries$mincase,rev(timeseries$maxcase)),
                col = "#00000022",border=NA)
    }
    # ensemble max/min
    if(!is.null(timeseries$ensmin) & !is.null(timeseries$ensmax)) {
        polygon(x = c(timeseries$day,rev(timeseries$day)), 
                y = c(timeseries$ensmax,rev(timeseries$ensmin)),
                col = "#00000033",border=NA)
    }
    # ensemble quantiles
    if(!is.null(timeseries$ensquant25) & !is.null(timeseries$ensquant75)) {
        polygon(x = c(timeseries$day,rev(timeseries$day)), 
                y = c(timeseries$ensquant75,rev(timeseries$ensquant25)),
                col = "#00000044",border=NA)
    }
    # raw run
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
# BUDGET <- read_budget_from_text(readLines("~/Downloads/budget.simbuto"))
# # MONEY <- timeseries_from_budget(budget = BUDGET, with_tolerance = TRUE)
# MONEY <- budget_ensemble(budget = BUDGET)
# cat("plotting...")
# plot_budget_timeseries(MONEY)
# cat("done!\n")
# 

#!/usr/bin/Rscript
# simbuto

#### functions ####
read_budget_from_text <- function(text) {
    BUDGET <- read.csv2(text=text, stringsAsFactors = F, na.strings = c("NA"),comment.char="#")
    BUDGET$amount <- as.numeric(BUDGET$amount)
    if(!is.null(BUDGET$tolerance_amount))
        BUDGET$tolerance_amount <- as.numeric(BUDGET$tolerance_amount)
    BUDGET$start <- as.Date(BUDGET$start,format="%F")
    BUDGET$end <- as.Date(BUDGET$end,format="%F")
    BUDGET$frequency[BUDGET$frequency == "monthly"] = "month"
    BUDGET$frequency[BUDGET$frequency == "weekly"] = "week"
    BUDGET$frequency[BUDGET$frequency == "yearly"] = "year"
    BUDGET$frequency[BUDGET$frequency == "daily"] = "day"
    return(BUDGET)
}

timeseries_from_budget <- function(
    budget, 
    start = Sys.Date(), end = Sys.Date() + 365,
    ensemble_size = NULL
    ) {
    # create empty frame with day series
    all.days <- seq.Date(from = start, to = end, by = "days")
    MONEY <- data.frame(day = all.days, amount = 0)
    
    # start with empty series
    worstcase <- bestcase <- undisturbed <- rep(0, nrow(MONEY))
    # loop over all facts
    for (factnr in 1:nrow(budget)) {
        fact <- budget[factnr,] # current fact
        # create sequence of occurence days
        fact.start <- if(is.na(fact$start)){start}else{fact$start}
        fact.end   <- if(is.na(fact$end)){end}else{fact$end}
        # cat("fact ",fact$title," occurs ",fact$frequency," from ",fact.start," to ",fact.end,"\n")
        interval = fact$frequency
        if(interval == "once") {
            fact.end <- fact.start
            interval = "day" # pick any interval, doesn't matter
        }
        # cat("from=",fact.start," to=",fact.end," by=",interval," length.out=",number.occurences,"\n")
        occurences <- c()
        if(fact.start <= fact.end) {
            occurences <- seq.Date(from = fact.start, to = fact.end, by = interval)
        }
        
        occurences_bool <- MONEY$day %in% occurences
        
        # get the indices
        indices <- na.omit(match(x = occurences, table = MONEY$day))
        undisturbed <- undisturbed + fact_amounts_series(
            occurences = occurences_bool, fact = fact,with_tolerance = FALSE)
        worstcase <- worstcase + fact_amounts_series(
            occurences = occurences_bool, fact = fact,with_tolerance = TRUE, 
            worst_case = TRUE )
        bestcase <- bestcase + fact_amounts_series(
            occurences = occurences_bool, fact = fact,with_tolerance = TRUE, 
            worst_case = FALSE )
    }
        
    # cumulate
    MONEY$amount    = cumsum(undisturbed)
    MONEY$worstcase = cumsum(worstcase)
    MONEY$bestcase  = cumsum(bestcase)
    # empty data frame
    return(MONEY)
}

fact_amounts_series <- function(
    fact, # the fact dataframe row/list
    occurences, # boolean vector with TRUE where the fact occurs, output has same length
    with_tolerance = FALSE, # use the tolerance?
    worst_case = FALSE, # TRUE = worst_case, FALSE = best_case
    random_tolerance = FALSE # if using the tolerance, randomize?
    ) {
    stopifnot(nrow(fact)==1)
    
    # the indices where the fact occurs
    indices <- which(occurences)
    # the output sequence starts with zeros everywhere
    out <- rep(0,length(occurences))
    # output length
    N <- length(out)
    
    # the tolerances
    fact_tolerance_day <- 0
    if(any(is.finite(fact$tolerance_day)))
            fact_tolerance_day = as.integer(abs(fact$tolerance_day))
    fact_tolerance_amount <- 0
    if(any(is.finite(fact$tolerance_amount)))
            fact_tolerance_amount = abs(fact$tolerance_amount)
    # fact data
    fact_amount <- 0
    if(any(is.finite(fact$amount)))
            fact_amount = fact$amount
    
    if(with_tolerance) {
        if(random_tolerance) {
            # modify amount randomly
            amounts <- runif( n = length(indices), 
                              min = fact_amount - fact_tolerance_amount,
                              max = fact_amount + fact_tolerance_amount
                              )
            # modify indices randomly
            indices <- indices + runif( n = length(indices), 
                              min = - fact_tolerance_amount,
                              max = + fact_tolerance_amount
                              )
        } else {
            if(worst_case) {
                # worst case: all costs are highest
                # worst case: all incomes are lowest
                amounts <- rep(fact_amount - fact_tolerance_amount, length(indices))
                # worst case: all costs are earliest
                # worst case: all incomes are latest
                indices <- indices + sign(fact_amount) * fact_tolerance_day
            } else {
                # best case: all costs are lowest
                # best case: all incomes are highest
                amounts <- rep(fact_amount + fact_tolerance_amount, length(indices))
                # best case: all costs are latest
                # best case: all incomes are earliest
                indices <- indices - sign(fact_amount) * fact_tolerance_day
            }
        # fix indices that lie outside the output vector
        # cat("indices before fixing: ",indices,"\n")
        # cat("amounts before fixing: ",amounts,"\n")
        tooearly <- which(indices < 1)
        # cat("too early indices: ",indices[tooearly],"\n")
        # stopifnot(length(tooearly)==0)
        toolate  <- which(indices > N)
        # cat("too late indices: ",indices[toolate],"\n")
        outside  <- sort(unique(c(tooearly,toolate)))
        out[1] <- out[1] + sum(amounts[tooearly])
        out[N] <- out[N] + sum(amounts[toolate])
        if(length(outside)>0) {
            amounts <- amounts[-(outside)]
            indices <- indices[-(outside)]
        }
        # cat("indices after fixing: ",indices,"\n")
        # cat("amounts after fixing: ",amounts,"\n")
        }
    } else {
        # keep amount
        amounts <- rep(fact_amount, length(indices))
    }
    # cat("amounts before putting into out: ",amounts,"\n")
    
    # set the amounts to the indices
    out[indices] <- amounts
    # cat("out: ",out,"\n")
    
    # return out vector
    return(out)
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
    if(any(is.finite(budget$tolerance_amount))) {
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
    plotrange <- range(c(timeseries$amount,timeseries$worstcase,
                         timeseries$bestcase,timeseries$ensmin,timeseries$ensmax))
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
    if(!is.null(timeseries$worstcase) & !is.null(timeseries$bestcase)) {
        polygon(x = c(timeseries$day,rev(timeseries$day)), 
                y = c(timeseries$worstcase,rev(timeseries$bestcase)),
                col = "#00000022",border=NA)
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
# MONEY <- timeseries_from_budget(budget = BUDGET)
# cat("plotting...")
# plot_budget_timeseries(MONEY)
# cat("done!\n")

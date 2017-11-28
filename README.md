# Project 3: Deliverable I

Project description: https://www.cs.usfca.edu/~mmalensek/courses/cs686/projects/project-3.html

## Three questions from Project 2

### Driest Month in the San Francisco Bay Area

Framework agnostic pseudo code:

    humidity_totals = array<double>[12]
    humidity_counts = array<long>[12]

    for row in dataset:
        m = row.timestamp.month
        humidity_totals[m] += row.relative_humidity_zerodegc_isotherm
        humidity_counts[m]++
        
    for m in January..December:
        avg = humidity_totals[m] / humidity_counts[m]
        print "Average humidity for $m: $avg"
        
In project 2, with Hadoop MapReduce, I fed a key-value pair of <month,humidity> for each observation to the mapper, which then gets <month,list<humidity>> as input and can easily compute the averages.
  
We could do the same with Spark by using the *map* and *reduceByKey* transformations. We could also use *aggregateByKey* and provide an average function as our aggregation method. Or simply sum the values as an aggregation and then use *countByKey* to calculate the average (can be trivially computed on the client). Or calculate that average using the *reduce* action (I think?) by calculating the average of two values, and the average of that, and the average of that, until there are no more values.

Another idea, which I'll explore here, is to use 2 x 12 Accumulators to implement the pseudo code above, thus avoiding any kind of reduce task altogether. The average is then trivially computed on the client. I am hoping that this should be rather fast.
  


### A Year of Travel

### Hottest Temperature


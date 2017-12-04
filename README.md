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
  
The first thing to do is to create those accumulators:

```python
counts = []
totals = []

for i in range(0, 12):
    counts.append(sc.accumulator(0.0)) # accumulator starts with value 0
for i in range(0, 12):
    totals.append(sc.accumulator(0.0))
```

and then we simply iterate over all the data and update them:

```python
import datetime

def timestamp_to_month(ts):
    return datetime.datetime.fromtimestamp(ts / 1e3).month

def update_accumulators(row):
    m = timestamp_to_month(row.Timestamp) - 1
    humidity = row.relative_humidity_zerodegc_isotherm
    totals[m].add(humidity)
    counts[m].add(1)
    
df.foreach(update_accumulators)

averages = []
for i in range(0,12):
    averages.append(totals[i].value / counts[i].value)
```

Simple enough, right? Well... after working for 58 min, Spark stopped and barked at me, because my code contained a bug. The problem is that unlike Java in Python `datetime.month` returns 1-12 but arrays are 0-indexed, also I forgot that `range(1,12)` produces 1, 2, ... 9, 10. The nice thing about this of course being that the program crashes only when processing December data, i.e. the last 8 % of the dataset. Genius!
But that's not the most important lesson here. That would be: test the code on the mini dataset first!
Also, this "query" seems painfully slow. Indeed it took 2.6 hours on my machine (3.1 GHz Core i7, 16 GB RAM). That's weird...

The results:

|Month|Average humidity|
|---|---:|
|January|57.48|
|February|54.57|
|March|52.70|
|April|54.42|
|May|52.10|
|June|51.83|
|July|51.19|
|August|50.36|
|September|50.36|
|October|51.17|
|November|53.84|
|December|55.37|

This looks very incorrect, not at all what I found in project 2.
That's because I forgot to bound my query to the Bay Area. Duh!

Since this was so slow, I ran it using the map and reduce paradigm, and threw a filter in there:

```python
prefixes = ("9q8u", "9q8v", "9q8y", "9q8z", "9q9h", "9q9j", "9q9k", "9q9m", "9q9n", "9q9p")

df.rdd\
    .filter(lambda row: row.Geohash.startswith(prefixes))\
    .map(lambda row: (timestamp_to_month(row.Timestamp), row.relative_humidity_zerodegc_isotherm))\
    .reduceByKey(lambda humidity1, humidity2: (humidity1 + humidity2)/2.0)\
    .collect()
```

and obtained this:

|Month|Average humidity|
|---|---:|
|January  |32.79|
|February |15.00|
|March    |19.08|
|April    |21.90|
|May      |19.36|
|June     |35.50|
|July     |27.29|
|August   |23.12|
|September|28.72|
|October  |36.10|
|November |47.33|
|December |68.04|

Now, that's better. Although the numbers are not the same as in project 2, probably because this comes from a sample, the general trend is the same, and we also find that the driest month of the year is around the end of the winter, though this time in February rather than March.

### A Year of Travel

Reminder:

During my year of travel I would like to visit:

  - dxfy: Halifax, Nova Scotia
  - dk2y: Nassau, Bahamas
  - dpky: Niaga Falls
  - 9whp: Albuquerque
  - 9xhv: Colorado Rockies
  
I had a few criteria such as the temperature and absence of snow.
Also I would like to be visit each destination at least two days in a row.
Here is how I implemented it with Spark:

```python
import numpy as np

def day_of_year(ts):
    return datetime.datetime.fromtimestamp(ts / 1e3).timetuple().tm_yday

# [1, 3, 1, 7, 2, 9, 10] => [[1, 2, 3], [9, 10]]
def consecutive(data):
    data = np.unique(np.array(data))
    # this line from https://stackoverflow.com/a/7353335/753136 :
    arr = np.split(data, np.where(np.diff(data) != 1)[0]+1) 
    return [x.tolist() for x in arr if np.size(x) > 1]

prefixes = (
            "dxfy", # Halifax, Nova Scotia
            "dk2y", # Nassau, Bahamas
            "dpxy", # Niagara Falls
            "9whp", # Albuquerque
            "9xhv"  # Rocky Mountain
           )

df.rdd\
    .filter(lambda row: \
        row.Geohash.startswith(prefixes) and
        row.temperature_surface > 290 and 
        row.temperature_surface < 301 and
        row.snow_depth_surface < 0.01 and
        row.categorical_rain_yes1_no0_surface == 0.0
        )\
    .map(lambda row: (row.Geohash[0:4], day_of_year(row.Timestamp)))\
    .map(lambda tple: (tple[0], [ tple[1] ] ))\
    .reduceByKey(lambda a,b: a + b)\
    .map(lambda tple: (tple[0], consecutive(tple[1])))\
    .filter(lambda tple: len(tple[1]) > 0)\
    .sortByKey()\
    .collect()
```

and this returned the following results:

```
[('9whp', [[202, 203, 204]]),
 ('dk2y', [[7, 8, 9, 10], [46, 47], [322, 323], [343, 344]]),
 ('dpxy', [[241, 242]])]
 ```
 
 in other words:
 
 |Destination|Days|
 |---|---|
 |Albuquerque|July 21-23|
 |Bahamas|January 7-10, February 15-16, November 18-19, December 9-10|
 |Niagara Falls|August 29-30|
 
 As you can see there haven't been two consecutive days in 2015 where Halifax and the Rockies were warm enough for me to go, so I'll just skip those destinations I guess...

### Hottest Temperature

Here I used an SQL to find the maximum temperature, 329 K, at d59eknqv867b, a place about a 2.5 hour drive from Cancun, Mexico, which is also what I found in Project 2.

### Overview of my experience

I wrote this section in the form of pros and cons for each framework, **regarding this question only.**

#### Pros of Spark
  
   * Python API has all important features of the native Scala API
   * Can just play around in a single Jupyter notebook, no need to create files, compile them, etc.
   * All the code at the same place
   * Easy to look at intermediary data ("What is my map function generating?")
   * Fancy data sources, can use tables, I could access features by name easily
   * SQL queries
   * Builtin aggregate functions (stddev, mean, ...)
   * Web UI is really cool to see what is going on

#### Cons of Spark

   * Complex API with tons of operations
   * Input / Output of operations not always clear
   * Not clear what approach is best, and faster
   * Painful refactoring necessary if map functions needs to return multiple values
   * Learning curve
   * Operations are inflexible
   * Unpleasant stacktraces
   
#### Pros of MapReduce

   * Straightforward API
   * Almost no Googling required
   * Map and Reduce are actually quite flexible, can return 0, 1, n values
   * Mapper and Reducer can emit another key easily
   
#### Cons of MapReduce

    * Files, compilation, ...
    * Java-only, Python supported only through pipes, so no access to API
    * Requires a main() method (=> Job class)
    * Cannot look at intermediary results
    * Couldn't use my own Writable (Out of Memory errors)
    * Comes with very little, might need boilerplate to do common operations

## Statistics for each feature

```python
for col in sorted(df.columns[2:]):
    try:
        row = spark.sql('SELECT MAX(%s), MIN(%s), AVG(%s), STDDEV(%s) FROM TEMP_DF' % (col, col, col, col)).collect()[0]
        print('Feature:', col)
        print('Max value:', row[0])
        print('Min value:', row[1])
        print('Average:', row[2])
        print('Std. dev.:', row[3])
        print()
    except:
        pass
```

This is the code I used to generate the report below. 

[Aggregate functions](http://spark.apache.org/docs/latest/api/scala/index.html#org.apache.spark.sql.functions$) (here used through SQL) came in handy.

```
Feature: albedo_surface
Max value: 80.0
Min value: 6.0
Average: 15.875211110753401
Std. dev.: 15.431209368902676

Feature: categorical_freezing_rain_yes1_no0_surface
Max value: 1.0
Min value: 0.0
Average: 0.0006860636929098981
Std. dev.: 0.026183833492621166

Feature: categorical_ice_pellets_yes1_no0_surface
Max value: 1.0
Min value: 0.0
Average: 0.00030547226456155386
Std. dev.: 0.01747509678826344

Feature: categorical_rain_yes1_no0_surface
Max value: 1.0
Min value: 0.0
Average: 0.08854384646383012
Std. dev.: 0.28408422808959644

Feature: categorical_snow_yes1_no0_surface
Max value: 1.0
Min value: 0.0
Average: 0.027455684318930067
Std. dev.: 0.16340708264318501

Feature: convective_available_potential_energy_surface
Max value: 7160.0
Min value: 0.0
Average: 438.2306865114475
Std. dev.: 897.6515247784854

Feature: convective_inhibition_surface
Max value: 10.7171630859375
Min value: -1270.3416748046875
Average: -11.585870085432866
Std. dev.: 46.21815913426563

Feature: direct_evaporation_cease_soil_moisture_surface
Max value: 0.13499999046325684
Min value: 0.0
Average: 0.03110594852291435
Std. dev.: 0.037380484131604996

Feature: downward_long_wave_rad_flux_surface
Max value: 519.33251953125
Min value: 0.0
Average: 335.87168615582425
Std. dev.: 71.91861473035964

Feature: downward_short_wave_rad_flux_surface
Max value: 1121.1038818359375
Min value: 0.0
Average: 190.75263160239342
Std. dev.: 284.8060079314416

Feature: drag_coefficient_surface
Max value: 48000.0
Min value: 0.0
Average: 0.15554024185410378
Std. dev.: 39.85484170220014

Feature: friction_velocity_surface
Max value: 2.4386146068573
Min value: 7.477789040422067e-05
Average: 0.3284759805524843
Std. dev.: 0.2204706201407389

Feature: geopotential_height_cloud_base
Max value: 14267.0
Min value: -5000.0
Average: -362.3657659567715
Std. dev.: 3283.5747322967245

Feature: geopotential_height_lltw
Max value: 6202.4365234375
Min value: -8015.53125
Average: 2141.460589701559
Std. dev.: 1898.1221123820196

Feature: geopotential_height_pblri
Max value: 5365.2919921875
Min value: 13.405797958374023
Average: 519.8203549129231
Std. dev.: 514.536093836141

Feature: geopotential_height_surface
Max value: 3576.320068359375
Min value: -73.92997741699219
Average: 321.18403584078413
Std. dev.: 549.8004201177264

Feature: geopotential_height_zerodegc_isotherm
Max value: 6326.55224609375
Min value: 0.0
Average: 3092.661752293876
Std. dev.: 1753.1464658864122

Feature: ice_cover_ice1_no_ice0_surface
Max value: 1.0
Min value: 0.0
Average: 0.02289247265273891
Std. dev.: 0.14956072842575954

Feature: land_cover_land1_sea0_surface
Max value: 1.0
Min value: 0.0
Average: 0.46817001205977116
Std. dev.: 0.49898586947522006

Feature: latent_heat_net_flux_surface
Max value: 1000000.125
Min value: -312.7490234375
Average: 2500.6184335680878
Std. dev.: 49249.48549856269

Feature: lightning_surface
Max value: 1.0
Min value: 0.0
Average: 0.03504790049338119
Std. dev.: 0.18390092827869525

Feature: maximumcomposite_radar_reflectivity_entire_atmosphere
Max value: 52.8125
Min value: -20.0
Average: -7.287122246355333
Std. dev.: 15.900977849622198

Feature: mean_sea_level_pressure_nam_model_reduction_msl
Max value: 106000.0
Min value: 94951.0
Average: 101541.29552693132
Std. dev.: 802.4057356789327

Feature: number_of_soil_layers_in_root_zone_surface
Max value: 4.0
Min value: 0.0
Average: 1.5996940466767542
Std. dev.: 1.7434935950250274

Feature: planetary_boundary_layer_height_surface
Max value: 21114.0
Min value: -1000000.0
Average: -1075.3082378663123
Std. dev.: 49332.54353623248

Feature: plant_canopy_surface_water_surface
Max value: 0.5
Min value: 0.0
Average: 0.060422839066438576
Std. dev.: 0.1480723043352639

Feature: precipitable_water_entire_atmosphere
Max value: 96.56735229492188
Min value: 0.413043737411499
Average: 21.60823007175919
Std. dev.: 14.043820227481033

Feature: pressure_maximum_wind
Max value: 50128.13671875
Min value: 11120.640625
Average: 22274.72372442975
Std. dev.: 7195.950880388055

Feature: pressure_reduced_to_msl_msl
Max value: 106272.0
Min value: 94951.0
Average: 101574.21354343016
Std. dev.: 790.8951387655161

Feature: pressure_surface
Max value: 105153.0
Min value: 64793.0
Average: 97921.93197108616
Std. dev.: 6044.402231989741

Feature: pressure_tropopause
Max value: 50103.296875
Min value: 6653.146484375
Average: 18644.448375531134
Std. dev.: 7533.655032286372

Feature: relative_humidity_zerodegc_isotherm
Max value: 100.0
Min value: 1.0
Average: 52.952279718602874
Std. dev.: 31.92960299721519

Feature: sensible_heat_net_flux_surface
Max value: 1000000.125
Min value: -317.9658203125
Average: 2460.591012176307
Std. dev.: 49251.43240969161

Feature: snow_cover_surface
Max value: 100.0
Min value: 0.0
Average: 16.340825082251783
Std. dev.: 36.910389053177084

Feature: snow_depth_surface
Max value: 16.647199630737305
Min value: 0.0
Average: 0.040932397917521
Std. dev.: 0.16044982192655047

Feature: soil_porosity_surface
Max value: 0.5
Min value: 0.0
Average: 0.23408500602988558
Std. dev.: 0.24949293473761003

Feature: soil_type_as_in_zobler_surface
Max value: 16.0
Min value: 0.0
Average: 2.439781258915775
Std. dev.: 3.185327619534401

Feature: surface_roughness_surface
Max value: 2.7500159740448
Min value: 1.5900002836133353e-05
Average: 0.4835673709973284
Std. dev.: 0.8124727164819947

Feature: surface_wind_gust_surface
Max value: 54.797950744628906
Min value: 0.0019546858966350555
Average: 6.847739082294093
Std. dev.: 4.461517224744664

Feature: temperature_surface
Max value: 329.73193359375
Min value: 219.7428436279297
Average: 287.31614237331695
Std. dev.: 14.097624763089414

Feature: temperature_tropopause
Max value: 260.5533447265625
Min value: 184.60946655273438
Average: 210.0485875405655
Std. dev.: 9.712765499794315

Feature: total_cloud_cover_entire_atmosphere
Max value: 100.0
Min value: -1.0000036264390164e+20
Average: -2.4317596621381523e+17
Std. dev.: 4.925296609040394e+18

Feature: upward_long_wave_rad_flux_surface
Max value: 669.976806640625
Min value: 0.0
Average: 384.21388734234324
Std. dev.: 70.9512226919964

Feature: upward_short_wave_rad_flux_surface
Max value: 740.67431640625
Min value: 0.0
Average: 28.2053758189692
Std. dev.: 54.77719372533869

Feature: vegetation_surface
Max value: 99.0
Min value: 0.0
Average: 15.446288548990092
Std. dev.: 24.53112388808062

Feature: vegitation_type_as_in_sib_surface
Max value: 19.0
Min value: 0.0
Average: 3.4795825742782363
Std. dev.: 5.111687219984822

Feature: visibility_surface
Max value: 24307.435546875
Min value: 17.29292869567871
Average: 21715.863747614734
Std. dev.: 6142.599331655297

Feature: water_equiv_of_accum_snow_depth_surface
Max value: 5649.0
Min value: 0.0
Average: 8.035800387291186
Std. dev.: 37.34503968059726

Feature: wilting_point_surface
Max value: 0.13499999046325684
Min value: 0.0
Average: 0.03110594852291435
Std. dev.: 0.037380484131604996
```

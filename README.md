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
|January|[57.48|
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

### A Year of Travel

### Hottest Temperature

## Statistics for each feature

```python
df = rdd.toDF()
cols = df.columns

#df.select(df.columns[0]).show()

for col in sorted(cols[2:]):
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
Max value: 76.0
Min value: 6.0
Average: 18.07
Std. dev.: 17.4802948221907

Feature: categorical_freezing_rain_yes1_no0_surface
Max value: 0.0
Min value: 0.0
Average: 0.0
Std. dev.: 0.0

Feature: categorical_ice_pellets_yes1_no0_surface
Max value: 0.0
Min value: 0.0
Average: 0.0
Std. dev.: 0.0

Feature: categorical_rain_yes1_no0_surface
Max value: 1.0
Min value: 0.0
Average: 0.09
Std. dev.: 0.2876234912646613

Feature: categorical_snow_yes1_no0_surface
Max value: 1.0
Min value: 0.0
Average: 0.06
Std. dev.: 0.23868325657594203

Feature: convective_available_potential_energy_surface
Max value: 2620.0
Min value: 0.0
Average: 207.0
Std. dev.: 486.30019410635526

Feature: convective_inhibition_surface
Max value: -0.65234375
Min value: -202.65234375
Average: -8.87234375
Std. dev.: 30.74153574891828

Feature: direct_evaporation_cease_soil_moisture_surface
Max value: 0.13499999046325684
Min value: 0.0
Average: 0.029712499007582664
Std. dev.: 0.03685379752217062

Feature: downward_long_wave_rad_flux_surface
Max value: 431.0912780761719
Min value: 141.09127807617188
Average: 321.9587780761719
Std. dev.: 62.296988016348685

Feature: downward_short_wave_rad_flux_surface
Max value: 664.0
Min value: 0.0
Average: 131.38625
Std. dev.: 174.9622507039776

Feature: drag_coefficient_surface
Max value: 0.0
Min value: 0.0
Average: 0.0
Std. dev.: 0.0

Feature: friction_velocity_surface
Max value: 0.8758659958839417
Min value: 0.02586597390472889
Average: 0.3311159858293831
Std. dev.: 0.2278106005123383

Feature: geopotential_height_cloud_base
Max value: 9865.5
Min value: -5000.0
Average: 26.565
Std. dev.: 3795.930430953841

Feature: geopotential_height_lltw
Max value: 4459.78125
Min value: -3469.21875
Average: 1660.09625
Std. dev.: 1842.4165258766086

Feature: geopotential_height_pblri
Max value: 1938.927734375
Min value: 22.67779541015625
Average: 534.6852838134765
Std. dev.: 528.5572856381282

Feature: geopotential_height_surface
Max value: 2258.570068359375
Min value: 0.0700225830078125
Average: 200.59002151489258
Std. dev.: 400.94056402556885

Feature: geopotential_height_zerodegc_isotherm
Max value: 5460.0
Min value: 0.0
Average: 2742.6
Std. dev.: 1816.0199682967489

Feature: ice_cover_ice1_no_ice0_surface
Max value: 1.0
Min value: 0.0
Average: 0.05
Std. dev.: 0.2190429135575903

Feature: land_cover_land1_sea0_surface
Max value: 1.0
Min value: 0.0
Average: 0.46
Std. dev.: 0.5009082659620331

Feature: latent_heat_net_flux_surface
Max value: 297.59210205078125
Min value: -53.90791320800781
Average: 47.75708709716797
Std. dev.: 61.78915286896088

Feature: lightning_surface
Max value: 1.0
Min value: 0.0
Average: 0.01
Std. dev.: 0.09999999999999998

Feature: maximumcomposite_radar_reflectivity_entire_atmosphere
Max value: 40.0
Min value: -20.0
Average: -5.8725
Std. dev.: 17.818192914472938

Feature: mean_sea_level_pressure_nam_model_reduction_msl
Max value: 102788.0
Min value: 98520.0
Average: 101349.11
Std. dev.: 777.2117594908809

Feature: number_of_soil_layers_in_root_zone_surface
Max value: 4.0
Min value: 0.0
Average: 1.58
Std. dev.: 1.7533805731624366

Feature: planetary_boundary_layer_height_surface
Max value: 5276.5
Min value: 74.5
Average: 1645.69
Std. dev.: 1213.3549797852634

Feature: plant_canopy_surface_water_surface
Max value: 0.5
Min value: 0.0
Average: 0.08507499887607992
Std. dev.: 0.17806105288972154

Feature: precipitable_water_entire_atmosphere
Max value: 44.58281326293945
Min value: 1.0828148126602173
Average: 17.945314816236497
Std. dev.: 11.404169176281634

Feature: pressure_maximum_wind
Max value: 39926.734375
Min value: 11126.736328125
Average: 20100.73623046875
Std. dev.: 6545.977306919039

Feature: pressure_reduced_to_msl_msl
Max value: 102788.0
Min value: 98514.0
Average: 101362.48
Std. dev.: 781.0997618613126

Feature: pressure_surface
Max value: 102787.0
Min value: 78016.0
Average: 99046.38
Std. dev.: 4558.024806532945

Feature: pressure_tropopause
Max value: 33382.23828125
Min value: 9182.23828125
Average: 19710.23828125
Std. dev.: 6883.475748765181

Feature: relative_humidity_zerodegc_isotherm
Max value: 100.0
Min value: 1.0
Average: 53.53
Std. dev.: 32.77639425260228

Feature: sensible_heat_net_flux_surface
Max value: 236.67236328125
Min value: -57.07763671875
Average: 11.14736328125
Std. dev.: 44.21273683549627

Feature: snow_cover_surface
Max value: 100.0
Min value: 0.0
Average: 25.0
Std. dev.: 43.51941398892446

Feature: snow_depth_surface
Max value: 2.128000020980835
Min value: 0.0
Average: 0.09450799790618475
Std. dev.: 0.2866969536458589

Feature: soil_porosity_surface
Max value: 0.5
Min value: 0.0
Average: 0.23
Std. dev.: 0.25045413298101654

Feature: soil_type_as_in_zobler_surface
Max value: 16.0
Min value: 0.0
Average: 2.25
Std. dev.: 3.1634752658390988

Feature: surface_roughness_surface
Max value: 2.7500159740448
Min value: 1.5900002836133353e-05
Average: 0.4992659015478057
Std. dev.: 0.846565071035368

Feature: surface_wind_gust_surface
Max value: 22.908788681030273
Min value: 0.6587895154953003
Average: 7.128789564371109
Std. dev.: 4.654106350419142

Feature: temperature_surface
Max value: 306.4980163574219
Min value: 247.49801635742188
Average: 284.9017663574219
Std. dev.: 13.002025568205235

Feature: temperature_tropopause
Max value: 227.60687255859375
Min value: 193.23187255859375
Average: 210.80562255859374
Std. dev.: 8.212131773796742

Feature: total_cloud_cover_entire_atmosphere
Max value: 100.0
Min value: 0.0
Average: 57.96
Std. dev.: 45.57509509512067

Feature: upward_long_wave_rad_flux_surface
Max value: 499.9310302734375
Min value: 212.93104553222656
Average: 371.75728118896484
Std. dev.: 62.29572689430119

Feature: upward_short_wave_rad_flux_surface
Max value: 101.0
Min value: 0.0
Average: 17.8025
Std. dev.: 22.273021655960125

Feature: vegetation_surface
Max value: 67.0
Min value: 0.0
Average: 9.585
Std. dev.: 16.550817825928444

Feature: vegitation_type_as_in_sib_surface
Max value: 18.0
Min value: 0.0
Average: 3.5
Std. dev.: 5.254146991287987

Feature: visibility_surface
Max value: 24221.587890625
Min value: 21.588850021362305
Average: 20941.58804655075
Std. dev.: 7445.64104615157

Feature: water_equiv_of_accum_snow_depth_surface
Max value: 1321.0
Min value: 0.0
Average: 29.28
Std. dev.: 137.3906970517423

Feature: wilting_point_surface
Max value: 0.13499999046325684
Min value: 0.0
Average: 0.029712499007582664
Std. dev.: 0.03685379752217062
```

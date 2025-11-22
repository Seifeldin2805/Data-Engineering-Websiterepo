# Dataset Structure Reference

This document describes the expected structure of the `data/df_merged_clean.csv` file.

## Required Columns

### Location Information
- `BOROUGH`: NYC Borough name (BROOKLYN, MANHATTAN, QUEENS, BRONX, STATEN ISLAND)
- `ZIP_CODE`: ZIP code (numeric or string)
- `LATITUDE`: Latitude coordinate (decimal, NYC area ~40.7)
- `LONGITUDE`: Longitude coordinate (decimal, NYC area ~-74.0)
- `ON_STREET_NAME`: Primary street name
- `CROSS_STREET_NAME`: Cross street name
- `OFF_STREET_NAME`: Off-street location name

### Date/Time Information
- `CRASH_DATE`: Date of crash (YYYY-MM-DD format)
- `CRASH_TIME`: Time of crash (HH:MM format)
- `CRASH_DATETIME`: Combined date-time (optional but recommended)
- `CRASH_YEAR`: Year (integer, e.g., 2022)
- `CRASH_MONTH`: Month (integer 1-12 or month name)
- `CRASH_DAY`: Day of month (integer 1-31)
- `CRASH_WEEKDAY`: Day of week (Monday, Tuesday, etc.)
- `CRASH_HOUR`: Hour of day (integer 0-23)
- `IS_WEEKEND`: Boolean (0/1 or True/False)

### Injury/Fatality Counts
- `NUMBER_OF_PERSONS_INJURED`: Total persons injured (integer)
- `NUMBER_OF_PERSONS_KILLED`: Total persons killed (integer)
- `NUMBER_OF_PEDESTRIANS_INJURED`: Pedestrians injured (integer)
- `NUMBER_OF_PEDESTRIANS_KILLED`: Pedestrians killed (integer)
- `NUMBER_OF_CYCLIST_INJURED`: Cyclists injured (integer)
- `NUMBER_OF_CYCLIST_KILLED`: Cyclists killed (integer)
- `NUMBER_OF_MOTORIST_INJURED`: Motorists injured (integer)
- `NUMBER_OF_MOTORIST_KILLED`: Motorists killed (integer)
- `TOTAL_INJURED`: Sum of all injuries (integer, optional - will be calculated)
- `TOTAL_KILLED`: Sum of all fatalities (integer, optional - will be calculated)

### Contributing Factors
- `CONTRIBUTING_FACTOR_VEHICLE_1`: Primary contributing factor
- `CONTRIBUTING_FACTOR_VEHICLE_2`: Secondary contributing factor
- Common values: "Unsafe Speed", "Alcohol Involvement", "Driver Inattention/Distraction", etc.

### Vehicle Information
- `VEHICLE_TYPE_CODE_1`: Primary vehicle type
- `VEHICLE_TYPE_CODE_2`: Secondary vehicle type
- Common values: "SEDAN", "SUV", "TRUCK", "MOTORCYCLE", "BICYCLE", "BUS", etc.

### Person Information (if merged)
- `TOTAL_PERSONS`: Total persons involved
- `AVG_PERSON_AGE`: Average age of persons
- `FEMALE_PERSONS`: Count of female persons
- `MALE_PERSONS`: Count of male persons
- `UNKNOWN_SEX`: Count of persons with unknown sex

### Identifiers
- `COLLISION_ID`: Unique collision identifier
- `LOCATION`: Location description (optional)

## Data Quality Requirements

1. **Numeric Columns**: Should be numeric type (integers for counts, floats for coordinates)
2. **Missing Values**: Null/NaN values are handled, but numeric columns should use 0 for counts
3. **Geographic Coordinates**: Should be valid NYC area coordinates:
   - Latitude: approximately 40.5 to 40.9
   - Longitude: approximately -74.3 to -73.7
4. **Dates**: Should be in consistent format (YYYY-MM-DD recommended)
5. **Years**: Should be 4-digit integers (e.g., 2022)

## Example Row

```csv
CRASH_DATE,CRASH_TIME,BOROUGH,ZIP_CODE,LATITUDE,LONGITUDE,NUMBER_OF_PERSONS_INJURED,NUMBER_OF_PERSONS_KILLED,CONTRIBUTING_FACTOR_VEHICLE_1,VEHICLE_TYPE_CODE_1,CRASH_YEAR,CRASH_MONTH,CRASH_HOUR,CRASH_WEEKDAY,TOTAL_INJURED,TOTAL_KILLED
2022-01-15,14:30,BROOKLYN,11201,40.6942,-73.9902,2,0,Unsafe Speed,SEDAN,2022,1,14,Monday,2,0
```

## Data Sources

This structure is based on the NYC Open Data:
- Motor Vehicle Collisions - Crashes: https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95
- Motor Vehicle Collisions - Persons: https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Persons/f55k-p6yu

The application expects these datasets to be merged and cleaned before use.


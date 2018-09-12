from classes import *

print('Script for changing the time zone')
my_raw_id = input('What is the raw id?')
try:
    assert len(my_raw_id) == 6
except AssertionError as e:
    my_raw_id = input('Raw_id must be 6 characters long!')
assert len(my_raw_id) == 6
new_zone = input('What is the new time zone?')
new_zone = int(new_zone)
soc_db = SocMediaDB()
soc_db.change_time_zone(raw_id=my_raw_id, new_zone=new_zone)

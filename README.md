# Django seed data generator

This project focuses on creating seed data for all manually created django models. This project as of now supports basic data types including charfield, boolean, emailfield, datetime, textfield and foreign keys. The version 1.0.0 is made to support basic django datatypes. Upcoming versions of this project will handle other complex datatypes including manytomany field, content types and file/image field. This project handles integrity constraints while populating seed data to the database.

## Using crud generator
---
1. Create a python app and register it in settings.py
```
python manage.py startapp <app_name>
```
2. Create models inside that app.
3. Inside python shell run below command,
```
python manage.py generate_seed
```
[Note:
 
i)Many to many and content type fields will be empty in v1.0.0 but if there is an intermediate table for many to many field, then that table shall be populated.

## Contributing
---
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.


## License
---
[MIT](https://choosealicense.com/licenses/mit/)
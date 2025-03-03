# SanicAPI
Test task for DimaTech company


### Environmental variables
+ **SANIC_SECRET** - value used for cryptographic purposes
+ **HOST** defines host to be used; defaults to localhost
+ **POSTGRES_DB** defines name of PostgreSQL database
+ **POSTGRES_PASSWORD** 
+ **POSTGRES_USER** 

Test default admin user can be created by running "models.py" located in /database from bash

Assuming you are in base directory:
```bash
cd src/database
python models.py
```
This will create an admin user with email "admin@example.com" and password "admin"

### Authentication notes
JWT is chosen as a authentication backend; 

user's email is chosen as a value for "sub" parameter of JWT payload



### Endpoint documentation
Endpoints are splitted into three [blueprints](https://sanic.dev/en/guide/best-practices/blueprints.html):
+ **auth**, handling only login
+ **main**, handling main user functionality
+ **admin_bp**, handling admin functionality

##### admin_bp
+ create_user(request) - accepts json object with required fields "password" and "email";
    optional are "full_name" and "is_admin"
    if data is valid, creates new user and returns information about it in
    json format
+ UserManipulationView.put(request, id: int) - accpets json-object, where looks only for 
    following "checkup fields" - "password", "full_name", "email", "is_admin"; other keys of json-object
    will be ignored. Sent JSON must contain at least one of "checkup fields"; if all checkup fields 
    provided contain valid value, user on given id will be updated   
    
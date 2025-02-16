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
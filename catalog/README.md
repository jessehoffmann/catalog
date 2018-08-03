# Catalog Project
This web application was designed as a generic website for catalogs. The program demonstrates frontend and backend (including databases and api calls) skills.
Once set up on the users computer it can be used to store category and item information.

## Requirements
You need Python installed on your OS to execute the program. Any version after 2.7 will do.

Installation packages can be found here:
https://www.python.org/getit/

You will also need to download virtual machine and vagrant, which will provide you the PostgreSQL database as well as an environment to run the project in. These two pieces of software can be downloaded here:
https://www.virtualbox.org/wiki/Download_Old_Builds_5_2
https://www.vagrantup.com/

## Deployment
To run the program execute the following from within the Catalog Project directory in the shell:
```
vagrant up
```
followed by
```
vagrant ssh
```

Then navigate to the project folder. From there execute the following:
```
python catalog.py
```
followed by
```
python applocation.py
```

Finally, navigate to a web browser and enter "localhost:8000" and enjoy navigating/adding to the application.

## Credit
Some of the code from gconnect() function was copied from notes I had taken in the Udacity classroom. Credit goes to the owner.

## License
This project is public domain.

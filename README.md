# Six Degrees of Kevin Bacon

This is a relatively simple app to show the power and speed of ArangoDB 

# Requirements

1. ArangoDB Database -  Please see https://arango.ai/ for different ways (e.g. Docker) to get access to an Arango DB system.  This also uses the ArangoDB client tools where are different to install on weather you are using Windows / Linux / Docker. 

2. Python - This is tested with the latest version of Python (3.14.7). But should work with most versions of Python3

# Setup 
In the setup directory there are a number of shell scripts to download CSV/TSV files from IMDB, and then parse these and upload to your ArangoDB Server. 

There is an example file /setup/arango.env.example  - add your information and rename to arango.env

I do not 100% guarantee this will work so you may need to tweak things based on your environmnent. 

The required python libraries are in the /setup/requirements.txt file

# Contributing

Please make any suggestions for interesting updates to the system
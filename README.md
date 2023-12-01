# merakiClientBalancingChecker
Checks which RF Profiles in your organization have Client Balancing enabled and optionally updates them to disable Client Balancing.

How to use:
* Add your details to `config.py`
* Run with `python main.py`
* As the code runs, it will first output a list of sites and RF profiles with Client Balancing enabled (templates will be separate from non-template networks)
* It will then ask you if you want to proceed and disable Client Balancing in those profiles, which you should answer with Y or N via keyboard input
* Regardless of what you do, it will output a .csv file with the list of sites and profiles with the feature enabled

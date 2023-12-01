import meraki
import pandas as pd
import config
import sys
from tabulate import tabulate

def print_tabulate(data):
    df = pd.DataFrame(data)
    print(tabulate(df, headers='keys', tablefmt='fancy_grid'))

dashboard = meraki.DashboardAPI(config.api_key, maximum_retries=5)

orgs = dashboard.organizations.getOrganizations()

for org in orgs:
    if org['name']==config.organization_name:
        org_id = org['id']

nets = dashboard.organizations.getOrganizationNetworks(org_id)
templates = dashboard.organizations.getOrganizationConfigTemplates(org_id)

check_networks = []

for temp in templates:
    if 'wireless' in temp['productTypes']:
        try:
            rf_profiles = dashboard.wireless.getNetworkWirelessRfProfiles(temp['id'])
            for rf_profile in rf_profiles:
                if rf_profile['clientBalancingEnabled']==True:
                    rf_profile['temp_id']=temp['id']
                    rf_profile['temp_name']=temp['name']
                    check_networks.append(rf_profile)
        except meraki.APIError as e:
            print(temp['id'], temp['name'], e)
            check_networks.append({"temp_id": temp['id'], "temp_name": temp['name'], "error": e})

for net in nets:
    if net['isBoundToConfigTemplate'] == False:
        if 'wireless' in net['productTypes']:
            try:
                rf_profiles = dashboard.wireless.getNetworkWirelessRfProfiles(net['id'])
                for rf_profile in rf_profiles:
                    if rf_profile['clientBalancingEnabled'] == True:
                        rf_profile['net_id'] = net['id']
                        rf_profile['net_name'] = net['name']
                        check_networks.append(rf_profile)
            except meraki.APIError as e:
                print(net['id'], net['name'], e)
                check_networks.append({"net_id": net['id'], "net_name": net['name'], "error": e})

check_networks_df = pd.DataFrame(check_networks)
check_networks_df.to_csv(f'client_balancing_check_{config.organization_name}.csv')

print("These are the RF Profiles in this organization with Client Balancing enabled: ")
print_tabulate(check_networks_df)

choice = str(input("Would you like to update these RF profiles to disable client balancing? (Y/N): "))
if choice == 'Y':
    for net in check_networks:
        if 'temp_id' in net.keys():
            # If you send the name parameter to one of the default profiles, you will get an API error
            if net['isIndoorDefault']==True or net['isOutdoorDefault']==True:
                upd = {k: net[k] for k in net.keys() - {'temp_id', 'temp_name', 'networkId', 'id', 'name'}}
            else:
                upd = {k: net[k] for k in net.keys() - {'temp_id', 'temp_name', 'networkId', 'id'}}
        elif 'net_id' in net.keys():
            # If you send the name parameter to one of the default profiles, you will get an API error
            if net['isIndoorDefault']==True or net['isOutdoorDefault']==True:
                upd = {k: net[k] for k in net.keys() - {'net_id', 'net_name', 'networkId', 'id', 'name'}}
            else:
                upd = {k: net[k] for k in net.keys() - {'net_id', 'net_name', 'networkId', 'id'}}
        # The API will throw an error if you try to set the 2.4GHz auto channels to something different from 1,6,11
        if upd['twoFourGhzSettings']['validAutoChannels']!=[1,6,11]:
            upd['twoFourGhzSettings']['validAutoChannels']=[1,6,11]
        # The API will throw an error if you try to update valid 5GHz auto channels to something that includes
        # 169, 173 and 177
        if (169 or 173 or 177) in upd['fiveGhzSettings']['validAutoChannels']:
            upd['fiveGhzSettings']['validAutoChannels'] = [
                channel for channel in upd['fiveGhzSettings']['validAutoChannels'] if channel not in [169, 173, 177]
            ]
        upd['clientBalancingEnabled']=False
        try:
            dashboard.wireless.updateNetworkWirelessRfProfile(networkId=net['networkId'], rfProfileId=net['id'], **upd)
        except meraki.APIError as e:
            print(net['id'], net['networkId'], e)
elif choice == 'N':
    sys.exit()
else:
    sys.exit()
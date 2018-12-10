#!/usr/bin/env python

import json
import subprocess

all_hz_json = "all_hz.json"
all_hz_tsv = "all_hz.tsv"
all_rrs_a_cname_tsv = "all_rrs_a_cname.tsv"

# This will use AWS SDK CLI to get all the Hosted Zones, HZ, and their info into a json file.
with open(all_hz_json, "w") as hzoutputfile:
    subprocess.call(['aws', 'route53', 'list-hosted-zones'], stdout=hzoutputfile, stderr=hzoutputfile)

fh = open(all_hz_json, "r")
data = json.loads(fh.read())

#print(len(data['HostedZones']))

# Parse the data in the HZ json file.
for hzones in data['HostedZones']:
    rrs_count = hzones['ResourceRecordSetCount']
    hz_id = hzones['Id']
    hz_name = hzones['Name']
    hz_config = hzones['Config']
    hz_privatezone = hzones['Config']['PrivateZone']
    if 'Comment' in hz_config:
        hz_comment = hz_config['Comment']
    else:
        hz_comment = ''
    hz_pub_priv = 'EXTERNAL'
    if hz_privatezone == True:
        hz_pub_priv = 'INTERNAL'


# This just creates an easier to read tsv file with all the hosted zones listed - for posterity, heh.
    with open(all_hz_tsv, "a") as ahzt:
        ahzt.write("{}\t{}\t{}\t{}\t{}\n".format(hz_name, hz_privatezone, hz_id, rrs_count, hz_comment))


# For each hosted zone, extract all the resource record sets (rrs) into individual files, one per HZ.
    hz_file_name = "{}_rrs_{}.json".format(hz_name , hz_pub_priv)
    with open("%s" % hz_file_name, "w") as rrsoutputfile:
        subprocess.call(['aws', 'route53', 'list-resource-record-sets', '--hosted-zone-id', str(hz_id)], stdout=rrsoutputfile, stderr=rrsoutputfile)


# For each HZ rrs file, find the A and CNAME record values for each (but not other record types).
    with open(hz_file_name, "r") as hzrrs:
        data = json.loads(hzrrs.read())
        for dnsstuff in data['ResourceRecordSets']:
            record_type = dnsstuff['Type']
            record_name = dnsstuff['Name']
            hostedzoneid = ''
            is_alias = ''

            with open("%s" % all_rrs_a_cname_tsv, "a") as rrsout_tsv:

                if record_type == 'CNAME':
                    if 'AliasTarget' in dnsstuff:
                        is_alias = 'ALIAS'
                        alias_target = dnsstuff['AliasTarget']
                        hostedzoneid = alias_target['HostedZoneId']
                        value = alias_target['DNSName']
                    else:
                        resource_recs = dnsstuff['ResourceRecords']
                        for cname_records in resource_recs:
                            value = cname_records['Value']
                    print("{}\t{}\t{}\t{}\t{}\t{}".format(hz_name, hz_pub_priv, record_type, record_name, is_alias, value))
                    rrsout_tsv.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(hz_name, hz_pub_priv, record_type, record_name, is_alias, value))
                elif record_type == 'A':
                    if 'AliasTarget' in dnsstuff:
                        is_alias = 'ALIAS'
                        alias_target = dnsstuff['AliasTarget']
                        hostedzoneid = alias_target['HostedZoneId']
                        value = alias_target['DNSName']
                    else:
                        resource_recs = dnsstuff['ResourceRecords']
                        for a_record in resource_recs:
                            value = a_record['Value']
                    print("{}\t{}\t{}\t{}\t{}\t{}".format(hz_name, hz_pub_priv, record_type, record_name, is_alias, value))
                    rrsout_tsv.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(hz_name, hz_pub_priv, record_type, record_name, is_alias, value))

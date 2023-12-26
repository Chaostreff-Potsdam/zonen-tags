#! /bin/bash

# check if number of arguments is less then 3
if [ $# -lt 3 ]
then
    echo "Usage: $0 <ipv4> <ipv6> <key>"
    exit 1
fi

# echo "updating nametag.d.ccc-p.org to $1 und $2"
# https://d.ccc-p.org/records/update?domain=nametag.d.ccc-p.org&key=$3&a=$1&aaaa=$2

echo "updating zonen-tags.d.ccc-p.org to $1 und $2"
curl "https://d.ccc-p.org/records/update?domain=zonen-tags.d.ccc-p.org&key=$3&a=$1&aaaa=$2"
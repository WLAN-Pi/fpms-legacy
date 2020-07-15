#!/bin/bash

#Displays IP address, subnet mask, default gateway, DNS servers, speed, duplex, DHCP server IP address and name 

#NetworkManager uses this location - WLAN Pi v1.x used /var/lib/dhcp/dhclient.eth0.leases
ETH0UUID=$(nmcli -f DEVICE,UUID connection show | grep "eth0" | cut -d" " -f5)
ETH0UUIDLENGTH=$(echo "$ETH0UUID" | wc -l)
if [ "$ETH0UUIDLENGTH" == "1" ]; then
    #In this case NetworkManager was actually used to request IP address from DHCP server 
    ETH0LEASES="/var/lib/NetworkManager/dhclient-"$ETH0UUID"-eth0.lease"
else
    #NetworkManager is not running properly for eth0, falling back to /etc/network/interfaces configuration, check that all references to eth0 in /etc/network/interfaces are removed and that NetworkManager services started
    ETH0LEASES="/var/lib/dhcp/dhclient.eth0.leases"
fi

ACTIVEIP=$(ip a | grep "eth0" | grep "inet" | grep -v "secondary" | cut -d '/' -f1 | cut -d ' ' -f6)
SUBNET=$(ip a | grep "eth0" | grep "inet" | cut -d ' ' -f6 | tail -c 4)

LEASEDIPISUSED=$(grep "$ACTIVEIP" "$ETH0LEASES")

ETH0ISUP=$(/sbin/ifconfig eth0 | grep "RUNNING")

#Not used by NetworkManager
#DHCPENABLED=$(grep -i "eth0" /etc/network/interfaces | grep "dhcp" | grep -v "#")

DHCPSRVNAME=$(grep -A 13 'interface "eth0"' "$ETH0LEASES" | tail -13 | grep -B 1 -A 10 "$ACTIVEIP" | grep "server-name" | cut -d '"' -f2)
DHCPSRVADDR=$(grep -A 13 'interface "eth0"' "$ETH0LEASES" | tail -13 | grep -B 1 -A 10 "$ACTIVEIP" | grep "dhcp-server-identifier" | grep -E -o "([0-9]{1,3}[\.]){3}[0-9]{1,3}")
DOMAINNAME=$(grep -A 13 'interface "eth0"' "$ETH0LEASES" | tail -13 | grep -B 1 -A 10 "$ACTIVEIP" | grep "domain-name " | cut -d '"' -f2)
DEFAULTGW=$(/sbin/route -n | grep G | grep eth0 | cut -d ' ' -f 10)
SPEED=$(ethtool eth0 | grep -q "Link detected: yes" && ethtool eth0 | grep "Speed" | sed 's/....$//' | cut -d ' ' -f2  || echo "Disconnected")
DUPLEX=$(ethtool eth0 | grep -q "Link detected: yes" && ethtool eth0 | grep "Duplex" | cut -d ' ' -f 2 || echo "Disconnected")
DNSSERVERS=$(grep "nameserver" /etc/resolv.conf | sed 's/nameserver/DNS:/g')

if [ "$ETH0ISUP" ]; then
    #IP address
    echo "IP: $ACTIVEIP"

    #Subnet
    echo "Subnet: $SUBNET"

    #Default gateway
    echo "DG: $DEFAULTGW"

    #DNS servers
    echo "$DNSSERVERS"

    #DHCP server info
    if [[ "$LEASEDIPISUSED" ]] && [[ "$ACTIVEIP" ]]; then
        if [[ "$DHCPSRVNAME" ]] && [[ "$LEASEDIPISUSED" ]]; then
            echo "DHCP server name: $DHCPSRVNAME"
        fi
        if [[ "$DHCPSRVADDR" ]] && [[ "$LEASEDIPISUSED" ]] && [[ "$ACTIVEIP" ]]; then
            echo "DHCP server address: $DHCPSRVADDR"
        fi
        if [[ "$DOMAINNAME" ]] && [[ "$LEASEDIPISUSED" ]] && [[ "$ACTIVEIP" ]]; then
            echo "Domain: $DOMAINNAME"
        fi
    else
        echo "No DHCP server used"
    fi

    #Speed
    echo "Speed: $SPEED"

    #Duplex
    echo "Duplex: $DUPLEX"

else
    echo "eth0 is down"
fi


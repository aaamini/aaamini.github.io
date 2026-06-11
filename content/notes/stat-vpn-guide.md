---
title: 'How to connect to the UCLA Statistics VPN'
date: 2020-06-08
---
It is hard to connect from an **[Arach Linux](https://archlinux.org/)** machine to the VPN provided by UCLA Statistics. We assume that you have **Gnome** and **NetworkManager** installed. 
Even then, you have to push the right buttons, and here are those buttons (as of the writing of this post):

1. Intsall `networkmanger-l2tp` and `libreswan` packages in Arch Linux.
1. Go to **Settings \| Network** and click `+` to add a VPN network.
- Select **Layer 2 Tunneling Protocol (L2TP)**
3. Name the network however you like.
4. Enter `vpn.stat.ucla.edu` for the **Gateway**.
5. Under **User Authentication**, leave the type as **Password** and enter your Stat. UCLA username and password. (God knows what these are, but the staff can help.) 
6. Leave the checkbox **Use L2TP ephemeral source port** unchecked.
7. Click on the **IPSec Settings** button:
    * Enter `3des-sha1-modp1024` for the Phase1 Algorithms.
    * Enter `3des-sha1` for the Phase2 Algorithms.
8. Click on the **PPP settings** button:
    * Only check `MSCHAPv2` for the authentication.
9. You may still not be able to connect. (You didn't think it was that easy, did you?) Then,
    * Disable `PFS` in IPSec settings (PFS stands for Perfect Forward Secrecy).

This guide may also work for other Linux distributions. 

DISCLAIMER: This guide is provided for **purely educational** purposes. I take no responsibility for any consequences the may result from following these instructions.

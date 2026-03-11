# Router Bootstrap Protocol

## Purpose

Bootstrap allows a new MikroTik router to automatically connect to the controller and request adoption.

This process is similar to the UniFi adoption model.

---

# Bootstrap Methods

Manual bootstrap  
Script bootstrap  
VPN bootstrap

---

# Script Bootstrap

Technician runs a script on the router.

Example:

/system script add name=bootstrap source="controller-register"

/tool fetch url=https://controller/register

The router sends:

identity  
routeros version  
interfaces  
public IP

---

# Registration Flow

Router → Controller

POST /register

Payload example:

{
  "hostname": "router-branch1",
  "routeros_version": "7.12",
  "architecture": "arm",
  "interfaces": ["ether1","ether2"]
}

---

# Controller Response

Controller marks device:

pending_adoption

Operator approves adoption.

Device state changes to:

managed

---

# VPN Bootstrap

Router automatically creates a WireGuard tunnel to the controller.

Once connected:

Controller detects device via tunnel.

---

# Security Requirements

Bootstrap tokens must be used.

Token example:

bootstrap_token

Tokens expire after configurable period.

---

# Bootstrap Steps

1 Router installed  
2 Bootstrap script executed  
3 Router contacts controller  
4 Device appears in pending_adoption  
5 Operator approves device  
6 Controller pushes configuration template

# Device Adoption Specification

## Purpose

The adoption system allows routers to be registered and managed by the controller.

## Adoption Lifecycle

discovered  
→ pending_adoption  
→ approved  
→ managed  

Possible rejection path:

pending_adoption  
→ rejected  

## Adoption Modes

### Manual adoption

Operator registers device using:

IP  
credentials  
tenant  
site  

Controller verifies connectivity.

### Script bootstrap

Technician installs bootstrap script on router.

Router registers itself to controller.

Controller marks device as:

pending_adoption

Operator approves adoption.

### VPN bootstrap

Router establishes VPN tunnel to controller.

Controller discovers device through VPN.

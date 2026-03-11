# Template Engine Specification

## Purpose

Templates define configuration policies applied to routers.

## Template Types

### Declarative templates

Example

interfaces:
  ether1:
    comment: WAN
    disabled: false

### Script templates

Example

/ip firewall filter add chain=input action=accept protocol=icmp

## Execution Modes

dry-run  
apply  
audit-only  
enforce  

## Template Versioning

Fields:

template_id  
version  
content  
created_at  
created_by

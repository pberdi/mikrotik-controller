# MikroTik Connector Specification

## Purpose

The connector provides a compatibility abstraction layer for RouterOS devices.

## Supported Versions

RouterOS 6.x  
RouterOS 7.x  

## Communication Protocol

Primary protocol:

API-SSL  
TCP 8729  

Fallback:

SSH  

## Responsibilities

Establish secure connection  
Execute commands  
Normalize responses  
Detect device capabilities  

## Core Functions

get_system_inventory()  
list_interfaces()  
backup_export()  
backup_binary()  
run_command()  
apply_template()

# Job Engine Specification

All remote operations must run as asynchronous jobs.

## Job Types

inventory collection  
backup  
template apply  
command execution  
health check  

## Job States

pending  
running  
success  
failed  
retrying  
cancelled  

## Scheduling

Jobs may run:

manually  
scheduled  
event-triggered

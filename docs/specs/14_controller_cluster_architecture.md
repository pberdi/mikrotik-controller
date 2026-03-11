# Controller Cluster Architecture

## Purpose

The MikroTik Controller must support horizontal scaling to manage thousands of routers.

The architecture must support:

multi-controller clusters  
worker pools  
stateless API nodes  
shared job queue  

---

# Cluster Components

API Nodes

Stateless FastAPI servers.

Responsibilities:

authentication  
API endpoints  
tenant logic  

---

Worker Nodes

Execute asynchronous tasks.

Examples:

inventory polling  
backup execution  
template deployment  
command execution  

---

Redis Queue

Central job queue.

Used by Celery workers.

---

PostgreSQL Database

Stores persistent data.

Shared by all nodes.

---

Backup Storage

Object storage or filesystem cluster.

Stores:

device backups  
template artifacts  

---

# Cluster Topology

Users  
→ Load Balancer  
→ API Nodes  

API Nodes  
→ Redis Queue  

Worker Nodes  
→ Redis Queue  

Workers  
→ MikroTik Connector  

Connector  
→ RouterOS Devices

---

# Horizontal Scaling

API nodes can scale horizontally.

Worker nodes can scale independently.

Example deployment:

2 API nodes  
4 worker nodes  

---

# Future scaling targets

10000+ routers  
100+ concurrent workers

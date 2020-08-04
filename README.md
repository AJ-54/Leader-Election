# Leader-Election using etcd 

## What is etcd ?

etcd is a strongly consistent, distributed key-value store that provides a reliable way to store data that needs to be accessed by a distributed system or cluster of machines.

## What is technical overview of etcd ?

  * etcd is written in Go, which has excellent cross-platform support, small binaries and a great community behind it. 
  * Communication between etcd machines is handled via the Raft consensus algorithm.

## How I used with python ?

I used the python client for the API v3 [link](https://python-etcd3.readthedocs.io/en/latest/readme.html). 

## What exactly I did ?

  * Each candidate leader attempts to set a common key using a transaction that checks if the key already exists.
  * If not, the candidate leader sets the key with a lease and assumes the leader role.
  * The leader can then do its work, meanwhile refreshing the lease.
  * Should the lease lapse, because the leader fails or revokes the lease, a new election is triggered and one of the followers will become leader.
  * I created multiple terminals as servers and keyboard interruptions as a measure to revoke the lease. Once the lease is revoked, all keys associated with the lease dies out.
  * The followers actively watch the event and as the key is deleted, the event triggers and new election is conducted.
  

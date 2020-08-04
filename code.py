import etcd3
import sys
import time
from threading import Event

# The current leader is going to be the value with this key.
LEADER_KEY = "/ayush-demo/leader"

# Entrypoint of the program
def main(server_name):
    # Create a new client to etcd.
    print(server_name)
    client = etcd3.client(host="localhost",port=2379)

    while True:
        is_leader, lease = leader_election(client,server_name)

        if (is_leader):
            print("I am the leader.")
            on_leadership_gained(lease)
        
        else:
            print("I am a follower.")
            wait_for_next_election(client)

# This election mechanism consists of all clients trying to put 
# their name into a single key. But in a way that only works if 
# the key does not exist (or has expired before).

def leader_election(client, server_name):
    print("New leader election happening.")
    # Create a lease before creating a key. This way, if this client
    # ever lets the lease expire, the keys associated with that lease
    # will all expire as well.
    # Here, if the client fails to renew lease for 5 seconds
    # (network partitions or machine gets down), than the leader
    # election key will  expire
    # https://help.compose.com/docs/etcd-using-etcd3-features#selection-leases
    lease = client.lease(5)

    # Try to create the key with your name as value. If it fails, then another
    # server got their first. 
    is_leader = try_insert(client,LEADER_KEY, server_name, lease)
    return is_leader,lease

def on_leadership_gained(lease):
    while True:
        # As long as this process is alive and we are the leader,
        # we try to renew the lease. We dont give up the leadership
        # unless the process / machine crashes or some exception
        # is raised.

        try:
            print("Refreshing lease; still the leader")
            # lease.refresh()
            #  Here we can add business logic
            do_work(lease)
        
        except KeyboardInterrupt:
            print ("\nRevoking lease, no longer the leader.")
            lease.revoke()
            sys.exit(1)
        
        except Exception:
            # Here we most likely got a client timeout
            # maybe frome network issues. Try to revoke 
            # the current lease so another member can get
            # leadership.
            print("this is wrong")
            lease.revoke()
            return
        
def wait_for_next_election(client):
    election_event = Event()

    def watch_callback(resp):
        print(resp)
        for event in resp.events:
            # For each event in watch event, if the event is a deletion
            # it means the kep expired / got deleted, which means the leadership
            # is up for grasp.
            if isinstance(event, etcd3.events.DeleteEvent):
                print("LEADERSHIP CHANGE REQUIRED")
                election_event.set()
    
    watch_id = client.add_watch_callback(LEADER_KEY, watch_callback)

    # While we haven't seen that leadership needs change, just sleep.
    try:
        while not election_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        client.cancel_watch(watch_id)
        sys.exit(1)

# Try to insert a key into etcd with a value and a lease.If the lease expires
# that key will get automatically deleted behind the scenes.If that key 
# was already present this will raise an exception
def try_insert(client, key, value, lease):
    insert_succeeded, _ = client.transaction(
        failure = [],
        success = [client.transactions.put(key,value,lease)],
        compare = [client.transactions.version(key) == 0],
    )
    return insert_succeeded

def do_work(lease):
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print ("\nRevoking lease, no longer the leader.")
        lease.revoke()
        sys.exit(1)

if __name__ == "__main__":
    server_name = sys.argv[1]
    main(server_name)
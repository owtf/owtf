# Workers and the worklist

When you launch a plugin against a target, OWTF creates a unit of work for that plugin-target pair. The worklist stores queued work; workers claim and execute it.

```text
plugin launch ──► worklist ──► available worker ──► plugin execution ──► result
```

## Monitor work

Use the worklist to review:

- the target and plugin attached to each item;
- whether work is queued, running, paused, or complete;
- the estimated execution time when available; and
- the order in which available workers will claim work.

The queue is persistent. Paused work remains paused across a normal restart because its state is stored in PostgreSQL.

## Pause and resume

Pause queued work when a target becomes unavailable, the testing window closes, or the rules of engagement change. Pausing prevents a worker from claiming the item; it does not necessarily undo work already performed.

Workers can also be paused individually or as a group. Resume only after rechecking target availability and authorization.

## Abort running work

Abort a worker when a running plugin must stop. Some external tools need time to terminate and may leave partial output. Review logs and the target report before assuming an aborted process made no requests.

## Add workers

Additional workers allow more plugins to execute concurrently. More concurrency also increases CPU, memory, network traffic, and pressure on targets. Scale workers gradually and remain within agreed traffic limits.

OWTF schedules no more than one plugin per target at a time, which helps avoid conflicting changes and unbounded target load.

## Diagnose a stuck queue

1. Confirm at least one worker is active.
2. Check whether the work item or whole queue is paused.
3. Inspect backend and worker logs.
4. Verify the required external tool exists.
5. Confirm the target is reachable from the backend container.

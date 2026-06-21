# Bridge Pipeline FAQ

## What is the shared pool?

The shared pool is the set of tasks with `owner: pool`, `status: todo`, and satisfied dependencies.

## Why use claim files?

Claim files make the bridge between asynchronous agents explicit. A task is not silently owned by a chat message; it is owned by a visible lease.

## What happens after done?

The task status changes to `done`, a marker appears in `queues/done/`, and the generated pipeline snapshot should be refreshed.

# ActivityPub Minimal Core (AP Core)

## Overview

This project is the result of a thought exercise into what a minimal core set of requirements would be for ActivityPub. The idea is that with this core set of requirements and domain-specific interoperability profiles (for microblogging, media sharing, social linking, etc.), we may be able to improve the current Fediverse developer experience and reduce the frustration associated with federation.

(The following is a starting point for exploration. It will probably change significantly over time.)

The proposed AP Core requires a server to implement the following:

* The instance MUST implement at least one actor
  * The actor MUST have at least the following properties: 
    * `id`     (MUST be valid for dereferencing)
    * `type`   (MUST be a single value)
    * `inbox`  (MUST be operational, MAY be instance-level)
    * `outbox` (Required by AP, but MAY be nonoperational)
* The instance MUST implement at least one of the following behaviors:
  * Incoming activity processing
  * Activity publication
    * Must support `inbox` `Follow` activity processing

In instance MAY have a nonoperational `outbox`. However, AP requires an `outbox` property on actors. The `outbox` endpoint MAY return an HTTP status of 403 Forbidden or 501 Not Implemented (or equivalent).

An instance MAY not store any activities. An `inbox` GET MAY return an HTTP error status. 

If an actor can be followed, it MUST be available for dereferencing.

Other than `Follow` for activity publishers, an instance MAY process any subject (including none) of the Activity Streams 2.0 activities received in its `inbox`.

An AP Core instance MAY not have any authentication or authorization features.

An instance MAY choose to not do `inbox` forwarding.

## Federation Limitations

It should be clear that only implementing the AP Core will not result in an ActivityPub implementation that will federate with existing server implementation like Mastodon. For example, a partial list of additional functionality needed for federation with Mastodon includes:

* Webfinger support to convert Mastodon account identifiers to AP actor URIs
* A specific version of HTTP Signatures to sign requests.
* Special properties on actors (like `preferredUsername` and signature-related properties)

Many microblogging servers mostly mimic the Mastodon-specific features for federation purposes. The requirements beyond the AP Core should be documented in a microblogging interoperability profile that overlaps with ActivityPub but defines specific variations for this social web domain.

Similar interoperability profiles can (and should) be written for other social web domains (e.g, image sharing, forums, [insert your domain here]).

## Potential AP Core use cases

The AP Core may seem ridiculously underpowered, to the point of not being useful for anything other than the thought experiment that conceived it (without additional interoperability profiles). However, there are possible uses.

### Activity Bridges (Follow-only)

This type of instance would subscribe to an activity publisher and possible pass the activities to another process (bridging) or do some limited local processing and storage.

### Relay-like Instances (Publish-only)

A publish-only, single-actor instance could be used to bridge or generate information and publish it to subscribers. For usage in a controlled environment (like a LAN) this may be all that's required. However, for public instance, to avoid spamming it would need some type of check on the validity of `Follow` requests (maybe a same origin policy or maybe IP address-based ACLs).

## Implementations

Currently, the only implementations are in this repository and are implemented in the Python programming language. The plan is to create implementations in other programming languages as well.

The repository contains two instance implementations:,a publish-only instance and a follow-only instance. Both have a single actor. These instances can interoperate with each other.

## Installation

```bash
poetry install

# Run a publish-only instance on port 8000
# Actor: http://127.0.0.1:8000/actor
poetry run mincore publisher

# In another shell...

# Run a follow-only instance on port 8001
# Actor: http://127.0.0.1:8001/actor
# This will request to follow the publisher
poetry run mincore follower
```

Both commands will have a `--port` option if the existing ports are already allocated on your computer or if you want to run multiple publishers and/or followers.

You can also run `poetry shell` and then just run the `mincore <subcommand>` at the prompt.

The publisher will publish a `Create\Note` every five seconds to its followers. The publisher will `Accept` any `Follow` request. The followers list is not persistent and if there's an error communicating to a follower, that follower's inbox will be removed from the list.

The consumer sends a `Follow` request to the publisher and just logs the incoming activities without doing any further processing of them. 

Considering only the AP Core processing, without the exception handling boilerplate, there are about 50 lines of code total for the two instances.
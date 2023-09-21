# ActivityPub Minimal Core (AP Core)

## Overview

This project is the result of a thought exercise into what a minimal core set of requirements would be for ActivityPub. The idea is that with this core set of requirements and domain-specific interoperability profiles (for microblogging, media sharing, social linking, etc.), we may be able to improve the current Fediverse developer experience and reduce the frustration associated with federation.

(The following is a starting point for exploration. It will probably change significantly over time.)

The proposed AP Core requires a server to implement the following:

* The instance MUST implement at least one actor
  * The actor MUST have at least the following properties:
    * `id`     (MUST be valid for dereferencing)
    * `type`   (MUST be a single value)
    * `inbox`  (MUST be operational for HTTP `POST`, MAY be instance-level)
    * `outbox` (Required by AP, but MAY be nonoperational)
* The instance MUST implement at least one of the following behaviors:
  * Incoming activity processing
  * Activity publication
    * Must support `inbox` `Follow` and `Undo` activities.

Although `type` is constrained to a single value in this AP Core, a domain-specific interoperability profile MAY relax that constraint so that Activity Streams 2.0 JSON-LD extensions are supported in that context.

The `type` value MUST be one of: `Service` or `Person`. Interoperability profiles will generally extend this set of valid values, possibly including allowing arbitrary extensions to them.

In instance MAY have a nonoperational `outbox`. However, AP requires an `outbox` property on actors. The `outbox` endpoint MAY return an HTTP status of 403 Forbidden or 501 Not Implemented (or equivalent).

An instance MAY not store any activities. An `inbox` `GET` MAY return an HTTP error status.

All AP Core actors MUST have URIs that can be dereferenced. In other words, they MUST be URLs (typically, HTTP/S) that can be used to retrieve the actor resource (the JSON document describing the actor).

Other than `Follow` and `Undo` for activity publishers, an instance MAY process any subject (including none) of the Activity Streams 2.0 activities received in its `inbox`.

An AP Core instance MAY not have any authentication or authorization features.

An instance MAY choose to not do `inbox` forwarding.


## Discussion

Note that this document does *not* represent a proposal. It's a starting point (an intentionally relatively extreme one) for further discussion and exploring the core essence of the AP protocol.

### Single-valued Type

The single-valued `type` constraint has caused concern for some reviewers. The AP Core does not support JSON-LD extensibility. However, domain-specific interoperability profile may allow support for such extensibility. The AP Core definition doesn't prevent it.

#### General Extensibility

The ActivityPub specification allows activities to be processed as either JSON-LD or plain JSON. The AP Core only supports plain JSON. Therefore, there are no extensibility features defined for the AP Core.

### Interoperability Profiles

An interoperability profile (also sometimes called a "conformance profile" or a "compliance profile") is a type of specification that extends the AP Core for a specific problem domain or for cross-cutting functionality. These interoperability profiles can relax and extend the minimal core for specific purposes or social web domains, like microblogging.

Examples:

* Interoperability Profiles (layered on AP Core)
  * Microblogging (Mastodon-flavored AP)
  * Image sharing (probably based on PixelFed)
  * Forums
  * Marketplaces
  * Long-form Writing
  * Internet/Web of Things
  * Distributed Moderation (cross-cutting)
  * Activity Streaming (SSE, Websockets, etc. - cross-cutting)
  * Full Linked Data Support (cross-cutting)
  * Others . . .
* AP Minimal Core (AP Core)

In practice, I wouldn't expect any nontrivial server to only implement the AP Core. They'd implement one or more interoperability profiles. The work to define those has not been done yet. The current thinking (myself and others I've discussed this with) is that the interoperability profiles would be maintained by the developer communities implementing servers for those social web domains.

Servers implementing different interoperability profiles are not expected to work together, but they may, to some extent, depending on the profiles.

### Federation Limitations (especially Mastodon)

It should be clear that only implementing the AP Core will not result in an ActivityPub implementation that will federate with existing server implementations like Mastodon. For example, a partial list of additional functionality needed for federation with Mastodon includes:

* Webfinger support to convert Mastodon account identifiers to AP actor URIs
* A specific version of HTTP Signatures to sign requests.
* Special properties on actors (like `preferredUsername` and signature-related properties)

Many microblogging servers mostly mimic the Mastodon-specific features for federation purposes. The requirements beyond the AP Core should be documented in a microblogging interoperability profile that overlaps with ActivityPub but defines specific variations for this social web domain.


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

## Development

The project is configured for pre-commit checks. To install the checks, run:

```sh
poetry run pre-commit install
```

If you're making temporary changes to the code and want to be sure you don't accidentally commit them, you can add a NO‎COMMIT string somewhere in the source code (a comment, for example). The related pre-commit check will detect this and prevent a commit.

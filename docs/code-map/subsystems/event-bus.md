# Event Bus

> Status: pilot page. Verified against source on 2026-11-25.
> Everything here is stated from the code. Items marked **Inferred:** are not directly
> visible in code; **Open question** items are unresolved observations.
> See [conventions](../index.md#conventions).

## Scope

In-process publish/subscribe of `Event` objects between hub components.
Two separate mechanisms exist in the code:

| Mechanism | Interfaces | Implementation | Delivery |
|---|---|---|---|
| **Hub event bus** (topic based) | `org.sensorhub.api.event.IEventBus`, `org.sensorhub.api.event.IEventPublisher`, `org.sensorhub.api.event.ISubscriptionBuilder` | `org.sensorhub.impl.event.EventBus` | Asynchronous, on a thread pool, with per-subscriber buffers (`java.util.concurrent.SubmissionPublisher`) |
| **Per-object listeners** (no topics) | `org.sensorhub.api.event.IEventProducer`, `org.sensorhub.api.event.IEventHandler`, `org.sensorhub.api.event.IEventListener` | `org.sensorhub.impl.event.BasicEventHandler` | Synchronous, on the publisher's thread |

Drivers, outputs and modules emit events through the per-object mechanism; the system
registry forwards them onto the hub event bus (see [Data path](#data-path-driver-output-to-bus-subscriber)).

Source folders:
- API: [`sensorhub-core/.../api/event/`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event)
- Implementation: [`sensorhub-core/.../impl/event/`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event)
- Tests: [`TestEventBus`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/event/TestEventBus.java)

## Key types

### API (`org.sensorhub.api.event`)

| Type | Kind | Role (from code / javadoc) |
|---|---|---|
| [`Event`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event/Event.java#L28) | abstract class | Base event. Fields `timeStamp`, transient `source`; abstract `getSourceID()`. Javadoc: "Immutable base class... All sub-classes should remain immutable." |
| [`IEventBus`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event/IEventBus.java#L29) | interface | `getPublisher(sourceID)`, `getPublisher(groupID, sourceID)`, `newSubscription()`, `newSubscription(Class)`, `getNumberOfSubscribers(sourceID)`, `shutdown()` |
| [`IEventPublisher`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event/IEventPublisher.java#L31) | interface | Extends `Flow.Publisher<Event>`; adds `publish(e)`, `publish(e, onDrop)`, `getNumberOfSubscribers()` |
| [`ISubscriptionBuilder`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event/ISubscriptionBuilder.java#L34) | interface | Fluent builder: `withTopicID`, `withTopicIDs`, `withEventType`, `withFilter`, then `subscribe(...)` or `consume(...)`; all return `CompletableFuture<Subscription>` |
| [`SubscribeOptions`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event/SubscribeOptions.java#L35) | class | Holds `sourceIDs`, `eventTypes`, `filter`. [`validate()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event/SubscribeOptions.java#L60) requires at least one topic ID |
| [`EventUtils`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event/EventUtils.java#L26) | utility | Builds topic ID strings (see [Topic naming](#topic-naming)) |
| [`IEventListener`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event/IEventListener.java#L29) | functional interface | `handleEvent(Event)`; no flow control |
| [`IEventProducer`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event/IEventProducer.java#L26) | interface | `registerListener` / `unregisterListener` |
| [`IEventHandler`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event/IEventHandler.java#L30) | interface | Extends `IEventProducer`; adds `publish(e)`, `getNumListeners()`, `clearAllListeners()` |
| [`IEventMultiTopicProducer`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event/IEventMultiTopicProducer.java#L26) | interface | Topic-scoped listener registration. No implementations or references found in this repo |
| [`IEventSourceInfo`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event/IEventSourceInfo.java#L18) | interface | `getGroupID()`, `getSourceID()`. Only implementation: `EventSourceInfo` |

### Implementation (`org.sensorhub.impl.event`)

| Type | Used by | Role |
|---|---|---|
| [`EventBus`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/EventBus.java#L53) | `SensorHub` | The only `IEventBus` implementation. Holds `Map<String, IEventPublisher> publishers` keyed by topic ID and one shared thread pool |
| [`EventBus.SubscriptionBuilderImpl`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/EventBus.java#L256) | `EventBus` | `ISubscriptionBuilder` implementation; extends `SubscribeOptions.Builder` |
| [`FilteredEventPublisher`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/FilteredEventPublisher.java#L33) | `EventBus` | Publisher for a standalone topic or a group. Extends `FilteredAsyncPublisher` → `java.util.concurrent.SubmissionPublisher` |
| [`FilteredEventPublisherWrapper`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/FilteredEventPublisherWrapper.java#L34) | `EventBus` | Publisher for a member of a group: publishes into the group publisher; subscribers are wrapped in a `FilteredSubscriber` matching `e.getSourceID()` |
| [`FilteredSubscriber`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/FilteredSubscriber.java#L33) | `EventBus`, wrapper | Drops events failing a predicate; on drop calls `request(1)` so filtered events do not consume demand ([`onNext`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/FilteredSubscriber.java#L47)) |
| [`AggregateSubscription`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/AggregateSubscription.java#L37) | `EventBus.subscribeMulti` | Joins N topic subscriptions into one `Subscription` for a subscriber |
| [`SubscriberConsumerAdapter`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/SubscriberConsumerAdapter.java#L26) | `SubscriptionBuilderImpl` | Adapts `Consumer` callbacks to `Flow.Subscriber` |
| [`DelegatingSubscriber`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/DelegatingSubscriber.java#L31), [`DelegatingSubscriberAdapter`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/DelegatingSubscriberAdapter.java#L34), [`DelegatingSubscription`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/DelegatingSubscription.java#L30) | various | Pass-through base classes |
| [`BasicEventHandler`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/BasicEventHandler.java#L49) | `AbstractModule`, `AbstractSensorDriver`, `AbstractDataInterface`, `AbstractControlInterface`, `AbstractProcessDriver`, `SMLOutputInterface` | Synchronous `IEventHandler` (see [Per-object listeners](#per-object-listeners-basiceventhandler)) |
| [`EventSourceInfo`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/EventSourceInfo.java#L21) | test fixture only | Simple `IEventSourceInfo` value class |

Classes in the package with **no references elsewhere in this repo** (searched all `.java` files):
`WeakEventHandler`, `SubscriberGroup`, `ListenerSubscriber`, `BaseSubscriber`, `EventThreadFactory`,
`SubmissionPublisherRetroflow`. `FilteredSubmissionPublisherV11` is referenced only inside a
commented-out block in `FilteredEventPublisherWrapper`. `EventBus.MAIN_TOPIC` is also unreferenced.

## How it works

### Bus creation

- `SensorHub.start()` constructs one [`new EventBus()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L134) during startup and calls [`eventBus.shutdown()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L176) on stop.
- Components obtain it via [`ISensorHub.getEventBus()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/ISensorHub.java#L46).
- The [`EventBus` constructor](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/EventBus.java#L68) creates a `ThreadPoolExecutor(0, 100, 10s, SynchronousQueue)` named `EventBus`, shared by every publisher.
- [`MAX_BUFFER_CAPACITY`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/EventBus.java#L56) = 1024 is passed to every `FilteredEventPublisher` as the `SubmissionPublisher` max buffer capacity (per subscriber, per JDK `SubmissionPublisher` semantics).

### Publishers

- [`getPublisher(topicID)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/EventBus.java#L98): returns the publisher already mapped to `topicID`, or creates a `FilteredEventPublisher` ([`ensurePublisher`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/EventBus.java#L82)).
- [`getPublisher(groupID, topicID)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/EventBus.java#L108): first ensures a `FilteredEventPublisher` for `groupID`, then, if `topicID` has no publisher yet, maps it to a `FilteredEventPublisherWrapper` around the group publisher.
  - Publishing on the member publisher publishes into the group publisher, so a subscriber on `groupID` receives events from every member.
  - A subscriber on a member `topicID` receives only events whose `getSourceID()` equals `topicID`.
- [`FilteredEventPublisher.publish(e)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/FilteredEventPublisher.java#L49) calls `SubmissionPublisher.offer` with an on-drop handler that logs a WARN `"... dropped by subscriber ..."` and returns `false` (no retry). `publish(e, onDrop)` lets the caller supply the handler.

### Subscriptions

```
newSubscription(EventClass)            → SubscriptionBuilderImpl (SubscribeOptions.Builder)
  .withTopicID(...) .withEventType(...) .withFilter(...)
  .subscribe(subscriber | onNext[, onError[, onComplete]])  or  .consume(consumer)
      → build() → validate()                       (≥1 topic ID required)
      → EventBus.subscribe(opts, subscriber)
          → buildPredicate(opts)                   (event-type check AND custom filter)
          → 1 topic : subscribe(topic, filter, sub) → getPublisher(topic).subscribe(FilteredSubscriber)
          → N topics: subscribeMulti → AggregateSubscription → one subscribe(...) per topic
```

- [`buildPredicate`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/EventBus.java#L201): with one event type, the result is `type.isAssignableFrom(e.getClass()) && filter`. With several types it is an OR over the types. **Open question:** in the multi-type branch the custom `filter` is not included in the combined predicate ([lines 215–224](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/EventBus.java#L215-L224)), so `withFilter` appears to be ignored when more than one `withEventType` is set.
- Subscribing to a topic that has no publisher yet creates a standalone `FilteredEventPublisher` for it ([`subscribe(String, Subscriber)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/EventBus.java#L149)).
- **Flow control:**
  - [`consume(consumer)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/EventBus.java#L314) builds a `SubscriberConsumerAdapter` with flow control disabled; its [`onSubscribe`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/SubscriberConsumerAdapter.java#L63) calls `request(Long.MAX_VALUE)`.
  - All `subscribe(...)` overloads leave flow control enabled. Nothing is delivered until the caller calls `Subscription.request(n)` on the subscription returned by the future.
- `AggregateSubscription` [`onSubscribe`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/AggregateSubscription.java#L89) calls the client's `onSubscribe` only after all N underlying subscriptions exist. [`request(n)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/AggregateSubscription.java#L106) forwards `n` to each underlying subscription. [`onNext`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/AggregateSubscription.java#L78) passes events straight through.

### Topic naming

[`EventUtils`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event/EventUtils.java#L28) builds topic IDs from these constants: `modules/`, `systems/`, `/outputs/`, `/commands/`, `/status`, `/data`, `/ack`.

| Method | Resulting topic ID |
|---|---|
| `getModuleRegistryTopicID()` | `modules/` |
| `getModuleTopicID(id)` | `modules/{id}` |
| `getSystemRegistryTopicID()` | `systems/` |
| `getSystemStatusTopicID(uid)` | `systems/{uid}/status` |
| `getDataStreamStatusTopicID(uid, output)` | `systems/{uid}/outputs/{output}/status` |
| `getDataStreamDataTopicID(uid, output)` | `systems/{uid}/outputs/{output}/data` |
| `getCommandStreamStatusTopicID(uid, input)` | `systems/{uid}/commands/{input}/status` |
| `getCommandDataTopicID(uid, input)` | `systems/{uid}/commands/{input}/data` |
| `getCommandStatusTopicID(uid, input)` | `systems/{uid}/commands/{input}/ack` |

Module lifecycle events use a separate group ID:
[`ModuleRegistry.EVENT_GROUP_ID`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L82) = `urn:osh:modules`.

### Per-object listeners (`BasicEventHandler`)

- [`publish(e)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/BasicEventHandler.java#L86) is `synchronized` and calls each listener's `handleEvent` in turn on the caller's thread.
- Exceptions thrown by a listener are caught and logged at ERROR; the remaining listeners still run.
- Re-entrant calls are deferred rather than applied mid-iteration: `publish` calls made during dispatch are queued, and register/unregister calls go into temporary lists. Both are applied after the current dispatch completes.
- Javadoc says weak references are used. **Open question:** `BasicEventHandler` holds a plain `List<IEventListener>`; only the unused `WeakEventHandler` holds `WeakReference`s.

### Data path: driver output to bus subscriber

Traced for observations:

1. A driver output calls `eventHandler.publish(new DataEvent(...))` on its own `BasicEventHandler`, created by [`new BasicEventHandler()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/data/AbstractDataInterface.java#L72) in `AbstractDataInterface` (which `AbstractSensorOutput` extends). Example: `DefaultLocationOutputLLA` [`eventHandler.publish`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/DefaultLocationOutputLLA.java#L77).
2. When the driver is registered, `SystemDriverTransactionHandler` registers a `DataStreamTransactionHandler` as a listener on each output ([`output.registerListener`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L283)).
3. [`DataStreamTransactionHandler.handleEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DataStreamTransactionHandler.java#L258) → [`addObs(DataEvent)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DataStreamTransactionHandler.java#L181). This builds `ObsData`, then:
   - publishes an `ObsEvent` on topic `systems/{uid}/outputs/{output}/data` via [`getDataEventPublisher()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DataStreamTransactionHandler.java#L223) (code comment: "first forward to event bus to minimize latency");
   - then writes each obs to the database's observation store.
4. Subscribers such as ConSys `ObsHandler` [`newSubscription`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/ObsHandler.java#L362) and `DataStreamSource` [`newSubscription`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/DataStreamSource.java#L157) subscribe to that topic with `newSubscription(ObsEvent.class)`.

Datastream lifecycle events ([`publishDataStreamEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DataStreamTransactionHandler.java#L286)) are published on four topics in turn:
1. the datastream status topic;
2. the system status topic;
3. each ancestor system's status topic (walking `getParent`);
4. `systems/`.

Similar code exists in `SystemTransactionHandler` and `CommandStreamTransactionHandler`.

### Module events

- `ModuleRegistry` [forwards](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L1312) each module's events with `getPublisher(EVENT_GROUP_ID, e.getSourceID())`, so all module events share the `urn:osh:modules` group.
- `AdminUI` [subscribes](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUI.java#L292) to the whole group with `consume(...)`.
- Module unload uses the single-argument form instead: [`getPublisher(moduleID)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L526).

## Observed behaviours to be aware of

Each item below follows from the code paths above. None is covered by a test in `TestEventBus`.

1. **A member topic's publisher type is fixed by the first call.** `ensurePublisher` never replaces an existing entry. If a topic ID is first used through `getPublisher(topicID)`, or by a subscription to it, it becomes a standalone `FilteredEventPublisher`. A later `getPublisher(groupID, topicID)` then returns that standalone publisher, and its events do not reach `groupID` subscribers. The comment above `ensurePublisher` describes converting a "placeholder" publisher, but no conversion code exists ([`subscribe`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/event/EventBus.java#L149) has the placeholder code commented out). `TestEventBus.createPublishersAndSubscribe` always creates publishers before subscribing, so this ordering is not exercised.
2. **Wildcard topics are documented but not implemented.** `ISubscriptionBuilder` javadoc says topic IDs may end in a wildcard (`"mysource/*"`). `EventBus` uses topic IDs only as literal `HashMap` keys, and nothing in `impl/event` matches `*`. No caller in the repo passes a wildcard.
3. **Time ordering across topics is documented but not implemented.** `AggregateSubscription` javadoc says it "tries to order events by time"; the ordering code is commented out.
4. **Subscribing to several topics multiplies the requested count.** `AggregateSubscription.request(n)` requests `n` from each of the N topics, so up to `N × n` events can be delivered.
5. **`subscribe(...)` without `request(n)` receives nothing** (see Flow control).
6. **Events are dropped when a subscriber falls behind.** Once a subscriber's buffer is full, `publish(e)` drops the event and logs a WARN.

## Where to make changes (by precedent in the code)

| Task | Existing pattern to follow |
|---|---|
| Publish a new event type | Subclass `Event` and implement `getSourceID()`. Examples: `ModuleEvent`, `DataStreamEvent`, `ObsEvent`. Publish via `getEventBus().getPublisher(topic).publish(e)` as in `DataStreamTransactionHandler` |
| Add a new topic family | Add builder methods to `EventUtils` next to the existing `getXxxTopicID` methods |
| Consume events with back-pressure | `newSubscription(Type.class).withTopicID(t).subscribe(subscriber)` and call `request(n)`, as in `DataStreamSource` |
| Consume events without back-pressure | `.consume(consumer)`, as in `AdminUI` |
| Change dispatch, buffering or threading | `EventBus` constructor (thread pool, `MAX_BUFFER_CAPACITY`), `FilteredEventPublisher` (drop handling) |
| Emit events from a driver or module | Call `eventHandler.publish(e)` on the inherited `BasicEventHandler` (`AbstractModule`, `AbstractDataInterface`); the registry forwards to the bus |

## Tests

[`TestEventBus`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/event/TestEventBus.java) covers:
- one or several publishers and subscribers, with and without filters;
- group publishers with group and multi-topic subscribers;
- filtering by event class;
- throughput.

```bash
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.event.TestEventBus'
```

Callers of the bus are also exercised in `TestModuleRegistry`, `TestSystemDriverRegistry` and `TestOnDemandProcess`.

## Related

- [Code map index](../index.md)
- External user docs: osh-docs `docs/osh-node/dev-docs/osh-core-apis/events.md` (separate repo, not verified against this fork)

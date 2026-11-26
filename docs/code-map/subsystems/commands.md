# Commands / Tasking

> Status: draft page. Verified against source on 2026-11-25.
> Everything here is stated from the code. Items marked **Inferred:** are not directly
> visible in code; **Open question** items are unresolved observations.
> See [conventions](../index.md#conventions).

## Scope

Sending commands to taskable systems (actuators, sensors with control inputs, processes) and
reporting command status back to the sender. Commands travel on the hub event bus; the system
registry connects each driver control input to its command topic and persists commands and
status reports.

| Part | Interfaces / types | Implementation |
|---|---|---|
| Command stream descriptor | `org.sensorhub.api.command.ICommandStreamInfo` | `org.sensorhub.api.command.CommandStreamInfo` |
| Command / status / result | `org.sensorhub.api.command.ICommandData`, `org.sensorhub.api.command.ICommandStatus`, `org.sensorhub.api.command.ICommandResult` | `CommandData`, `CommandStatus`, `CommandResult` |
| Driver side | `org.sensorhub.api.command.ICommandReceiver`, `org.sensorhub.api.command.IStreamingControlInterface` | `org.sensorhub.impl.command.AbstractControlInterface`, `org.sensorhub.impl.sensor.AbstractSensorControl` |
| Routing & persistence | — | `org.sensorhub.impl.system.CommandStreamTransactionHandler`, `SystemDriverTransactionHandler` (package-private) |

Source folders:
[`api/command`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command),
[`impl/command`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/command),
[`CommandStreamTransactionHandler`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/CommandStreamTransactionHandler.java#L63),
[`AbstractSensorControl`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorControl.java#L38).

## Key types

### Model (`org.sensorhub.api.command`)

| Type | Kind | Role (from code / javadoc) |
|---|---|---|
| [`ICommandStreamInfo`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/ICommandStreamInfo.java#L33) | interface | Command stream descriptor: `getSystemID()`, `getControlInputName()`, parameter record structure/encoding, `getValidTime()`, `getIssueTimeRange()`, `getExecutionTimeRange()`, optional result and feasibility-result structures. [`getFullName()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/ICommandStreamInfo.java#L141) = `{sysUID}#{inputName}` |
| [`CommandStreamInfo`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/CommandStreamInfo.java#L33) | class + Builder | Default implementation |
| [`ICommandData`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/ICommandData.java#L31) | interface | One command: `getID()` / `assignID()`, `getCommandStreamID()`, `getFoiID()`, `getSenderID()`, `getIssueTime()`, `getParams()` (`DataBlock`) |
| [`CommandData`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/CommandData.java#L35) | class + Builder | [`build()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/CommandData.java#L209) requires a valid command stream ID and params; defaults `issueTime` to now. A [helper constructor](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/CommandData.java#L60) is for "send[ing] a command directly to a driver" |
| [`ICommandStatus`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/ICommandStatus.java#L41) | interface | Status report: `getCommandID()`, `getReportTime()`, `getStatusCode()`, `getExecutionTime()`, `getProgress()`, `getMessage()`, `getResult()` |
| [`CommandStatusCode`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/ICommandStatus.java#L51) | enum | `PENDING`, `ACCEPTED`, `SCHEDULED`, `UPDATED`, `EXECUTING` (non-final); `REJECTED`, `CANCELED`, `FAILED`, `COMPLETED` (final, [`isFinal()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/ICommandStatus.java#L136)) |
| [`CommandStatus`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/CommandStatus.java#L35) | class + Builder | Static factories `completed`, `rejected`, `failed`, `pending`, `accepted`, `scheduled`, `progress` |
| [`ICommandResult`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/ICommandResult.java#L44) / [`CommandResult`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/CommandResult.java#L36) | interface / class | Result as inline records, observation IDs, datastream IDs or external links; factories `withData`, `withObservation(s)`, `withDatastream(s)` |
| [`CommandEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/CommandEvent.java#L28) | event | Carries `ICommandData` + `correlationID` on the command data topic |
| [`CommandStatusEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/CommandStatusEvent.java#L28) | event | Carries `ICommandStatus` + `correlationID` on the status (`/ack`) topic |
| [`CommandStreamEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/CommandStreamEvent.java#L31) | abstract event | Base of the above and of `CommandStream{Added,Changed,Enabled,Disabled,Removed}Event` |
| [`CommandException`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/CommandException.java#L28) | exception | Extends `SensorHubException` |

There is no separate "ack" type: acknowledgements are `CommandStatusEvent`s on the topic built by
[`EventUtils.getCommandStatusTopicID`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event/EventUtils.java#L183), which ends in [`ACK_CHANNEL`](../../../sensorhub-core/src/main/java/org/sensorhub/api/event/EventUtils.java#L34) = `/ack`.

### Driver side

| Type | Role |
|---|---|
| [`ICommandReceiver`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/ICommandReceiver.java#L29) | `ISystemDriver` with [`getCommandInputs()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/ICommandReceiver.java#L36) |
| [`IStreamingControlInterface`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/IStreamingControlInterface.java#L41) | One control input: `getName()`, `getCommandDescription()`, [`getCommandEncoding()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/IStreamingControlInterface.java#L79) (default text), `getValidStartTime()`, `validateCommand`, [`submitCommand`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/IStreamingControlInterface.java#L134), and default-failing [`updateCommand`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/IStreamingControlInterface.java#L143) / [`cancelCommand`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/IStreamingControlInterface.java#L155) |
| [`IStreamingControlInterfaceWithResult`](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/IStreamingControlInterfaceWithResult.java#L22) | Adds `getResultDescription()` / `getResultEncoding()`; the registry then creates a command stream with a result schema |
| [`AbstractControlInterface`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/command/AbstractControlInterface.java#L39) | Holds `name`, `parent`, a [`BasicEventHandler`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/command/AbstractControlInterface.java#L65) and a logger; `isEnabled()` returns `true`; `validateCommand` is empty |
| [`AbstractSensorControl`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorControl.java#L38) | [`submitCommand`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorControl.java#L58) runs `execCommand(params)` on the common pool and maps `true`/`false`/`CommandException` to `completed` / `failed` |

`IStreamingControlInterface.submitCommand` javadoc: the future must always return a status; a final
code means "no further status reports are to be expected"; otherwise "Subsequent reports are then
sent via the dedicated event channel". The future "should only complete exceptionally if there is an
unexpected error".

## How it works

### Registering a control input

`SystemDriverTransactionHandler.doFinishRegister` calls, for each entry of `getCommandInputs()`,
[`doRegister(IStreamingControlInterface)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L321):

1. `addOrUpdateCommandStream(...)` on the system handler: creates / versions / updates the command stream entry with the same rules as datastreams (see [system registry](system-registry.md#output--datastream)), using `getIssueTimeRange() != null` as "has commands" ([source](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemTransactionHandler.java#L479)).
2. Cancels any previous command subscription for that input.
3. [`connectControlInput`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L367) → `csHandler.connectCommandReceiver(subscriber)`.
4. `enable()` (`CommandStreamEnabledEvent`) and `controlInput.registerListener(csHandler)`.

Inputs added after start go through `registry.register(controlInterface)`, e.g. `AbstractSensorModule` [`register(controlInterface)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L381).

### Command flow: submitter → driver → status

```
Submitter (ConSys / SPS / admin UI / CommandStreamSink)
  txn = new SystemDatabaseTransactionHandler(bus, db).getCommandStreamHandler(...)
  cmd = CommandData.Builder().withCommandStream(txn.getCommandStreamKey().getInternalID())
                             .withSender(...).withParams(...).build()
  txn.submitCommand(correlationID, cmd[, timeout])
    → connectStatusReceiver(correlationID, statusSubscriber)   subscribe to  .../commands/{input}/ack
    → publish CommandEvent on                                  systems/{uid}/commands/{input}/data
                                    │ event bus
Registry-side CommandStreamTransactionHandler.connectCommandReceiver (subscriber wrapper)
    onNext: copy cmd with internal command stream ID → db.getCommandStore().add(cmd)
            e.getCommand().assignID(cmdKey); remember correlationID as pending
            → forward to SystemDriverTransactionHandler subscriber
            schedule: after ackTimeout (5000 ms) still pending → sendStatus(PENDING)
SystemDriverTransactionHandler subscriber.onNext (CompletableFuture.runAsync)
    controlInput.submitCommand(cmd)
      .thenAccept(status → csHandler.sendStatus(correlationID, status); request(1))
      .exceptionally(→ sendStatus(FAILED "Internal error processing command"); request(1))
sendStatus: publish CommandStatusEvent on .../ack, then db.getCommandStatusStore().add(status)
                                    │ event bus
Submitter's status subscriber: matches correlationID, then command ID; completes on final status
```

Links for each step:

| Step | Source |
|---|---|
| Submit, with status subscriber | [`submitCommand(correlationID, cmd, subscriber)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/CommandStreamTransactionHandler.java#L332) |
| Submit, future of first status (optional timeout → `TimeoutException`) | [`submitCommand(correlationID, cmd, timeOut, unit)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/CommandStreamTransactionHandler.java#L400) |
| Per-command status filter | [`connectStatusReceiver(correlationID, subscriber)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/CommandStreamTransactionHandler.java#L257) |
| Receive, persist, assign ID, ack timeout | [`connectCommandReceiver(subscriber, ackTimeout)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/CommandStreamTransactionHandler.java#L162), [store add](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/CommandStreamTransactionHandler.java#L215) |
| Dispatch to driver | [`controlInput.submitCommand`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L388) |
| Publish + store status | [`sendStatus`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/CommandStreamTransactionHandler.java#L463) |
| Later status from the driver | [`handleEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/CommandStreamTransactionHandler.java#L487): a `CommandStatusEvent` published on the control input's own `BasicEventHandler` is passed to `sendStatus(-1, status)` |

- **One command at a time per input.** The driver subscriber requests 1 on subscribe and requests the next only after the driver's future completes ([`sub.request(1)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L391)).
- **Synchronous exception in `submitCommand`** cancels the subscription: log message "No more commands will be processed." ([`sub.cancel()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L405)).
- **Single receiver.** `connectCommandReceiver` throws `IllegalStateException` if the data topic already has a subscriber ([check](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/CommandStreamTransactionHandler.java#L167)).
- **Lifecycle events** use [`publishCommandStreamEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/CommandStreamTransactionHandler.java#L525): command stream status topic, system status topic, ancestors, then `systems/`.

### Submitters and external receivers found in the repo

| Caller | Role | Source |
|---|---|---|
| ConSys `CommandHandler` | submit (waits for first status if a response is expected) | [`submitCommand`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/task/CommandHandler.java#L387) |
| ConSys `CommandHandler` | external receiver (with `command_status_permissions.create`) | [`connectCommandReceiver`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/task/CommandHandler.java#L276) |
| ConSys `CommandStatusHandler` | status ingestion from external receivers | [`sendStatus`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/task/CommandStatusHandler.java#L316) |
| SPS `SystemTaskingConnector` | submit; and external receiver that always replies `completed` | [`submitCommand`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SystemTaskingConnector.java#L173), [`connectCommandReceiver`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SystemTaskingConnector.java#L197) |
| Admin UI `SWEControlForm` | submit, no status subscriber | [`submitCommand`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/SWEControlForm.java#L114) |
| `CommandStreamSink` (processing) | submit with correlation ID 0 | [`submitCommand`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/CommandStreamSink.java#L158) |

## Observed behaviours to be aware of

1. **Open question:** `validateCommand`, `updateCommand` and `cancelCommand` are never called anywhere in the repo. `validateCommand` javadoc says it "is called before the command is submitted for execution"; `submitCommand` has `// TODO validate command` ([line 337](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/CommandStreamTransactionHandler.java#L337)).
2. **Open question:** `submitCommand` checks the stream with `cmd.getCommandStreamID() == csKey.getInternalID()` ([line 335](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/CommandStreamTransactionHandler.java#L335)), a reference comparison on `BigId` (which defines `equals`). All callers found pass `getCommandStreamKey().getInternalID()` of the same handler.
3. **Open question:** the "Receiving system is disabled" rejection is only applied when `rootHandler instanceof SystemRegistryTransactionHandler` ([line 345](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/CommandStreamTransactionHandler.java#L345)). Every submitter in the table above builds its handler from a plain `SystemDatabaseTransactionHandler`, so this check does not run for them. **Inferred:** with no receiver, those submitters wait until their own timeout.
4. **Status can be stored twice.** A driver that both returns a status from the future and publishes a `CommandStatusEvent` produces two `sendStatus` calls (correlation ID and `-1`). The test fixture `FakeSensorControl1` does both ([`eventHandler.publish`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/sensor/FakeSensorControl1.java#L84)).
5. **Open question:** when a control input re-registers, the old `CommandStreamTransactionHandler` is not unregistered as a listener on the input ([line 348](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L348)); the datastream path does unregister the old handler. **Inferred:** later status events from that input are then handled by both handlers.
6. **Open question:** `CommandStreamTransactionHandler.update` publishes `CommandStreamChangedEvent(csInfo)` with the argument, not the stored `newCsInfo` ([line 117](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/CommandStreamTransactionHandler.java#L117)), and always keeps the old valid time.
7. **Open question:** `AbstractSensorControl` javadoc says "async exec, scheduling and status history are reported as unsupported", but the class has no such methods. Its default `execCommand` throws `UnsupportedOperationException`, which `submitCommand` does not catch, so the registry reports `FAILED` "Internal error processing command".
8. `CommandEvent` requires a non-empty sender ID ([line 38](../../../sensorhub-core/src/main/java/org/sensorhub/api/command/CommandEvent.java#L38)) and returns it from `getSourceID()`, while other `CommandStreamEvent`s return their topic ID. `CommandData.UNKNOWN_SENDER` is defined but not referenced.
9. The ack-timeout `PENDING` status is sent through `sendStatus`, so it is also stored. The pending map is cleared by any status event with the same correlation ID; statuses sent by the driver later via events carry `-1`.

## Where to make changes (by precedent in the code)

| Task | Existing pattern to follow |
|---|---|
| Add a control input to a driver | Subclass `AbstractSensorControl`, implement `getCommandDescription()` and `execCommand`, or override `submitCommand` for async status (as `FakeSensorControl1`); add it with `AbstractSensorModule.addControlInput` |
| Report asynchronous progress | Return a non-final status from the future, then `eventHandler.publish(new CommandStatusEvent(this, 0, status))` |
| Return a command result | Implement `IStreamingControlInterfaceWithResult` and use `CommandStatus.completed(id, execTime, CommandResult.withData(...))` |
| Submit a command from a service | `new SystemDatabaseTransactionHandler(bus, db).getCommandStreamHandler(...)` then `submitCommand(...)`, as in ConSys `CommandHandler` |
| Act as an external command receiver | `connectCommandReceiver(subscriber)` + `sendStatus(...)`, as in ConSys `CommandHandler` / `CommandStatusHandler` |
| Change ack timeout or persistence order | `CommandStreamTransactionHandler.connectCommandReceiver` |

## Tests

- [`TestOnDemandProcess`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/processing/TestOnDemandProcess.java): direct `submitCommand` on a process input, and via `CommandStreamTransactionHandler.submitCommand` with a 1 s timeout.
- [`TestCommandSinkProcess`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/processing/TestCommandSinkProcess.java): process chain sending commands to a `FakeSensorControl1`.
- [`TestSPSService`](../../../sensorhub-service-swe/src/test/java/org/sensorhub/impl/service/sps/TestSPSService.java): SPS submit and direct tasking against `FakeSensorControl1` / `FakeSensorControl2`.
- [`TestControlStreams`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys/TestControlStreams.java): ConSys control stream creation.
- Store-level: `TestInMemCommandStore`, `TestInMemCommandStreamStore`, `TestMVCommandStore`, `TestMVCommandStreamStore`.

```bash
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.processing.TestOnDemandProcess'
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.processing.TestCommandSinkProcess'
./gradlew :sensorhub-service-swe:test --tests 'org.sensorhub.impl.service.sps.TestSPSService'
```

`TestSystemDriverRegistry` contains no command-related assertions. No test covers the ack timeout or the "Receiving system is disabled" rejection.

## Related

- [Code map index](../index.md)
- [System registry & data model](system-registry.md)
- [Event bus](event-bus.md) (command topics)
- [Sensor drivers](sensor-drivers.md)
- [Processing](processing.md)
- [Connected Systems API service](service-consys.md)
- [SWE services (SOS / SPS)](service-swe.md)

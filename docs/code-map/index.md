# osh-core Code Map

An index into the source code of this repository, for humans and coding agents.
Start at [`AGENTS.md`](../../AGENTS.md) for build commands and working rules.

## Conventions

These docs describe **only what can be determined from the source code**. There are
no design rationales, because none are available to the maintainers of this fork.

- **Every claim is traceable.** Types are written as fully-qualified names in backticks
  (`org.sensorhub.impl.event.EventBus`), or as relative links to source files. Line anchors
  (`File.java#L98`) point at the declaration being described.
- **Inferred:** marks anything not directly visible in code, such as a likely purpose.
- **Open question** marks observations that look inconsistent: javadoc that disagrees with
  code, unused classes, commented-out logic. These are recorded, not resolved.
- **Quoted intent.** Where the code states intent (javadoc, comments), it is quoted and
  attributed, not paraphrased.
- **"Where to make changes"** sections point to existing patterns in the code. They describe
  precedent, not endorsed design.
- **Checked by a script.** [`tools/check_refs.py`](tools/check_refs.py) verifies that every
  link, line anchor and class name still matches the code. Run it after editing code or docs:
  ```bash
  python3 docs/code-map/tools/check_refs.py
  ```

## Subsystem pages

Each page uses the same layout: Scope → Key types → How it works → Observed behaviours →
Where to make changes → Tests.

| Subsystem | Page | Main source location |
|---|---|---|
| Event bus | [subsystems/event-bus.md](subsystems/event-bus.md) | `sensorhub-core/.../api/event`, `.../impl/event` |
| Module lifecycle & registry | [subsystems/module-lifecycle.md](subsystems/module-lifecycle.md) | `sensorhub-core/.../api/module`, `.../impl/module` |
| System registry & data model | [subsystems/system-registry.md](subsystems/system-registry.md) | `sensorhub-core/.../api/system`, `.../api/data`, `.../impl/system` |
| Databases & datastores (API, federated DB) | [subsystems/databases.md](subsystems/databases.md) | `sensorhub-core/.../api/database`, `.../api/datastore`, `.../impl/database`, `.../impl/datastore` |
| Sensor drivers | [subsystems/sensor-drivers.md](subsystems/sensor-drivers.md) | `sensorhub-core/.../api/sensor`, `.../impl/sensor` |
| Commands / tasking | [subsystems/commands.md](subsystems/commands.md) | `sensorhub-core/.../api/command`, `.../impl/command` |
| Processing | [subsystems/processing.md](subsystems/processing.md) | `sensorhub-core/.../api/processing`, `.../impl/processing` |
| Security | [subsystems/security.md](subsystems/security.md) | `sensorhub-core/.../api/security`, `.../impl/security` |
| Comms & network | [subsystems/comms-network.md](subsystems/comms-network.md) | `sensorhub-core/.../api/comm`, `.../impl/comm` |
| H2 datastore | [subsystems/datastore-h2.md](subsystems/datastore-h2.md) | `sensorhub-datastore-h2` |
| Connected Systems API service | [subsystems/service-consys.md](subsystems/service-consys.md) | `sensorhub-service-consys` |
| SWE services (SOS / SPS) | [subsystems/service-swe.md](subsystems/service-swe.md) | `sensorhub-service-swe` |
| Admin web UI | [subsystems/webui.md](subsystems/webui.md) | `sensorhub-webui-core` |
| Kryo serialization | [subsystems/kryo-serialization.md](subsystems/kryo-serialization.md) | `sensorhub-utils-kryo` |
| OGC libraries (overview only) | [subsystems/lib-ogc.md](subsystems/lib-ogc.md) | `lib-ogc/*` |

## Entry points

- Hub object: [`SensorHub`](../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java) implements [`ISensorHub`](../../sensorhub-core/src/main/java/org/sensorhub/api/ISensorHub.java). Its `start()` method creates the module registry, event bus, database registry and system registry ([init block](../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L132-L136)).
- Package convention in `sensorhub-core`: interfaces live in `org.sensorhub.api.<area>` and implementations in `org.sensorhub.impl.<area>`.

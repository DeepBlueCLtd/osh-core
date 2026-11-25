# AGENTS.md

Guidance for coding agents (and humans) working in this repository. The format follows the
[AGENTS.md](https://agents.md) convention, which is tool-agnostic.

## What this repository is

`osh-core` is the core of OpenSensorHub (OSH): a Java framework for connecting sensors and
actuators and exposing their data through OGC standard services. This repository is a fork.
User-level documentation is maintained separately in the `osh-docs` repository.

## Navigating the code

**Start with the code map: [`docs/code-map/index.md`](docs/code-map/index.md).** It indexes
subsystems, key classes and data flows, with links to the source files. Read the relevant
subsystem page before searching the tree.

### Module map

Modules are declared in [`settings.gradle`](settings.gradle). Descriptions are taken from each
module's `build.gradle`. File counts were measured on 2026-11-25.

| Gradle project | Directory | Description (from build.gradle) | main / test `.java` |
|---|---|---|---|
| `sensorhub-core` | [`sensorhub-core`](sensorhub-core) | OSH Core APIs & Components | 440 / 32 |
| `sensorhub-core-osgi` | [`sensorhub-core-osgi`](sensorhub-core-osgi) | OSH OSGi Launcher | 2 / 2 |
| `sensorhub-datastore-h2` | [`sensorhub-datastore-h2`](sensorhub-datastore-h2) | OSH Datastore (H2) | 74 / 7 |
| `sensorhub-service-consys` | [`sensorhub-service-consys`](sensorhub-service-consys) | Connected Systems API | 157 / 38 |
| `sensorhub-service-swe` | [`sensorhub-service-swe`](sensorhub-service-swe) | OSH SWE Services | 78 / 13 |
| `sensorhub-utils-kryo` | [`sensorhub-utils-kryo`](sensorhub-utils-kryo) | Kryo Serialization | 21 / 5 |
| `sensorhub-webui-core` | [`sensorhub-webui-core`](sensorhub-webui-core) | OSH Admin UI (Vaadin) | 79 / 2 |
| `sensorhub-webui-widgetset` | [`sensorhub-webui-core/widgetset`](sensorhub-webui-core/widgetset) | Vaadin widgetset for the Admin UI | — |
| `swe-common-core` | [`lib-ogc/swe-common-core`](lib-ogc/swe-common-core) | SWE Common Core | 291 / 19 |
| `swe-common-om` | [`lib-ogc/swe-common-om`](lib-ogc/swe-common-om) | SWE O&M and GML Models | 100 / 7 |
| `sensorml-core` | [`lib-ogc/sensorml-core`](lib-ogc/sensorml-core) | SensorML Models | 167 / 9 |
| `ogc-services-common` | [`lib-ogc/ogc-services-common`](lib-ogc/ogc-services-common) | OGC Services Common | 184 / 1 |
| `ogc-services-swe` | [`lib-ogc/ogc-services-swe`](lib-ogc/ogc-services-swe) | OGC SWE Services Common | 32 / 0 |
| `ogc-services-sos` | [`lib-ogc/ogc-services-sos`](lib-ogc/ogc-services-sos) | OGC Sensor Observation Service (SOS) | 47 / 7 |
| `ogc-services-sps` | [`lib-ogc/ogc-services-sps`](lib-ogc/ogc-services-sps) | OGC Sensor Planning Service (SPS) | 81 / 6 |

`lib-ogc/sensorml-profile-gen` exists on disk, but it is not included in `settings.gradle` and
contains no Java sources.

In `sensorhub-core`, public interfaces are in `org.sensorhub.api.*` and implementations are in
`org.sensorhub.impl.*`, with matching sub-package names (for example `api/event` and
`impl/event`).

## Build and test

- **JDK 17.** CI uses Temurin 17 ([`.github/workflows/gradle_build.yml`](.github/workflows/gradle_build.yml)), and [`common.gradle`](common.gradle) sets source and target compatibility to 17.
- **Full build (what CI runs):**
  ```bash
  ./gradlew build
  ```
- **One module's tests:**
  ```bash
  ./gradlew :sensorhub-core:test
  ```
- **One test class:**
  ```bash
  ./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.event.TestEventBus'
  ```
- Shared test helpers (fake sensors, dummy modules) are in `sensorhub-core/src/testFixtures`.

## Documentation rules

The docs under `docs/code-map/` describe only what can be determined from the code. Follow the
[conventions](docs/code-map/index.md#conventions). In short:

1. **State facts, cite sources.** Link each claim to a source file (with a `#L` line anchor where
   useful) or name the class by its fully-qualified name in backticks.
2. **Do not invent rationale.** Mark anything not visible in code as **Inferred:**. Record
   contradictions (javadoc vs code, dead code) as **Open question**.
3. **Keep docs in step with code.** When you change behaviour, signatures or file locations in a
   subsystem, update its code-map page in the same commit.
4. **Run the reference check** before committing. It must pass:
   ```bash
   python3 docs/code-map/tools/check_refs.py
   ```
   It fails if a linked file is missing, a line anchor no longer points at the named symbol, or a
   referenced class no longer exists.
5. **Precedent is not endorsement.** "Where to make changes" sections list existing patterns. They
   are not design guidance.

## Legacy docs

`sensorhub-core/src/site/markdown/` and `sensorhub-service-swe/src/site/markdown/` contain older
Maven-site pages. Parts of them reference types that no longer exist in the code (for example
`ISensorDataInterface`, `IModuleDescriptor`). Prefer `docs/code-map/` and the source code.

# Comms & Network

> Status: draft page. Verified against source on 2026-11-25.
> Everything here is stated from the code. Items marked **Inferred:** are not directly
> visible in code; **Open question** items are unresolved observations.
> See [conventions](../index.md#conventions).

## Scope

Four separate pieces of code that deal with I/O outside the hub's in-memory APIs:

| Piece | Interfaces | Implementations in this repo |
|---|---|---|
| **Comm providers** (byte streams for drivers) | `org.sensorhub.api.comm.ICommProvider`, `org.sensorhub.api.comm.CommProviderConfig` | `org.sensorhub.impl.comm.TCPCommProvider`, `org.sensorhub.impl.comm.UDPCommProvider` |
| **Networks & device discovery** | `org.sensorhub.api.comm.INetworkManager`, `org.sensorhub.api.comm.ICommNetwork`, `org.sensorhub.api.comm.IDeviceScanner` | `org.sensorhub.impl.comm.NetworkManagerImpl` only (no `ICommNetwork` implementation) |
| **Message queues** | `org.sensorhub.api.comm.IMessageQueuePush` | `org.sensorhub.impl.comm.LocalMessageQueue` |
| **Embedded HTTP server & service modules** | `org.sensorhub.api.service.IHttpServer`, `org.sensorhub.api.service.IServiceModule` | `org.sensorhub.impl.service.HttpServer` (Jetty), `org.sensorhub.impl.service.AbstractHttpServiceModule` |

Plus connection helpers (`RobustIPConnection`, `RobustHTTPConnection`, `IPNetworkUtils`) and
plain protocol config classes (`TCPConfig`, `UDPConfig`, `HTTPConfig`, `UARTConfig`, `USBConfig`, `BluetoothConfig`).

Source folders:
- API: [`api/comm/`](../../../sensorhub-core/src/main/java/org/sensorhub/api/comm), [`api/service/`](../../../sensorhub-core/src/main/java/org/sensorhub/api/service)
- Implementation: [`impl/comm/`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm), [`impl/service/`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service)
- Module providers: [`META-INF/services/org.sensorhub.api.module.IModuleProvider`](../../../sensorhub-core/src/main/resources/META-INF/services/org.sensorhub.api.module.IModuleProvider) lists `TCPCommModuleDescriptor`, `UDPCommModuleDescriptor`, `LocalMessageQueueDescriptor`

## Key types

### Comm API (`org.sensorhub.api.comm`)

| Type | Kind | Role (from code / javadoc) |
|---|---|---|
| [`ICommProvider`](../../../sensorhub-core/src/main/java/org/sensorhub/api/comm/ICommProvider.java#L33) | interface, extends `IModule` | Javadoc: "communication providers giving access to an input stream for reading incoming data and an output stream for sending outgoing data". `getInputStream()`, `getOutputStream()` |
| [`CommProviderConfig<P>`](../../../sensorhub-core/src/main/java/org/sensorhub/api/comm/CommProviderConfig.java#L31) | config class | `ModuleConfig` with one field `protocol` of type `P` |
| [`ICommConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/api/comm/ICommConfig.java#L26) | tagging interface | Implemented by `IPConfig`, `UARTConfig`, `USBConfig`, `BluetoothConfig` |
| [`ICommNetwork`](../../../sensorhub-core/src/main/java/org/sensorhub/api/comm/ICommNetwork.java#L32) | interface, extends `IModule` | `getInterfaceName()`, `getNetworkType()`, `isOfType()`, `getDeviceScanner()`, `getAvailableNetworks()`. Enum `NetworkType` (IP, ETHERNET, WIFI, CELLULAR, BLUETOOTH, BLUETOOTH_LE, ZIGBEE, VPN, UNKNOWN) |
| [`INetworkManager`](../../../sensorhub-core/src/main/java/org/sensorhub/api/comm/INetworkManager.java#L22) | interface | `IModuleManager<ICommNetwork<?>>` plus `getLoadedModules(NetworkType)` |
| [`IDeviceScanner`](../../../sensorhub-core/src/main/java/org/sensorhub/api/comm/IDeviceScanner.java#L28) | interface | `startScan(callback[, idRegex])`, `stopScan()`, `isScanning()` |
| [`IDeviceScanCallback`](../../../sensorhub-core/src/main/java/org/sensorhub/api/comm/IDeviceScanCallback.java#L26), [`IDeviceInfo`](../../../sensorhub-core/src/main/java/org/sensorhub/api/comm/IDeviceInfo.java#L18), [`INetworkInfo`](../../../sensorhub-core/src/main/java/org/sensorhub/api/comm/INetworkInfo.java#L20) | interfaces | Scan results and network descriptions |
| [`IMessageQueuePush`](../../../sensorhub-core/src/main/java/org/sensorhub/api/comm/IMessageQueuePush.java#L30) | interface, extends `ISubModule` | `publish(payload)`, `publish(attrs, payload)`, `registerListener(MessageListener)`; `MessageListener.receive(Map<String,String>, byte[])` |
| [`MessageQueueConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/api/comm/MessageQueueConfig.java#L7) | abstract config | `topicName`, `enablePublish`, `enableSubscribe` |
| [`NetworkConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/api/comm/NetworkConfig.java#L20) | abstract config | Empty; used by the admin UI to list network modules |
| `DeviceScanEvent`, `INetworkProvider` | class / interface | **No references elsewhere in this repo** (searched all `.java` files) |

### Comm implementation (`org.sensorhub.impl.comm`)

| Type | Role |
|---|---|
| [`TCPCommProvider`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/TCPCommProvider.java#L41) | Opens a `Socket` (or `SSLSocket` when `enableTLS`) to `remoteHost:remotePort` in `doStart` |
| [`TCPCommProviderConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/TCPCommProviderConfig.java#L21) | `protocol = new TCPConfig()`, `connection = new RobustIPConnectionConfig()` |
| [`UDPCommProvider`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/UDPCommProvider.java#L41) | `DatagramChannel` bound to `localPort` and connected to `remoteHost:remotePort` |
| [`NetworkManagerImpl`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/NetworkManagerImpl.java#L37) | Filters `ModuleRegistry.getLoadedModules()` by `instanceof ICommNetwork` |
| [`LocalMessageQueue`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/LocalMessageQueue.java#L38) | `IMessageQueuePush` over the hub event bus. Javadoc: "Local message queue implementation based on Java Publisher." |
| [`IPConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/IPConfig.java#L34) → [`TCPConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/TCPConfig.java#L32) → [`HTTPConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/HTTPConfig.java#L28); [`UDPConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/UDPConfig.java#L29) | IP protocol configs. `HTTPConfig` is used by `SOSTClientConfig`, `SWEVirtualSensorConfig`, `ConSysApiClientConfig` |
| [`RobustIPConnection`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/RobustIPConnection.java#L31), [`RobustHTTPConnection`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/RobustHTTPConnection.java#L33) | Extend `org.sensorhub.impl.module.RobustConnection` (retry loop, see [Module lifecycle](module-lifecycle.md)) with DNS / reachability / HTTP checks |
| [`IPNetworkUtils`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/IPNetworkUtils.java#L45) | `isNetworkUp()`, `resolveAll/resolveHost(host, timeout)` (DNS on a separate thread), `isHostReachable(host[, port], timeout)` |
| `UARTConfig`, `USBConfig`, `BluetoothConfig` | Config POJOs. **No references elsewhere in this repo**; no providers for them exist here |

### Service API and HTTP server (`org.sensorhub.api.service`, `org.sensorhub.impl.service`)

| Type | Role |
|---|---|
| [`IHttpServer`](../../../sensorhub-core/src/main/java/org/sensorhub/api/service/IHttpServer.java#L33) | `deployServlet`, `undeployServlet`, `addServletSecurity`, `getServerBaseUrl`, `getServletsBaseUrl`, `getPublicEndpointUrl`, `isAuthEnabled` |
| [`HttpServer`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/HttpServer.java#L73) | The only `IHttpServer`. Javadoc: "Wrapper module for the HTTP server engine (Jetty for now)" |
| [`HttpServerConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/HttpServerConfig.java#L30) | Default module ID `HTTP_SERVER_0`, `autoStart = true` (see [Configuration](#configuration)) |
| [`AbstractHttpServiceModule`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/AbstractHttpServiceModule.java#L39) | Javadoc: "automatically handles deployments and re-deployments when the embedded HTTP server stops and starts." Extended by `SWEService`, `ConSysApiService`, `AdminUIModule` |
| [`IServiceModule`](../../../sensorhub-core/src/main/java/org/sensorhub/api/service/IServiceModule.java#L29), [`ServiceConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/api/service/ServiceConfig.java#L28), [`HttpServiceConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/api/service/HttpServiceConfig.java#L29) | Marker interface / base configs. `HttpServiceConfig.endPoint` is `@Required`. `OGCServiceConfig` extends it |
| [`WebSocketOutputStream`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/WebSocketOutputStream.java#L36), `WebSocketUtils` | Buffered binary output to a Jetty websocket `Session`; shared log/close helpers. Used by SOS, SPS and ConSys websocket code |
| `OshLoginService`, `HttpLogoutWrapper` | HTTP authentication; see [Security](security.md) |
| `CustomFormatConfig` | `mimeType` + `className`; used only by `ConSysApiServiceConfig` |
| `org.sensorhub.api.service.ServiceException` | **No references elsewhere in this repo** |

## How it works

### Comm providers

- A provider is a normal module: `init(config)` then `start()` → `doStart()` opens the link; callers then read `getInputStream()` / `getOutputStream()`.
- [`TCPCommProvider.doStart`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/TCPCommProvider.java#L70) loops: resolve host, connect (plain socket with `connection.connectTimeout`, or `SSLSocketFactory.getDefault()` + `startHandshake()`), and on `IOException` retries until `++count >= connection.reconnectAttempts`.
- [`UDPCommProvider.doStart`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/UDPCommProvider.java#L65): when `remotePort <= 0` it first blocks on a `DatagramSocket.receive` to learn the sender's port (code comment: "use port the first UDP packet was sent from").
- No driver in this repo consumes an `ICommProvider`. The admin UI registers [`CommProviderConfigForm`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/CommProviderConfigForm.java#L26) for any `CommProviderConfig` property. **Inferred:** drivers in other repositories hold a `CommProviderConfig` in their config and load the provider themselves.

### Network manager and discovery

- `SensorHub.start()` creates [`new NetworkManagerImpl(this)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L140), exposed by [`ISensorHub.getNetworkManager()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/ISensorHub.java#L58).
- [`getLoadedModules(NetworkType)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/NetworkManagerImpl.java#L65) scans all loaded modules each call and keeps `ICommNetwork`s whose `isOfType(netType)` is true.
- Callers: `GenericConfigForm` and `NetworkAddressSelectionPopup` (address pickers for fields annotated `@AddressType`, e.g. `IPConfig.remoteHost`), and `NetworkAdminPanel`, which calls `getAvailableNetworks()` and `getDeviceScanner().startScan(...)`.

### Message queue (`LocalMessageQueue`)

- [`start()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/LocalMessageQueue.java#L110): if `topicName` is set, gets `eventBus.getPublisher(topicName)` and subscribes to `LocalMqMessage` events on the same topic, requesting one event at a time.
- [`publish(attrs, payload)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/LocalMessageQueue.java#L84) wraps the payload in a `LocalMqMessage` event and publishes it on the bus; if there is no publisher (no topic, or not started) it calls the listeners directly on the caller's thread.
- Bus delivery semantics (async, drop on full buffer) are those of the [Event bus](event-bus.md).

### Embedded HTTP server

[`HttpServer.doStart`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/HttpServer.java#L114) builds a Jetty `Server` with a mutable `HandlerCollection`:
1. HTTP connector if `httpPort > 0`; HTTPS connector (`SslContextFactory.Server`) if `httpsPort > 0`. Idle timeout 300 000 ms; server version header off.
2. Static files: `ResourceHandler` at `staticDocsRootUrl` serving `staticDocsRootDir`.
3. Servlets: one `ServletContextHandler` (sessions on) at `servletsRootUrl`, with an optional security handler (see [Security](security.md#authentication-inbound-http)), an optional `CrossOriginFilter`, and a built-in `/test` servlet returning [`TEST_MSG`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/HttpServer.java#L87).
4. Optional Jetty XML file (`xmlConfigFile`) applied with IDs `osh-server`, `osh-handlers`, `osh-http`, `osh-https`, `osh-static`, `osh-servlets`.

Servlet registration:
- [`deployServlet(servlet, initParams, paths...)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/HttpServer.java#L334) requires the server to be started, then adds a `ServletHolder` and a `ServletMapping` to the live handler.
- [`undeployServlet`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/HttpServer.java#L352) rebuilds the servlet and mapping arrays without the holder whose servlet is `==` the argument.
- URL helpers: [`getServerBaseUrl()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/HttpServer.java#L418) returns `proxyBaseUrl` if set, else `http://localhost[:port]` or `https://localhost[:port]`.

### How service modules attach

```
AbstractHttpServiceModule.start()
  → httpServer = moduleRegistry.getModuleByType(IHttpServer.class)   (error if none loaded)
  → httpServer.registerListener(this)
        AbstractModule.registerListener sends the current state immediately if not LOADED
  → handleEvent(ModuleEvent from httpServer)
        STARTED  → doStart(); setState(STARTED)     (subclass deploys servlets here)
        STOPPED  → doStop();  setState(STOPPED)
        UNLOADED → stop()
```

- [`start()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/AbstractHttpServiceModule.java#L45) overrides `AbstractModule.start()`; the module's own `doStart` runs from [`handleEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/AbstractHttpServiceModule.java#L75). The immediate state notification is in [`AbstractModule.registerListener`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L666-L676).
- Deploy call sites:

| Module | Paths | Security |
|---|---|---|
| `SWEService` (SOS, SPS) [`deploy()`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/SWEService.java#L127) | `config.endPoint` | `addServletSecurity(endPoint, config.security.requireAuth)` |
| `ConSysApiService` [`deploy()`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiService.java#L315) | `config.endPoint + "/*"` | `addServletSecurity(..., config.security.requireAuth)` |
| `AdminUIModule` [`doStart()`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIModule.java#L149) | `/admin/*`, `/VAADIN/*`; with landing page also `/*` | `requireAuth = true` on each |

## Configuration

| Class | Field | Default |
|---|---|---|
| `HttpServerConfig` | `httpPort` / `httpsPort` | `8080` / `0` (0 disables) |
| | `staticDocsRootUrl` / `staticDocsRootDir` | `/` / `web` |
| | `servletsRootUrl` | `/sensorhub` |
| | `proxyBaseUrl` | `null` |
| | `authMethod` | `NONE` |
| | `enableCORS` | `true` (methods `GET, POST, PUT, DELETE, PATCH, OPTIONS`) |
| | `xmlConfigFile`, key/trust store fields | see [Security](security.md#configuration) |
| `RobustConnectionConfig` (base of `RobustIPConnectionConfig`) | `connectTimeout`, `reconnectPeriod`, `reconnectAttempts` | `3000` ms, `10000` ms, `0` |
| `RobustIPConnectionConfig` | `checkReachability` | `true` |
| `UDPConfig` | `remotePort` | `PORT_AUTO` (0) |
| `IPConfig` | `localAddress` | `"AUTO"` |

## Observed behaviours to be aware of

1. **`TCPCommProvider` retry settings are only partly applied.** With the default `reconnectAttempts = 0`, and with any negative value (documented in `RobustConnectionConfig` as "no limit"), the loop stops after the first failure because `++count >= reconnectAttempts` is already true. `reconnectPeriod` is not read, so retries run back to back. The TLS branch does not apply `connectTimeout`.
2. **Unused config fields in the providers.** `IPConfig.localAddress` is not read by either provider (UDP binds `new InetSocketAddress(localPort)`); `TCPConfig.user` / `password` are not read by `TCPCommProvider`.
3. **`MessageQueueConfig.enablePublish` / `enableSubscribe` are not read by `LocalMessageQueue`**; it always publishes and subscribes when `topicName` is set.
4. **No `ICommNetwork` implementation in this repo**, so `NetworkManagerImpl` always returns empty lists here. `ICommNetwork.getAvailableNetworks()` carries a "TODO: move to INetworkManager".
5. **Servlet deployment depends on `servletsRootUrl`.** The `ServletContextHandler` is created only when it is non-null; `deployServlet` dereferences `servletHandler` without a null check.
6. **`undeployServlet` matches mappings with `String.contains`** ([line 381](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/HttpServer.java#L379-L382)) rather than equality, and constraint mappings added by `addServletSecurity` are never removed.
7. **`addServletSecurity` is a no-op when `authMethod` is `NONE`**, so a service's `requireAuth = true` has no effect unless the HTTP server has authentication on.
8. **`IPNetworkUtils.resolveAll` returns an empty array when interrupted** ([line 124](../../../sensorhub-core/src/main/java/org/sensorhub/impl/comm/IPNetworkUtils.java#L121-L125)); `resolveHost` then indexes `[0]`. The per-call executor is not shut down in the method.
9. **`RobustIPConnection.tryConnect(host)` javadoc says "ping host with ICMP packets"**; the code calls `isHostReachable`, i.e. `InetAddress.isReachable`, and only when `checkReachability` is true.
10. The start log line always prints `config.httpPort`, also when only HTTPS is enabled.

## Where to make changes (by precedent in the code)

| Task | Existing pattern to follow |
|---|---|
| Add a transport for drivers | Implement `ICommProvider` as an `AbstractModule` with a `CommProviderConfig<YourProtocolConfig>` subclass and an `IModuleProvider` descriptor listed in `META-INF/services`, as `TCPCommProvider` / `TCPCommModuleDescriptor` |
| Add a message queue backend | Implement `IMessageQueuePush` as an `AbstractSubModule` with a `MessageQueueConfig` subclass, as `LocalMessageQueue` |
| Add an HTTP service | Extend `AbstractHttpServiceModule`; in `doStart` call `httpServer.deployServlet(...)` and `addServletSecurity(...)`; undeploy in `doStop`, as `ConSysApiService` |
| Change Jetty setup | `HttpServer.doStart`, or an external `xmlConfigFile` using the published bean IDs |
| Reconnect to a remote IP service | Subclass `RobustIPConnection` and implement `tryConnect()`, as in `SOSTClient` |

## Tests

| Test | Covers |
|---|---|
| [`TestHttpServer`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/service/TestHttpServer.java) | Server start, hot servlet deployment, `/test` servlet with `NONE`/`BASIC`/`DIGEST` |
| [`TestIpNetworkUtils`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/comm/TestIpNetworkUtils.java) | Resolving a valid host, pinging localhost (invalid-host tests are commented out) |
| [`TestTcpCommProvider`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/comm/TestTcpCommProvider.java) | A `main()` method connecting to a hard-coded remote IP; it has no JUnit `@Test` methods |

```bash
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.service.TestHttpServer'
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.comm.TestIpNetworkUtils'
```

No tests exist for `UDPCommProvider`, `LocalMessageQueue`, `NetworkManagerImpl` or `AbstractHttpServiceModule`.

## Related

- [Code map index](../index.md)
- [Security](security.md) (HTTP authentication, servlet constraints)
- [Event bus](event-bus.md) (used by `LocalMessageQueue`)
- [Module lifecycle](module-lifecycle.md) (`AbstractModule`, `RobustConnection`), [Sensor drivers](sensor-drivers.md)
- [Connected Systems API service](service-consys.md), [SWE services](service-swe.md), [Admin web UI](webui.md)

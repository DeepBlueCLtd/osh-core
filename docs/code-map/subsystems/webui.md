# Admin Web UI

> Status: draft page. Verified against source on 2026-11-25.
> Everything here is stated from the code. Items marked **Inferred:** are not directly
> visible in code; **Open question** items are unresolved observations.
> See [conventions](../index.md#conventions).

## Scope

Browser-based administration UI for the hub, built with Vaadin. Two Gradle projects:

| Project | Directory | Content |
|---|---|---|
| `sensorhub-webui-core` | [`sensorhub-webui-core`](../../../sensorhub-webui-core) | Module, servlets, `AdminUI`, panels and forms in `org.sensorhub.ui` (+ `api`, `data`, `filter`, `table` sub-packages) |
| `sensorhub-webui-widgetset` | [`sensorhub-webui-core/widgetset`](../../../sensorhub-webui-core/widgetset) | Vaadin widgetset org.sensorhub.ui.SensorHubWidgetSet (GWT module) and two JavaScript chart components |

**Vaadin version:** [`build.gradle`](../../../sensorhub-webui-core/build.gradle) sets `ext.vaadinVersion = '8.14.3'` on all projects (a commented line keeps `7.7.12`). Dependencies include `vaadin-compatibility-server`/`-client`; 46 of the main source files import `com.vaadin.v7.*` (compatibility layer: `Table`, `TreeTable`, `FieldGroup`, `Property`, ...). The widgetset inherits com.vaadin.v7.Vaadin7WidgetSet ([`SensorHubWidgetSet.gwt.xml`](../../../sensorhub-webui-core/widgetset/src/main/resources/org/sensorhub/ui/SensorHubWidgetSet.gwt.xml)).

Build tasks in [`widgetset/build.gradle`](../../../sensorhub-webui-core/widgetset/build.gradle): `compileWidgetset` (GWT `WidgetsetCompiler`) and `compileTheme` (`SassCompiler` on `VAADIN/themes/sensorhub/styles.scss`); `processResources` depends on both.

Module registration: [`META-INF/services/org.sensorhub.api.module.IModuleProvider`](../../../sensorhub-webui-core/src/main/resources/META-INF/services/org.sensorhub.api.module.IModuleProvider) → `AdminUIDescriptor`. OSGi activator: `org.sensorhub.ui.Activator`.

## Key types

### Module, servlets, entry point

| Type | Role |
|---|---|
| [`AdminUIModule`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIModule.java#L53) | `AbstractHttpServiceModule<AdminUIConfig>`. Deploys servlets; holds the config-class → form/panel class maps; `generatePanel()`, `generateForm()` |
| [`AdminUIConfig`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIConfig.java#L23) | `widgetSet` (default org.sensorhub.ui.SensorHubWidgetSet), `bundleRepoUrls`, `customPanels`, `customForms`, `deploymentName`, `enableLandingPage` |
| [`CustomUIConfig`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/CustomUIConfig.java#L28) | Pair `configClass` → `uiClass` (both fully-qualified names) |
| [`AdminUIServlet`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIServlet.java#L28) | `VaadinServlet`; sets current user and checks `admin_access` on every request |
| [`AdminUI`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUI.java#L108) | The Vaadin `UI`. `@Theme("sensorhub")`, `@Push(value=PushMode.MANUAL, transport=Transport.LONG_POLLING)` ([annotations](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUI.java#L105-L106)) |
| [`LandingUI`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/LandingUI.java#L33), `LandingServlet`, `VaadinResourcesServlet` | Optional landing page at `/*` (see [Servlet deployment](#servlet-deployment)) |
| [`AdminUISecurity`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUISecurity.java#L22) | `ModuleSecurity` with root `webadmin` and permissions `view`, `shutdown`, `restart`, `save_config`, `add`, `remove`, `init`, `start`, `stop`, `update_config` |

### Extension interfaces (`org.sensorhub.ui.api`)

| Type | Role |
|---|---|
| [`IModuleAdminPanel`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/api/IModuleAdminPanel.java#L32) | Javadoc: "Interface for all UI panels used to interact with modules". Single method `build(MyBeanItem<ModuleConfig>, ModuleType)` |
| [`IModuleConfigForm`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/api/IModuleConfigForm.java#L38) | Form builder: `build(...)` (two overloads), `commit()`, `getPossibleModuleTypes`, `getPossibleTypes`, `getPossibleValues`, parent/sub-form accessors |
| `UIConstants` | Shared style names and messages |

### Panels and forms (`org.sensorhub.ui`)

| Type | Registered for | Notes |
|---|---|---|
| [`DefaultModulePanel`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/DefaultModulePanel.java#L50) | fallback | Status/error labels, config form (+ README tab), "Apply Changes" button; `IEventListener` on the module |
| `DataSourceAdminPanel` → `SensorAdminPanel`, `ProcessAdminPanel` | `SensorConfig`, `ProcessConfig` | Outputs/control inputs; `ProcessAdminPanel` uses `ProcessFlowDiagram` (JointJS, `VAADIN/js`) |
| `DatabaseAdminPanel` | `IObsSystemDatabase` (matched by module class) | Uses `DatabaseStreamPanel` (chart.js `Chart` from widgetset) |
| `NetworkAdminPanel` | `NetworkConfig` | Network scan panel |
| `SOSAdminPanel`, `SPSAdminPanel` | `SOSServiceConfig`, `SPSServiceConfig` | Links to service endpoints |
| [`GenericConfigForm`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/GenericConfigForm.java#L113) | fallback | Reflection-driven form (see [below](#how-config-forms-are-generated)) |
| `HttpServerConfigForm`, `SystemDriverDatabaseConfigForm`, `CommProviderConfigForm`, `BasicSecurityConfigForm`, `SOSConfigForm`, `SPSConfigForm`, `filter.DatabaseViewConfigForm`, `filter.DatabaseFilterConfigForm` | config classes listed in [`setConfiguration`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIModule.java#L75) | Subclasses of `GenericConfigForm` (filter forms build `FilterTree`s) |
| `SWECommonForm`, `SWEControlForm`, `SWEParamForm`, `SWEEditForm` | — | Render SWE Common components; `SWEControlForm` sends commands |
| `*Popup` classes | — | Selection dialogs (module type, module instance, system, address, value entry) |
| `table.PagedTable`, `table.LazyLoadingObsContainer` | — | Paged observation tables |

### Bean binding (`org.sensorhub.ui.data`)

| Type | Role |
|---|---|
| [`MyBeanItem`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/data/MyBeanItem.java#L46) | Javadoc: "Custom bean item to also generate properties for public fields". Vaadin 7 `Item` over a config object |
| [`BaseProperty`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/data/BaseProperty.java#L32) | Reads `@DisplayInfo` and its nested annotations from the `java.lang.reflect.Field` |
| `FieldProperty`, `ComplexProperty`, `ContainerProperty`, `MapProperty` | Scalar, nested object, collection, map properties |
| `MyBeanItemContainer` | Container for collection/map elements |

## How it works

### Servlet deployment

[`AdminUIModule.doStart()`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIModule.java#L149):
- Init params: `UI` = `AdminUI`, `widgetset` = `config.widgetSet`, `productionMode=true`, `heartbeatInterval=10`.
- Code comment: "HACK: we have to disable std err ..." — `System.err` is replaced by a no-op stream while servlets deploy.
- `enableLandingPage = false`: `AdminUIServlet` at `/admin/*` and `/VAADIN/*`.
- `enableLandingPage = true`: `VaadinResourcesServlet` at `/VAADIN/*`, `AdminUIServlet` at `/admin/*`, `LandingServlet` at `/*`; `addServletSecurity("/*", true)`; Jetty error pages for 400/403/404 ([lines 184–199](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIModule.java#L184-L199)).
- Always: [`addServletSecurity`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIModule.java#L209-L210) for `/admin/*` and `/VAADIN/*` with auth required.
- The module instance is passed to the UI through the servlet-context attribute `module_instance`; [`AdminUI.init()`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUI.java#L142) reads it.

### AdminUI layout

`init()` builds a split panel: header, toolbar (Shutdown, Logout, Save, add-module/download buttons), and an `Accordion` with tabs Sensors, Databases, Processing, Services, Clients, Network, Security. Each tab is a `TreeTable` of modules whose config is assignable to `SensorConfig`, `DatabaseConfig`, `ProcessConfig`, `ServiceConfig`, `ClientConfig`, (network), `SecurityModuleConfig`. Selecting a module calls [`openModuleInfo`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUI.java#L1241) → `adminModule.generatePanel(module)` → `panel.build(beanItem, module)`.

Toolbar actions call `hub.stop(false, true)` then `System.exit(0)` (Shutdown) and `moduleRegistry.saveModulesConfiguration()` (Save). Module context-menu actions (add, remove, start, stop, restart, force init) each check the matching permission first.

### Extension mechanism: custom panels and forms per type

[`AdminUIModule.setConfiguration()`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIModule.java#L75) fills two maps keyed by canonical class name:
- [`customForms`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIModule.java#L65): built-in entries (`HttpServerConfig`, `SystemDriverDatabaseConfig`, `CommProviderConfig`, `BasicSecurityRealmConfig.UserConfig`/`RoleConfig`, `SOSServiceConfig`, `SPSServiceConfig`, `ObsSystemDatabaseViewConfig`, `SystemFilter`, `DataStreamFilter`, `CommandStreamFilter`, `ObsFilter`, `CommandFilter`), then each `config.customForms` entry, loaded with `Class.forName(uiClass)`.
- [`customPanels`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIModule.java#L66): built-in entries (`SensorConfig`, `ProcessConfig`, `IObsSystemDatabase`, `NetworkConfig`, `SOSServiceConfig`, `SPSServiceConfig`), then `config.customPanels`.

Lookup:

| Method | Algorithm | Fallback |
|---|---|---|
| [`generatePanel(module)`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIModule.java#L239) | 1. walk the config class and its superclasses, look up by canonical name; 2. if none, for every map key do `Class.forName(key).isAssignableFrom(module.getClass())` (last match wins) | `DefaultModulePanel` |
| [`generateForm(clazz)`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIModule.java#L282) | walk the class and its superclasses | `GenericConfigForm` |

`GenericConfigForm` calls `getParentModule().generateForm(...)` for every nested object, collection element and tab ([`buildSubForm`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/GenericConfigForm.java#L633)), so custom forms apply at any nesting depth. `getParentModule()` resolves the module through `UI.getCurrent()` ([source](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/GenericConfigForm.java#L1430-L1433)).

### How config forms are generated

1. [`MyBeanItem.addFieldProperties`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/data/MyBeanItem.java#L83) iterates **public** non-static, non-transient fields of the config object (including superclasses):
   - simple types / enums → `FieldProperty`;
   - `Collection` → `ContainerProperty` (element type from generic parameter);
   - `Map` → `MapProperty` (value type from generic parameter);
   - arrays → skipped (empty branch);
   - other objects → `ComplexProperty` wrapping a nested `MyBeanItem`.
   Protected/private fields with getters/setters are added as `MethodProperty` (`addMethodProperties`).
2. [`GenericConfigForm.build(...)`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/GenericConfigForm.java#L147) binds each property with a Vaadin 7 `FieldGroup`: containers → list/table/tabs, complex → sub-form, scalars → [`buildAndBindField`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/GenericConfigForm.java#L292).
3. Label = `@DisplayInfo.label` if non-empty, else `DisplayUtils.getPrettyName(propId)`; tooltip = `@DisplayInfo.desc` ([`BaseProperty.getLabel()`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/data/BaseProperty.java#L43)).

Annotations (`org.sensorhub.api.config.DisplayInfo` and nested types) and how the form uses them:

| Annotation | Effect in `GenericConfigForm` |
|---|---|
| `@DisplayInfo(label, desc)` | Caption and description |
| `@FieldType(MODULE_ID)` + `@ModuleType` | Module picker restricted to the module type ([switch](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/GenericConfigForm.java#L377-L402)) |
| `@FieldType(SYSTEM_UID)` | System picker (also for lists of UIDs) |
| `@FieldType(REMOTE_ADDRESS)` + `@AddressType` | Address picker (network scan) |
| `@FieldType(PASSWORD)` | Masked field |
| `@FieldType(TABLE)` | Collection rendered as a table |
| `@Required` | Validator for `String` (length ≥ 1) and `int`/`Integer` only |
| `@ValueRange(min, max)` | `IntegerRangeValidator` (values cast to `int`) |
| `@IdField` (on type) | `MyBeanItem.getItemId()` uses that field as item ID |

### Event bus usage

- `AdminUI.init()` [subscribes](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUI.java#L292) to the module event group `ModuleRegistry.EVENT_GROUP_ID` with `consume(this::handleEvent)` (no back-pressure; see [Event bus](event-bus.md#module-events)). The subscription is cancelled in [`detach()`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUI.java#L1497).
- [`AdminUI.handleEvent`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUI.java#L1261) handles `ModuleEvent` types `LOADED`, `DELETED`, `CONFIG_CHANGED`, `STATE_CHANGED`, `ERROR` by updating the module `TreeTable` inside `access(...)` followed by `push()` (manual push mode).
- `DefaultModulePanel` registers itself as a per-object listener on the displayed module in [attach/detach](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/DefaultModulePanel.java#L261-L272); [`handleEvent`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/DefaultModulePanel.java#L277) refreshes status/error via `getUI().access(...)` + `push()`.
- `SWEControlForm` and `DatabaseAdminPanel` create `SystemDatabaseTransactionHandler(eventBus, db)` to send commands and delete systems.

### Security

- `AdminUISecurity` is created with `enable = true` in `setConfiguration` ([line 80](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIModule.java#L80)); [`isAccessControlEnabled()`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUISecurity.java#L63) additionally requires `httpServer.isAuthEnabled()`.
- [`AdminUIServlet.service()`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIServlet.java#L42) sets the user from `getUserPrincipal()`, checks `admin_access` (the root permission), returns 403 on `SecurityException`, clears the user in `finally`.
- `AdminUI.init()` checks `admin_access` again ([line 163](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUI.java#L163)); actions check specific permissions, e.g. "Apply Changes" checks `module_update` ([source](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/DefaultModulePanel.java#L115)) then calls `ModuleRegistry.updateModuleConfigAsync`.
- See [Security](security.md) for `ModuleSecurity` and permissions.

## Observed behaviours to be aware of

1. **Two permissions share the name `restart`.** `osh_restart` and `module_restart` are both `new ItemPermission(rootPerm, "restart", ...)` ([line 45](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUISecurity.java#L45), [line 56](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUISecurity.java#L56)). `AbstractPermission` stores children in a map keyed by name ([`getChildren().put`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/AbstractPermission.java#L54)), so the second replaces the first. `osh_restart` and `admin_view` are not referenced anywhere else.
2. **One bad custom form/panel entry stops the rest.** The `customForms` / `customPanels` loops are each inside a single `try`; an exception from `Class.forName` logs an error and skips all remaining entries. **Inferred:** `Class.forName` uses this bundle's classloader, unlike `ModuleRegistry.findClass` used elsewhere (e.g. SOS custom formats).
3. **Module-class panel lookup is order dependent.** The second pass in `generatePanel` iterates a `HashMap` and keeps the last assignable match.
4. **Several `@FieldType` values and `@TextInfo` are not used by the form.** `LABEL`, `TEXT`, `LOCAL_ADDRESS`, `FILESYSTEM_PATH` fall into `default:`; `BaseProperty.getTextInfo()` has no callers.
5. **Array config fields are not shown** (empty branch in `addFieldProperties`, [line 123](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/data/MyBeanItem.java#L123)).
6. **`AdminUIModule implements IEventListener`** but declares no `handleEvent`; it inherits `AbstractHttpServiceModule.handleEvent` ([source](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/AbstractHttpServiceModule.java#L75)).
7. **`PlotlyChart` is unused.** The widgetset class `org.sensorhub.ui.plotly.PlotlyChart` has no references outside the widgetset; only `org.sensorhub.ui.chartjs.Chart` is used (by `DatabaseStreamPanel`).
8. **Landing servlet production mode.** `LandingServlet` is annotated `@VaadinServletConfiguration(..., productionMode = false)` while `doStart` passes `productionMode=true` init params.

## Where to make changes (by precedent in the code)

| Task | Existing pattern |
|---|---|
| Custom panel for a module type | Implement `IModuleAdminPanel` (usually extend `DefaultModulePanel`), then add a built-in entry in `AdminUIModule.setConfiguration` (like `SOSAdminPanel`) or a `CustomUIConfig` in `AdminUIConfig.customPanels` |
| Custom config form for a config class | Extend `GenericConfigForm` (override e.g. `isFieldVisible`, `getPossibleValues`, `getPossibleTypes`), register like `SOSConfigForm` or via `AdminUIConfig.customForms` (as `TestWebUI` does) |
| Change how a config field is rendered | Annotate the config field with `@DisplayInfo` / `@FieldType` / `@Required` / `@ValueRange`; rendering is in `GenericConfigForm.buildAndBindField` |
| React to module events in the UI | `AdminUI.handleEvent` or a panel's `handleEvent`, always via `access(...)` + `push()` |
| New JavaScript component | `AbstractJavaScriptComponent` + `JavaScriptComponentState`, as `ProcessFlowDiagram` or widgetset `Chart` |

## Tests

| Test | What it is |
|---|---|
| [`TestWebUI`](../../../sensorhub-webui-core/src/test/java/org/sensorhub/ui/TestWebUI.java) | Manual harness with a `main()` that starts a hub with HTTP server, admin UI and dummy modules, then sleeps one hour. No `@Test` methods |
| [`TestServiceConfig`](../../../sensorhub-webui-core/src/test/java/org/sensorhub/ui/TestServiceConfig.java) | Config class used by `TestWebUI` |

```bash
./gradlew :sensorhub-webui-core:test --tests 'org.sensorhub.ui.TestWebUI'
```

**Inferred:** this command finds no JUnit tests to run; the harness is meant to be launched through `TestWebUI.main()`.

## Related

- [Code map index](../index.md)
- [Event bus](event-bus.md) — module event group consumed by `AdminUI`
- [Module lifecycle & registry](module-lifecycle.md) — `ModuleRegistry`, `ModuleEvent`, config classes
- [Security](security.md) — `ModuleSecurity`, `ItemPermission`
- [SWE services](service-swe.md) — `SOSServiceConfig` / `SPSServiceConfig` with custom panels and forms
- [Databases & datastores](databases.md) — filters and DB views edited by the filter forms

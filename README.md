# Send your Home Assistant metrics to Datadog

[![Tests](https://github.com/rapdev-io/ha-datadog-metrics/actions/workflows/test.yml/badge.svg)](https://github.com/rapdev-io/ha-datadog-metrics/actions/workflows/test.yml) [![HACS Validate](https://github.com/rapdev-io/ha-datadog-metrics/actions/workflows/validate.yml/badge.svg)](https://github.com/rapdev-io/ha-datadog-metrics/actions/workflows/validate.yml) 

<a href="https://www.rapdev.io"><img alt="by rapdev.io" src="https://brands.home-assistant.io/rapdev/icon.png" align="left" height="48" width="48" ></a> <img alt="for Datadog" src="https://brands.home-assistant.io/datadog/icon.png" align="left" height="48" width="48" >

This component exposes a Home Assistant [Service](https://developers.home-assistant.io/docs/dev_101_services) that can be used as a custom [Action Target](https://www.home-assistant.io/docs/automation/action/) to send any metrics from Homeassistant to Datadog.

## Install

* [prereq] Have [HACS installed](https://www.hacs.xyz/docs/use/download/download/)
* Install via HACS:
  * HACS > `...` in top right corner > Custom Repositories, add this repo:
  ```
  https://github.com/rapdev-io/ha-datadog-metrics/
  ```
  * Choose type: `Integration`. Click `Add`.
* Settings > Devices & services > Add Integration > add "Datadog Metrics"
* Customize any settings, if desired, then `Submit`

## What about HA's [built-in Datadog integration](https://www.home-assistant.io/integrations/datadog/)?

Both this component and the built-in integration are used to send custom metrics to datadog. However, the built-in integration was **last updated in 2017**, when the HA platform was considerably different.

The built-in integration provides:
* No control over which metrics to send. It sends everything, even internal HA events. This is a LOT of metrics:
  * Every state change event
  * Every _numeric attribute_ on every state change event too
* No control over tags: you only get the `entity_id`
* 100% of logbook entries are also sent as custom events
* Only `state_changed` events are listened to

This component gives you the power to pick and choose what you want to send to datadog, and format it / tag it the way you want. Anywhere you can use an Action, you can use this.

## Usage

The most common usage is to set up an Entity-based `state_changed` automation:

```yaml
- id: '987654321'
  alias: My thermometer automation
  description: 'Push all temperature updates from my thermometers to datadog'
  triggers:
  - trigger: state
    entity_id:
    - sensor.bedroom_ewelink_snzb_02p_temperature
    - ...
  conditions: []
  actions:
  - action: rapdev.datadog_metric
    data:
      metric: sensor.temperature
      value: '{{ trigger.to_state.state }}'
      tags:
        name: '{{ trigger.to_state.name }}'
  mode: parallel
  max: 10
```

This pushes sensor state changes as metrics. You can just as easily push attributes as metrics, e.g. you could push `sun` component metrics with:

```yaml
- id: '123456789'
  alias: sun example
  triggers:
  - trigger: state
    entity_id:
    - sun.sun
  actions:
  - action: rapdev.datadog_metric
    data:
      value: '{{ trigger.to_state.attributes.azimuth }}'
      metric: sun.azimuth
  - action: rapdev.datadog_metric
    data:
      metric: sun.elevation
      value: '{{ trigger.to_state.attributes.elevation }}'
```

You can use the Automation UI to help build the majority of this if you don't like slinging YAML :grin:. You will still want to familiarize yourself with [Automation Templating](https://www.home-assistant.io/docs/automation/templating/) in order to write the `data:` entry for each action. Use `developer tools > states` if you're not sure about what `to_state` looks like for a given entity.

This integration will **not** auto-magically write any metrics to datadog for you; the `metric`s and `value`s (and optional `tags`) must be specified explicitly in automation actions (or equivalent).

## Important: Datadog Agent required

This integration writes your metrics in `statsd` format over UDP (default `localhost:8125`). You probably want to install the [Datadog add-on](https://github.com/rapdev-io/addon-datadog-agent) that provides the collector to receive these metrics.

## Actions

The integration provides the following actions.

### Action: Send Datadog Metric

The `rapdev.datadog_metrics` service is used to push metrics via dogstatsd into datadog.

- **Data attribute**: `metric`
    - **Description**: The name of the metric. Shows up in datadog prefixed by `prefix.<metric>` (default prefix is `hass`)
    - **Optional**: No
    - **Example**: `sensor.temperature`
- **Data attribute**: `value`
    - **Description**: The value of the metric. Will be coerced to a float.
    - **Optional**: No
    - **Example**: `42.0`
- **Data attribute**: `tags`
    - **Description**: Additional tags to attach to the metric.
    - **Optional**: Yes
    - **Example**:
    ```yaml
    tags:
        name: my_sensor_name
        foo: bar
    ```

## Contributing

Contributions welcome; see [Contributing](CONTRIBUTING.md).

File | Purpose | Documentation
-- | -- | --
`.devcontainer.json` | Used for development/testing with Visual Studio Code. | [Documentation](https://code.visualstudio.com/docs/remote/containers)
`.github/ISSUE_TEMPLATE/*.yml` | Templates for the issue tracker | [Documentation](https://help.github.com/en/github/building-a-strong-community/configuring-issue-templates-for-your-repository)
`custom_components/rapdev/*` | Integration files, this is where everything happens. | [Documentation](https://developers.home-assistant.io/docs/creating_component_index)
`CONTRIBUTING.md` | Guidelines on how to contribute. | [Documentation](https://help.github.com/en/github/building-a-strong-community/setting-guidelines-for-repository-contributors)
`LICENSE` | The license file for the project. | [Documentation](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/licensing-a-repository)
`README.md` | The file you are reading now, should contain info about the integration, installation and configuration instructions. | [Documentation](https://help.github.com/en/github/writing-on-github/basic-writing-and-formatting-syntax)
`requirements.txt` | Python packages used for development/lint/testing this integration. | [Documentation](https://pip.pypa.io/en/stable/user_guide/#requirements-files)


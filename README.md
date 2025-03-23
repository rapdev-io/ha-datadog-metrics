# Send your Home Assistant metrics to Datadog

This component exposes a Home Assistant [Service](https://developers.home-assistant.io/docs/dev_101_services) that can be used as a custom [Action Target](https://www.home-assistant.io/docs/automation/action/).

Common usage is to set up an Entity-based `state_changed` automation:

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

This gives you maximum flexibility to write what you want, how you want.  You can easily push attributes as metrics, e.g. you could push `sun` component metrics with:

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

You can use the Automation UI to help build the majority of this if you don't like slinging YAML :grin:. You will still want to familiarize yourself with [Automation Templating](https://www.home-assistant.io/docs/automation/templating/) in order to write the `data:` entry for each action.

This integration will **not** auto-magically write any metrics to datadog for you; the `metric`s and `value`s (and optional `tags`) must be specified explicitly in automation actions (or equivalent).

## Important: Datadog Agent required

This integration simply writes your metrics in `dogstatsd` format over UDP (default `localhost:8125`). You probably want to install the [Datadog add-on](TODO) that stands up the collector to receive these metrics.

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

## Next steps

TODO

- Add brand images (logo/icon) to https://github.com/home-assistant/brands.
- Create your first release.
- Share your integration on the [Home Assistant Forum](https://community.home-assistant.io/).
- Submit your integration to [HACS](https://hacs.xyz/docs/publish/start).

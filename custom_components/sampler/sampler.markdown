---
title: "Sampler Sensor"
description: "Republish values from another entity at a given frequency."
ha_category:
  - Utility
---

The `sampler` platform monitors another entity, and republishes its value at a given frequency.  This can be useful to throttle output from a high-frequency sensor down to a lower rate in order to reduce the amount of data in graphs, or to provide a regular sampling for use with certain modes of the Filter component such as lowpass which assume a fixed frequency of updates from the source.

## Setup

This platform is currently implemented as a custom component, and so copy the `sampler` directory to be within a `custom_components` subdirectory under your Home Assistant's `config` directory (see [this page](https://developers.home-assistant.io/docs/en/creating_integration_file_structure.html) for more info).

## Configuration

To add the sensor to your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: sampler
    name: "Test sampler throttle"
    entity_id: sensor.noisy_sensor
    mode: throttle
    interval: 60
```

### Configuration variables

* **name** (string) (Required) name for the sensor.
* **entity_id** (string) (Required) ID of the entity to sample.
* **mode** (string) (Optional) mode of the sampler (`boost`, `regulate`, `throttle`), defaults to `regulate`.
* **interval** (integer) (Optional) sampling interval in seconds, defaults to 60.

## Modes

### Regulate (default)

In this mode, the sampler will emit a value at the interval given no matter whether the input entity has published or not.  This provides a regular value stream, which may be useful for statistical analysis or time-based [filtering](https://www.home-assistant.io/components/filter/).

### Throttle

In this mode, the sampler will only emit a value when the input entity publishes a new value, but no more often than the interval given.  This can be useful if you want to reduce the amount of data being produced by a high-frequency sensor - e.g. to improve rendering speed of graphs.

### Boost

In this mode, the sampler will emit a value at the interval given, plus also immediately if the input entity publishes a new value.  This is useful if you have a sensor which only changes value occasionally but where you want to record the value more frequently.

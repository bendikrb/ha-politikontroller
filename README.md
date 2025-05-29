# Politikontroller.no Home Assistant integration

--------

[![GitHub Release][releases-shield]][releases]
[![Downloads][download-latest-shield]](Downloads)
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
[![Build Status][build-shield]][build]
![Made with Love in Norway][madewithlove-shield]


![Politikontroller][logo]

_Integration to bring entries from [politikontroller.no][politikontroller] to your Home Assistant instance._


---

# ⚠️ CURRENTLY BROKEN ⚠️

Due to an issue with the Politikontroller API, which was changed some time in early may, this integration is currently broken.


---

**This integration will set up the following platforms.**

| Platform       | Description                                                                                |
|----------------|--------------------------------------------------------------------------------------------|
| `geo_location` | One entity is created for each police control currently active within a configured radius. |

## Installation

### HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=bendikrb&repository=ha-politikontroller&category=Integration)

Or
Search for `Politikontroller` in HACS and install it under the "Integrations" category.

### Manual Installation
<details>
<summary>More Details</summary>

* You should take the latest [published release](https://github.com/bendikrb/ha-politikontroller/releases).
* To install, place the contents of `custom_components` into the `<config directory>/custom_components` folder of your Home Assistant installation.
* Restart Home Assistant
* In the HA UI go to Settings -> Integrations click "+" and search for "Politikontroller"
</details>

## Configuration is done in the UI

The configuration UI will guide you through adding the integration to Home Assistant, you just need an account at [politikontroller.no](https://politikontroller.no) with a valid username and password.

***
[politikontroller]: https://politikontroller.no
[commits-shield]: https://img.shields.io/github/commit-activity/y/bendikrb/ha-politikontroller.svg?style=flat
[commits]: https://github.com/bendikrb/ha-politikontroller/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=flat
[logo]: https://brands.home-assistant.io/ha_politikontroller/logo.png
[icon]: https://brands.home-assistant.io/ha_politikontroller/icon.png
[build-shield]: https://github.com/bendikrb/ha_politikontroller/actions/workflows/validate.yaml/badge.svg
[build]: https://github.com/bendikrb/ha_politikontroller/actions/workflows/validate.yaml
[license-shield]: https://img.shields.io/github/license/bendikrb/ha-politikontroller.svg?style=flat
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40bendikrb-blue.svg?style=flat
[releases-shield]: https://img.shields.io/github/release/bendikrb/ha-politikontroller.svg?style=flat
[releases]: https://github.com/bendikrb/ha-politikontroller/releases
[download-latest-shield]: https://img.shields.io/github/downloads/bendikrb/ha-politikontroller/total?style=flat
[madewithlove-shield]: https://madewithlove.now.sh/no?heart=true&colorB=%233584e4

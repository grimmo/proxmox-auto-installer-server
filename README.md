[![Latest Release][version-image]][version-url]
[![proxmox-auto-installer-server on DockerHub][dockerhub-image]][dockerhub-url]
[![Docker Build][gh-actions-image]][gh-actions-url]

# proxmox-auto-installer-server

This `Dockerfile` provides a mechanism to host `answer.toml` files, served dynamically, for Automated Proxmox VE installation via the HTTP answer file option.

Doc: https://pve.proxmox.com/wiki/Automated_Installation

> NOTE: Throughout this document, it's assumed that you are performing this on a Proxmox VE host or similar Debian/Ubuntu based solution. You *may* need to modify these steps if you are using another distro.

Builds are available at the following Docker repositories:

* Docker Hub: [docker.io/slothcroissant/proxmox-auto-installer-server](https://hub.docker.com/r/slothcroissant/proxmox-auto-installer-server)
* GitHub Container Registry: [ghcr.io/slothcroissant/proxmox-auto-installer-server](https://ghcr.io/slothcroissant/proxmox-auto-installer-server)
* Quay Container Registry: [quay.io/slothcroissant/proxmox-auto-installer-server](https://quay.io/repository/slothcroissant/proxmox-auto-installer-server)

# Run the Container

Populate a folder on the host with your .toml files (in this example, `/host/path/answers`). Each file should be `<mac_address>.toml` - for example `bc:24:11:d5:36:d1.toml`

Run the container:

``` bash
docker run -p 8000:8000 --mount type=bind,source=/host/path/answers,target=/app/answers slothcroissant/proxmox-auto-installer-server:latest
```

| Key | Value |
|-|-|
| `-p 8000:8000` | Port (host:container) on which to expose the application. The container port is `8000`, but you can map a different port via Docker. Ref: [Docker: Expose Ports](https://docs.docker.com/engine/containers/run/#exposed-ports)|
| `--mount type=bind,source=/host/path/answers,target=/app/answers` | Volume (via Bind Mount) exposed into the container. This can be anywhere on your host, and should always map to `/app/answers` in the container. Ref: [Docker: Bind Mounts](https://docs.docker.com/engine/containers/run/#bind-mounts)|
| `-e PUID=<int>` (Optional) | Sets the container's User ID (PUID) in case your volume mount has dependencies on PUID/PGID and is different than the default `1000`. |
| `-e PGID=<int>` (Optional) | Sets the container's Group ID (PGID) in case your volume mount has dependencies on PUID/PGID and is different than the default `1000`. |

Take note of your docker host's IP address and exposed port (if you deviated from the default `8000`), so you can point PVE to it later.

# PVE Automated Install Process

## Prerequisites

You will need to point Proxmox at your now-deployed container URL: `http://<ip_address>:8000/answer`.

If using DNS (via TXT record at `proxmox-auto-installer.{search domain}`, where `{search domain}` is the search domain provided by the DHCP server) or DHCP (as DHCP option 250) discovery options, you must have these configured prior to proceeding. As there are an infinite number of DNS/DHCP servers out there, please reference your specific solution if you choose this path. 

Alternatively, there are no prerequisites if using the `--url` option in the ISO itself.

Once this container is running, you will see logs confirming:

``` bash
======== Running on http://0.0.0.0:8000 ========
```

## Boot Proxmox

To run the PVE installer against this container:

1. Download the PVE ISO from https://www.proxmox.com/downloads:

    ``` bash
    wget https://enterprise.proxmox.com/iso/proxmox-ve_8.2-2.iso
    ```

1. Prepare the PVE ISO for Automated Install

   * If using DNS/DHCP (previously configured - see prerequisites):
      ```
      proxmox-auto-install-assistant prepare-iso \
        --fetch-from http \
        --output /root/proxmox-ve_8.2-2.-httpanswer.iso \
        /root/proxmox-ve_8.2-2.iso
      ```
   * If using `--url` to declare the URL manually, you must add the parameter: 
      ```
      proxmox-auto-install-assistant prepare-iso \
        --fetch-from http \
        --url http://<ip_address>:8000/answer
        --output /root/proxmox-ve_8.2-2.-httpanswer.iso \
        /root/proxmox-ve_8.2-2.iso
      ```

1. Boot to this ISO, and the automated process shoud take over from there!

# Appendix

## Example JSON POST data

Below you can find a few exmples of the JSON POST data sent by Proxmox VE installer:

### Cisco UCS C220m4:

### Proxmox VM

This is just for additional context/learning, it's generally rare to use this (in a nested virtualization scenario). In this example, the VM was created with *all* the defaults, with the PVE 8.2.2 ISO booted:

``` json
{
 "product": {
  "fullname": "Proxmox VE",
  "product": "pve",
  "enable_btrfs": true
 },
 "iso": {
  "release": "8.2",
  "isorelease": "2"
 },
 "dmi": {
  "system": {
   "name": "Standard PC (i440FX + PIIX, 1996)",
   "serial": "",
   "uuid": "bcf43ddf-6d92-4ace-b93f-76f71ffe4495",
   "sku": ""
  },
  "baseboard": {},
  "chassis": {
   "asset_tag": "",
   "serial": ""
  }
 },
 "network_interfaces": [
  {
   "link": "ens18",
   "mac": "bc:24:11:d5:36:d1"
  }
 ]
}
```

[version-image]: https://img.shields.io/github/v/release/SlothCroissant/proxmox-auto-installer-server?style=for-the-badge
[version-url]: https://github.com/SlothCroissant/proxmox-auto-installer-server/releases

[gh-actions-image]: https://img.shields.io/github/actions/workflow/status/SlothCroissant/proxmox-auto-installer-server/main.yml?style=for-the-badge
[gh-actions-url]: https://github.com/SlothCroissant/proxmox-auto-installer-server/actions

[dockerhub-image]: https://img.shields.io/docker/pulls/slothcroissant/proxmox-auto-installer-server?label=DockerHub%20Pulls&style=for-the-badge
[dockerhub-url]: https://hub.docker.com/r/slothcroissant/proxmox-auto-installer-server

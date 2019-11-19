import asyncio
import ipaddress

from aiozeroconf import ServiceBrowser, ServiceStateChange, Zeroconf

from .bridge import Bridge

URL_NUPNP = 'https://www.meethue.com/api/nupnp'


async def discover_nupnp(websession):
    """Discover bridges via NUPNP."""
    async with websession.get(URL_NUPNP) as res:
        return [Bridge(item['internalipaddress'], websession=websession)
                for item in (await res.json())]

async def discover_mdns(websession=None, timeout=5):
    discovered_bridge = []

    async def do_close(zc):
        await zc.close()

    def on_service_state_change(zc, service_type, name, state_change):
        if state_change is ServiceStateChange.Added:
            asyncio.ensure_future(on_service_state_change_process(zc, service_type, name))

    async def on_service_state_change_process(zc, service_type, name):
        info = await zc.get_service_info(service_type, name)
        discovered_bridge.append(info)
        await do_close(zc)

    async def find_hue(zc):
        browser = ServiceBrowser(zc, "_hue._tcp.local.", handlers=[on_service_state_change])
        await asyncio.sleep(timeout)
        browser.cancel()

    loop = asyncio.get_event_loop()
    zeroconf = Zeroconf(loop)
    await find_hue(zeroconf)
    return [Bridge(ipaddress.ip_address(item.address), websession=websession) for item in discovered_bridge]
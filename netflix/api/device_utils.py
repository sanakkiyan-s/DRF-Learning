"""
Device detection utilities for parsing User-Agent headers.
"""
from user_agents import parse
from .models import Device


def get_device_info(request):
    """
    Parse the User-Agent header and extract device information.
    Returns a dict with device_type, device_name, device_model, os_version.
    """
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    user_agent = parse(user_agent_string)
    
    # Determine device type
    if user_agent.is_mobile:
        device_type = Device.DeviceType.MOBILE
    elif user_agent.is_tablet:
        device_type = Device.DeviceType.TABLET
    elif user_agent.is_pc:
        device_type = Device.DeviceType.DESKTOP
    else:
        # Could be Smart TV or other device
        device_type = Device.DeviceType.SMART_TV
    
    # Build device name from browser and OS
    browser = user_agent.browser.family or 'Unknown Browser'
    browser_version = user_agent.browser.version_string or ''
    os_name = user_agent.os.family or 'Unknown OS'
    os_version = user_agent.os.version_string or ''
    
    device_name = f"{browser} on {os_name}"
    device_model = user_agent.device.family or None
    
    device_info = {
        'device_type': device_type,
        'device_name': device_name,
        'device_model': device_model,
        'os_version': f"{os_name} {os_version}".strip(),
        'raw_user_agent': user_agent_string
    }
    print(f"Device Info: {device_info}")
    return device_info


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

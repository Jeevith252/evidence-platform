# services/image_service.py
# Extracts hidden EXIF metadata from images
# This is like reading the secret diary of a photo!

import exifread
import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime


def extract_metadata(image_path: str) -> dict:
    """
    Extracts ALL hidden metadata from an image file
    Including WiFi, network, and location clues
    """
    result = {
        "file_name": os.path.basename(image_path),
        "file_size": f"{os.path.getsize(image_path) / 1024:.2f} KB",
        "gps": None,
        "device": {},
        "datetime": None,
        "software": None,
        "network_clues": {},   # NEW - WiFi/network data
        "location_hints": [],  # NEW - indirect location clues
        "full_exif": {}
    }

    try:
        # --- METHOD 1: Using Pillow ---
        img = Image.open(image_path)
        result["image_width"] = img.width
        result["image_height"] = img.height
        result["image_format"] = img.format

        exif_data = img._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)

                if tag == "Make":
                    result["device"]["brand"] = str(value)
                elif tag == "Model":
                    result["device"]["model"] = str(value)
                elif tag == "Software":
                    result["software"] = str(value)
                elif tag == "DateTime":
                    result["datetime"] = str(value)
                elif tag == "DateTimeOriginal":
                    result["datetime"] = str(value)
                elif tag == "GPSInfo":
                    gps = {}
                    for gps_tag_id, gps_value in value.items():
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps[gps_tag] = str(gps_value)
                    result["gps_raw"] = gps
                    coords = convert_gps(value)
                    if coords:
                        result["gps"] = coords

                # --- NEW: Look for network related tags ---
                elif "wifi" in str(tag).lower():
                    result["network_clues"]["wifi_tag"] = str(value)
                elif "network" in str(tag).lower():
                    result["network_clues"]["network_tag"] = str(value)
                elif "location" in str(tag).lower():
                    result["location_hints"].append({
                        "type": "location_tag",
                        "value": str(value)
                    })

                result["full_exif"][str(tag)] = str(value)

    except Exception as e:
        result["pillow_error"] = str(e)

    try:
        # --- METHOD 2: ExifRead (deeper scan) ---
        with open(image_path, "rb") as f:
            tags = exifread.process_file(f, details=True)

        for tag, value in tags.items():
            tag_str = str(tag).lower()
            value_str = str(value)
            clean_tag = tag.replace("EXIF ", "").replace("Image ", "")

            result["full_exif"][str(clean_tag)] = value_str

            # Device info
            if "make" in tag_str and not result["device"].get("brand"):
                result["device"]["brand"] = value_str
            if "model" in tag_str and not result["device"].get("model"):
                result["device"]["model"] = value_str
            if "datetime" in tag_str and not result["datetime"]:
                result["datetime"] = value_str

            # --- NEW: Scan ALL tags for network/WiFi clues ---
            if any(word in tag_str for word in [
                "wifi", "network", "ssid", "bssid",
                "wireless", "internet", "connection"
            ]):
                result["network_clues"][clean_tag] = value_str

            # --- NEW: Scan for location hints ---
            if any(word in tag_str for word in [
                "location", "place", "city", "country",
                "address", "sublocation", "province",
                "state", "region"
            ]):
                result["location_hints"].append({
                    "type": clean_tag,
                    "value": value_str
                })

            # --- NEW: Scan values for IP addresses ---
            import re
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            ips_found = re.findall(ip_pattern, value_str)
            if ips_found:
                for ip in ips_found:
                    # Filter out version numbers like 1.0.0.1
                    if not ip.startswith("1.0") and not ip.startswith("0."):
                        result["network_clues"]["possible_ip"] = ip
                        result["location_hints"].append({
                            "type": "IP Address found in metadata",
                            "value": ip,
                            "note": "Check this IP for approximate location"
                        })

            # --- NEW: Scan for XMP location data ---
            if "xmp" in tag_str or "iptc" in tag_str:
                result["location_hints"].append({
                    "type": f"XMP/IPTC: {clean_tag}",
                    "value": value_str
                })

    except Exception as e:
        result["exifread_error"] = str(e)

    # --- NEW: Check for XMP metadata separately ---
    try:
        with open(image_path, "rb") as f:
            raw_data = f.read().decode("latin-1")

        # Look for XMP location data embedded in file
        xmp_fields = [
            ("City", "city"),
            ("Country", "country"),
            ("State", "state"),
            ("Location", "location"),
            ("GPSLatitude", "xmp_latitude"),
            ("GPSLongitude", "xmp_longitude"),
            ("WiFiSSID", "wifi_ssid"),
            ("NetworkSSID", "network_ssid"),
        ]

        for xml_tag, key in xmp_fields:
            # Search for tag in raw XMP data
            pattern = f'<[^>]*{xml_tag}[^>]*>([^<]+)<'
            matches = re.findall(pattern, raw_data)
            if matches:
                result["location_hints"].append({
                    "type": key,
                    "value": matches[0].strip()
                })
                if "wifi" in key or "network" in key:
                    result["network_clues"][key] = matches[0].strip()

    except Exception as e:
        result["xmp_error"] = str(e)

    # Build summary
    result["summary"] = build_summary(result)
    return result


def convert_gps(gps_info: dict) -> dict:
    """
    Converts raw GPS data to readable latitude/longitude
    """
    try:
        def to_decimal(values):
            d = float(values[0])
            m = float(values[1])
            s = float(values[2])
            return d + (m / 60.0) + (s / 3600.0)

        lat = to_decimal(gps_info.get(2, [0, 0, 0]))
        lon = to_decimal(gps_info.get(4, [0, 0, 0]))

        lat_ref = str(gps_info.get(1, "N"))
        lon_ref = str(gps_info.get(3, "E"))

        if lat_ref == "S":
            lat = -lat
        if lon_ref == "W":
            lon = -lon

        return {
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "google_maps_url": f"https://maps.google.com/?q={lat},{lon}"
        }
    except:
        return None


def build_summary(data: dict) -> dict:
    """
    Builds a human readable summary of findings
    """
    findings = []
    risk_indicators = []

    if data.get("device"):
        device = data["device"]
        brand = device.get("brand", "Unknown")
        model = device.get("model", "Unknown")
        findings.append(f"Photo taken with: {brand} {model}")

    if data.get("datetime"):
        findings.append(f"Date & Time: {data['datetime']}")

    if data.get("software"):
        findings.append(f"Software used: {data['software']}")

    if data.get("gps"):
        gps = data["gps"]
        findings.append(
            f"GPS Location: {gps['latitude']}, {gps['longitude']}"
        )
        findings.append(f"Google Maps: {gps['google_maps_url']}")
        risk_indicators.append(
            "GPS coordinates found — exact location traceable!"
        )

    # --- NEW: Network clues summary ---
    if data.get("network_clues"):
        clues = data["network_clues"]

        if clues.get("wifi_ssid") or clues.get("network_ssid"):
            ssid = clues.get("wifi_ssid") or clues.get("network_ssid")
            findings.append(f"WiFi Network found: {ssid}")
            risk_indicators.append(
                f"WiFi SSID '{ssid}' found — search this network name to find location!"
            )

        if clues.get("possible_ip"):
            ip = clues["possible_ip"]
            findings.append(f"IP Address found: {ip}")
            risk_indicators.append(
                f"IP Address {ip} found in metadata — can be traced to ISP/location!"
            )

    # --- NEW: Location hints summary ---
    if data.get("location_hints"):
        for hint in data["location_hints"]:
            findings.append(
                f"Location clue [{hint['type']}]: {hint['value']}"
            )
            risk_indicators.append(
                f"Location data found: {hint['value']}"
            )

    if not data.get("gps"):
        if not data.get("network_clues") and not data.get("location_hints"):
            risk_indicators.append(
                "No GPS or network data found. "
                "Image may have been shared through "
                "WhatsApp/Instagram which strips metadata."
            )
        else:
            risk_indicators.append(
                "No GPS but other location clues found — see findings above!"
            )

    if not data.get("device"):
        risk_indicators.append(
            "No device info found — EXIF may have been stripped."
        )

    return {
        "findings": findings,
        "risk_indicators": risk_indicators,
        "has_gps": data.get("gps") is not None,
        "has_device_info": bool(data.get("device")),
        "has_timestamp": data.get("datetime") is not None,
        "has_network_clues": bool(data.get("network_clues")),
        "has_location_hints": bool(data.get("location_hints"))
    }

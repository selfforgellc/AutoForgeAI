from typing import Optional

HL = "#ff3b3b"
DIM = "#9aa0a6"

def ignition_circuit_svg(highlight: Optional[str] = "coil"):
    """Ignition system schematic."""
    return f'''<svg width="720" height="360" viewBox="0 0 720 360" xmlns="http://www.w3.org/2000/svg">
      <rect width="720" height="360" fill="#0b0b0d"/>
      <g font-family="Inter,Arial" font-size="12" fill="{DIM}" stroke="{DIM}">
        <rect x="40" y="150" width="80" height="60" fill="none" stroke="{DIM}" rx="6"/>
        <text x="80" y="185" text-anchor="middle">Battery</text>

        <rect x="160" y="165" width="40" height="30" fill="none" stroke="{DIM}"/>
        <text x="180" y="160" text-anchor="middle">Fuse</text>

        <rect x="240" y="145" width="60" height="70" fill="none" stroke="{HL if highlight=='coil' else DIM}" stroke-width="{2 if highlight=='coil' else 1.2}" rx="6"/>
        <text x="270" y="140" text-anchor="middle" fill="{HL if highlight=='coil' else DIM}">Ignition Coil</text>

        <circle cx="380" cy="180" r="18" fill="none" stroke="{HL if highlight=='plug' else DIM}" stroke-width="{2 if highlight=='plug' else 1.2}"/>
        <text x="380" y="210" text-anchor="middle" fill="{HL if highlight=='plug' else DIM}">Spark Plug</text>

        <rect x="520" y="120" width="130" height="120" fill="none" stroke="{HL if highlight=='ecm' else DIM}" stroke-width="{2 if highlight=='ecm' else 1.2}" rx="8"/>
        <text x="585" y="115" text-anchor="middle" fill="{HL if highlight=='ecm' else DIM}">ECM</text>

        <line x1="120" y1="180" x2="160" y2="180" stroke="{DIM}"/>
        <line x1="200" y1="180" x2="240" y2="180" stroke="{DIM}"/>
        <line x1="300" y1="180" x2="362" y2="180" stroke="{DIM}"/>
        <line x1="398" y1="180" x2="520" y2="180" stroke="{DIM}"/>
      </g>
    </svg>'''


def fuel_system_svg(highlight: Optional[str] = "injector"):
    """Fuel system schematic."""
    return f'''<svg width="720" height="360" xmlns="http://www.w3.org/2000/svg">
      <rect width="720" height="360" fill="#0b0b0d"/>
      <g font-family="Inter,Arial" font-size="12" fill="{DIM}" stroke="{DIM}">
        <rect x="40" y="150" width="90" height="50" fill="none" stroke="{DIM}" rx="6"/>
        <text x="85" y="180" text-anchor="middle">Fuel Tank</text>

        <rect x="160" y="160" width="70" height="30" fill="none" stroke="{HL if highlight=='pump' else DIM}" stroke-width="{2 if highlight=='pump' else 1.2}" rx="6"/>
        <text x="195" y="155" text-anchor="middle" fill="{HL if highlight=='pump' else DIM}">Fuel Pump</text>

        <rect x="270" y="160" width="60" height="30" fill="none" stroke="{HL if highlight=='filter' else DIM}" stroke-width="{2 if highlight=='filter' else 1.2}" rx="6"/>
        <text x="300" y="155" text-anchor="middle" fill="{HL if highlight=='filter' else DIM}">Filter</text>

        <rect x="370" y="150" width="90" height="50" fill="none" stroke="{HL if highlight=='injector' else DIM}" stroke-width="{2 if highlight=='injector' else 1.2}" rx="6"/>
        <text x="415" y="145" text-anchor="middle" fill="{HL if highlight=='injector' else DIM}">Injectors</text>

        <rect x="520" y="130" width="140" height="90" fill="none" stroke="{HL if highlight=='ecm' else DIM}" stroke-width="{2 if highlight=='ecm' else 1.2}" rx="8"/>
        <text x="590" y="125" text-anchor="middle" fill="{HL if highlight=='ecm' else DIM}">ECM</text>

        <line x1="130" y1="175" x2="160" y2="175" stroke="{DIM}"/>
        <line x1="230" y1="175" x2="270" y2="175" stroke="{DIM}"/>
        <line x1="330" y1="175" x2="370" y2="175" stroke="{DIM}"/>
        <line x1="460" y1="175" x2="520" y2="175" stroke="{DIM}"/>
      </g>
    </svg>'''


def cooling_system_svg(highlight: Optional[str] = "radiator"):
    """Cooling system schematic."""
    return f'''<svg width="720" height="360" xmlns="http://www.w3.org/2000/svg">
      <rect width="720" height="360" fill="#0b0b0d"/>
      <g font-family="Inter,Arial" font-size="12" fill="{DIM}" stroke="{DIM}">
        <rect x="60" y="120" width="100" height="120" fill="none" stroke="{HL if highlight=='radiator' else DIM}" stroke-width="{2 if highlight=='radiator' else 1.2}" rx="6"/>
        <text x="110" y="115" text-anchor="middle" fill="{HL if highlight=='radiator' else DIM}">Radiator</text>

        <rect x="200" y="150" width="60" height="60" fill="none" stroke="{HL if highlight=='thermostat' else DIM}" stroke-width="{2 if highlight=='thermostat' else 1.2}" rx="6"/>
        <text x="230" y="145" text-anchor="middle" fill="{HL if highlight=='thermostat' else DIM}">Thermostat</text>

        <rect x="300" y="140" width="80" height="80" fill="none" stroke="{HL if highlight=='pump' else DIM}" stroke-width="{2 if highlight=='pump' else 1.2}" rx="6"/>
        <text x="340" y="135" text-anchor="middle" fill="{HL if highlight=='pump' else DIM}">Water Pump</text>

        <rect x="420" y="130" width="140" height="100" fill="none" stroke="{HL if highlight=='engine' else DIM}" stroke-width="{2 if highlight=='engine' else 1.2}" rx="8"/>
        <text x="490" y="125" text-anchor="middle" fill="{HL if highlight=='engine' else DIM}">Engine Block</text>

        <line x1="160" y1="180" x2="200" y2="180" stroke="{DIM}"/>
        <line x1="260" y1="180" x2="300" y2="180" stroke="{DIM}"/>
        <line x1="380" y1="180" x2="420" y2="180" stroke="{DIM}"/>
      </g>
    </svg>'''


def charging_system_svg(highlight: Optional[str] = "alternator"):
    """Charging system schematic."""
    return f'''<svg width="720" height="360" xmlns="http://www.w3.org/2000/svg">
      <rect width="720" height="360" fill="#0b0b0d"/>
      <g font-family="Inter,Arial" font-size="12" fill="{DIM}" stroke="{DIM}">
        <rect x="60" y="150" width="100" height="60" fill="none" stroke="{DIM}" rx="6"/>
        <text x="110" y="180" text-anchor="middle">Battery</text>

        <circle cx="270" cy="180" r="30" fill="none" stroke="{HL if highlight=='alternator' else DIM}" stroke-width="{2 if highlight=='alternator' else 1.2}"/>
        <text x="270" y="225" text-anchor="middle" fill="{HL if highlight=='alternator' else DIM}">Alternator</text>

        <rect x="380" y="150" width="60" height="60" fill="none" stroke="{HL if highlight=='regulator' else DIM}" stroke-width="{2 if highlight=='regulator' else 1.2}" rx="6"/>
        <text x="410" y="145" text-anchor="middle" fill="{HL if highlight=='regulator' else DIM}">Regulator</text>

        <rect x="500" y="150" width="150" height="60" fill="none" stroke="{HL if highlight=='ecm' else DIM}" stroke-width="{2 if highlight=='ecm' else 1.2}" rx="8"/>
        <text x="575" y="145" text-anchor="middle" fill="{HL if highlight=='ecm' else DIM}">ECM</text>

        <line x1="160" y1="180" x2="240" y2="180" stroke="{DIM}"/>
        <line x1="300" y1="180" x2="380" y2="180" stroke="{DIM}"/>
        <line x1="440" y1="180" x2="500" y2="180" stroke="{DIM}"/>
      </g>
    </svg>'''


def starter_circuit_svg(highlight: Optional[str] = "starter"):
    """Starting system schematic."""
    return f'''<svg width="720" height="360" xmlns="http://www.w3.org/2000/svg">
      <rect width="720" height="360" fill="#0b0b0d"/>
      <g font-family="Inter,Arial" font-size="12" fill="{DIM}" stroke="{DIM}">
        <rect x="60" y="150" width="100" height="60" fill="none" stroke="{DIM}" rx="6"/>
        <text x="110" y="180" text-anchor="middle">Battery</text>

        <rect x="200" y="160" width="80" height="40" fill="none" stroke="{HL if highlight=='ignition_switch' else DIM}" stroke-width="{2 if highlight=='ignition_switch' else 1.2}" rx="6"/>
        <text x="240" y="155" text-anchor="middle" fill="{HL if highlight=='ignition_switch' else DIM}">Ignition Switch</text>

        <rect x="330" y="160" width="80" height="40" fill="none" stroke="{HL if highlight=='solenoid' else DIM}" stroke-width="{2 if highlight=='solenoid' else 1.2}" rx="6"/>
        <text x="370" y="155" text-anchor="middle" fill="{HL if highlight=='solenoid' else DIM}">Solenoid</text>

        <rect x="460" y="140" width="100" height="80" fill="none" stroke="{HL if highlight=='starter' else DIM}" stroke-width="{2 if highlight=='starter' else 1.2}" rx="6"/>
        <text x="510" y="135" text-anchor="middle" fill="{HL if highlight=='starter' else DIM}">Starter Motor</text>

        <line x1="160" y1="180" x2="200" y2="180" stroke="{DIM}"/>
        <line x1="280" y1="180" x2="330" y2="180" stroke="{DIM}"/>
        <line x1="410" y1="180" x2="460" y2="180" stroke="{DIM}"/>
      </g>
    </svg>'''


def obd_network_svg(highlight: Optional[str] = "can"):
    """OBD-II CAN network schematic."""
    return f'''<svg width="720" height="360" xmlns="http://www.w3.org/2000/svg">
      <rect width="720" height="360" fill="#0b0b0d"/>
      <g font-family="Inter,Arial" font-size="12" fill="{DIM}" stroke="{DIM}">
        <rect x="60" y="160" width="100" height="40" fill="none" stroke="{HL if highlight=='dlc' else DIM}" stroke-width="{2 if highlight=='dlc' else 1.2}" rx="6"/>
        <text x="110" y="155" text-anchor="middle" fill="{HL if highlight=='dlc' else DIM}">OBD-II DLC</text>

        <rect x="240" y="150" width="100" height="60" fill="none" stroke="{HL if highlight=='can' else DIM}" stroke-width="{2 if highlight=='can' else 1.2}" rx="6"/>
        <text x="290" y="145" text-anchor="middle" fill="{HL if highlight=='can' else DIM}">CAN Bus</text>

        <rect x="400" y="140" width="90" height="80" fill="none" stroke="{HL if highlight=='ecm' else DIM}" stroke-width="{2 if highlight=='ecm' else 1.2}" rx="6"/>
        <text x="445" y="135" text-anchor="middle" fill="{HL if highlight=='ecm' else DIM}">ECM</text>

        <rect x="520" y="140" width="120" height="80" fill="none" stroke="{HL if highlight=='tcm' else DIM}" stroke-width="{2 if highlight=='tcm' else 1.2}" rx="6"/>
        <text x="580" y="135" text-anchor="middle" fill="{HL if highlight=='tcm' else DIM}">TCM / ABS</text>

        <line x1="160" y1="180" x2="240" y2="180" stroke="{DIM}"/>
        <line x1="340" y1="180" x2="400" y2="180" stroke="{DIM}"/>
        <line x1="490" y1="180" x2="520" y2="180" stroke="{DIM}"/>
      </g>
    </svg>'''

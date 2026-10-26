import os
import json
import logging
from typing import Optional

from database import db_manager

logger = logging.getLogger(__name__)

# Complete standalone CSS extracted from zayro.html with high-priority isolation
ZAYRO_CSS = """
:root {
  --z-red: #ff003c;
  --z-glow: rgba(255, 0, 60, 0.45);
  --z-gold: #ffd000;
  --z-green: #00ff88;
  --z-bg-card: #0d0208;
  --z-card-w: 240px;
}

#zayro-vip-overlay {
  position: fixed !important;
  top: 14px !important;
  left: 50% !important;
  transform: translateX(-50%) !important;
  z-index: 2147483647 !important;
  width: var(--z-card-w) !important;
  pointer-events: none !important;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
  user-select: none !important;
  -webkit-user-select: none !important;
  display: block !important;
  box-sizing: border-box !important;
}

#zayro-vip-overlay * {
  box-sizing: border-box !important;
  margin: 0;
  padding: 0;
}

#zayro-vip-overlay .card-outer {
  position: relative !important;
  width: 100% !important;
  background: radial-gradient(circle at 50% 0%, #1e030a 0%, #0d0206 50%, #060103 100%) !important;
  border-radius: 16px !important;
  box-shadow: 
    0 16px 40px rgba(0, 0, 0, 0.95),
    0 0 25px rgba(255, 0, 60, 0.4),
    inset 0 0 15px rgba(255, 0, 60, 0.18) !important;
  border: 1.2px solid rgba(255, 0, 60, 0.7) !important;
  overflow: visible !important;
}

#zayro-vip-overlay .card-stroke {
  position: absolute !important;
  inset: 0 !important;
  width: 100% !important;
  height: 100% !important;
  pointer-events: none !important;
  z-index: 8 !important;
  overflow: visible !important;
}

#zayro-vip-overlay .card-stroke rect {
  fill: none !important;
  stroke: #ffd166 !important;
  stroke-width: 1.8 !important;
  stroke-dasharray: 22 78 !important;
  stroke-dashoffset: 0 !important;
  stroke-linecap: round !important;
  animation: zayroRunningStroke 3.4s linear infinite !important;
  filter: drop-shadow(0 0 4px rgba(255, 164, 0, 0.95)) drop-shadow(0 0 10px rgba(255, 74, 0, 0.55)) !important;
}

@keyframes zayroRunningStroke {
  from { stroke-dashoffset: 100; }
  to { stroke-dashoffset: 0; }
}

#zayro-vip-overlay .card-title-line1 {
  position: absolute !important;
  top: -10px !important;
  left: 50% !important;
  transform: translateX(-50%) !important;
  background: linear-gradient(180deg, #ff3b6d 0%, #d00035 56%, #78001b 100%) !important;
  border: 1px solid #ff8aa5 !important;
  border-radius: 14px !important;
  padding: 2px 10px !important;
  font-size: 8px !important;
  font-weight: 900 !important;
  letter-spacing: 0.1em !important;
  color: #ffffff !important;
  text-transform: uppercase !important;
  white-space: nowrap !important;
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.7),
    0 0 10px rgba(255, 0, 60, 0.7),
    inset 0 1px 1px rgba(255, 255, 255, 0.5) !important;
  z-index: 10 !important;
}

#zayro-vip-overlay .card-bracket {
  position: absolute !important;
  width: 9px !important;
  height: 9px !important;
  pointer-events: none !important;
  z-index: 6 !important;
}
#zayro-vip-overlay .card-bracket::before, #zayro-vip-overlay .card-bracket::after {
  content: '' !important;
  position: absolute !important;
  background: #ffd000 !important;
  box-shadow: 0 0 5px #ffd000 !important;
}
#zayro-vip-overlay .b-tl { top: -2px !important; left: -2px !important; }
#zayro-vip-overlay .b-tl::before { top: 0 !important; left: 0 !important; width: 7px !important; height: 1.5px !important; }
#zayro-vip-overlay .b-tl::after  { top: 0 !important; left: 0 !important; width: 1.5px !important; height: 7px !important; }

#zayro-vip-overlay .b-tr { top: -2px !important; right: -2px !important; }
#zayro-vip-overlay .b-tr::before { top: 0 !important; right: 0 !important; width: 7px !important; height: 1.5px !important; }
#zayro-vip-overlay .b-tr::after  { top: 0 !important; right: 0 !important; width: 1.5px !important; height: 7px !important; }

#zayro-vip-overlay .b-bl { bottom: -2px !important; left: -2px !important; }
#zayro-vip-overlay .b-bl::before { bottom: 0 !important; left: 0 !important; width: 7px !important; height: 1.5px !important; }
#zayro-vip-overlay .b-bl::after  { bottom: 0 !important; left: 0 !important; width: 1.5px !important; height: 7px !important; }

#zayro-vip-overlay .b-br { bottom: -2px !important; right: -2px !important; }
#zayro-vip-overlay .b-br::before { bottom: 0 !important; right: 0 !important; width: 7px !important; height: 1.5px !important; }
#zayro-vip-overlay .b-br::after  { bottom: 0 !important; right: 0 !important; width: 1.5px !important; height: 7px !important; }

#zayro-vip-overlay .card-inner {
  position: relative !important;
  padding: 8px 7px 7px !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 5px !important;
  z-index: 2 !important;
}

#zayro-vip-overlay .mode-strip {
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  background: rgba(15, 2, 8, 0.9) !important;
  border: 1px solid rgba(255, 0, 60, 0.4) !important;
  border-radius: 6px !important;
  padding: 3px 6px !important;
  font-size: 6.5px !important;
  font-weight: 800 !important;
  letter-spacing: 0.05em !important;
  color: #ffffff !important;
  font-family: monospace, sans-serif !important;
}

#zayro-vip-overlay .strip-item {
  display: flex !important;
  align-items: center !important;
  gap: 2px !important;
}
#zayro-vip-overlay .strip-item span:first-child {
  color: rgba(255, 255, 255, 0.75) !important;
}
#zayro-vip-overlay .strip-val {
  color: #ffffff !important;
  font-weight: 900 !important;
}
#zayro-vip-overlay .strip-mode {
  color: #ff003c !important;
  font-weight: 900 !important;
  text-shadow: 0 0 6px rgba(255, 0, 60, 0.7) !important;
}
#zayro-vip-overlay .strip-ping {
  color: #00ff88 !important;
  font-weight: 900 !important;
  text-shadow: 0 0 6px rgba(0, 255, 136, 0.6) !important;
}

#zayro-vip-overlay .card-screen {
  position: relative !important;
  width: 100% !important;
  background: #090105 !important;
  border-radius: 10px !important;
  border: 1px solid rgba(255, 0, 60, 0.5) !important;
  padding: 6px 5px !important;
  box-shadow: inset 0 0 16px rgba(0, 0, 0, 0.9) !important;
  overflow: hidden !important;
}

#zayro-vip-overlay .screen-cyber-matrix {
  position: absolute !important;
  inset: 0 !important;
  pointer-events: none !important;
  overflow: hidden !important;
  z-index: 0 !important;
}

#zayro-vip-overlay .circuit-svg {
  position: absolute !important;
  inset: 0 !important;
  width: 100% !important;
  height: 100% !important;
  opacity: 0.3 !important;
}

#zayro-vip-overlay .telemetry-hud-tag {
  position: absolute !important;
  font-family: monospace, sans-serif !important;
  font-size: 5.5px !important;
  font-weight: 800 !important;
  letter-spacing: 0.05em !important;
  color: rgba(255, 0, 60, 0.6) !important;
}
#zayro-vip-overlay .tele-tl { top: 3px !important; left: 5px !important; }
#zayro-vip-overlay .tele-tr { top: 3px !important; right: 5px !important; color: rgba(255, 208, 0, 0.65) !important; }
#zayro-vip-overlay .tele-bl { bottom: 3px !important; left: 5px !important; }
#zayro-vip-overlay .tele-br { bottom: 3px !important; right: 5px !important; }

#zayro-vip-overlay .laser-sweep-line {
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  height: 1px !important;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 0, 60, 0.8) 50%, transparent 100%) !important;
  box-shadow: 0 0 8px #ff003c !important;
  animation: zayroLaserSweep 4s ease-in-out infinite !important;
  opacity: 0.45 !important;
}
@keyframes zayroLaserSweep {
  0% { top: 0%; opacity: 0; }
  25% { opacity: 0.6; }
  75% { opacity: 0.6; }
  100% { top: 100%; opacity: 0; }
}

#zayro-vip-overlay #sv-result {
  position: relative !important;
  z-index: 3 !important;
  width: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 5px !important;
}

#zayro-vip-overlay .pred-showcase-row {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  width: 100% !important;
  padding: 0 4px !important;
}

#zayro-vip-overlay .res-outcome-ingot {
  position: relative !important;
  width: 110px !important;
  height: 52px !important;
  border-radius: 9px !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  text-align: center !important;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.7),
    inset 0 1px 2px rgba(255, 255, 255, 0.4),
    inset 0 -2px 4px rgba(0, 0, 0, 0.6) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
}

#zayro-vip-overlay .res-outcome-ingot.big {
  background: linear-gradient(180deg, #ff1a53 0%, #c4002c 50%, #750017 100%) !important;
  border-color: #ff5c85 !important;
  box-shadow: 
    0 0 14px rgba(255, 0, 60, 0.65),
    inset 0 1px 2px rgba(255, 255, 255, 0.4),
    inset 0 -2px 4px rgba(0, 0, 0, 0.6) !important;
}
#zayro-vip-overlay .res-outcome-ingot.small {
  background: linear-gradient(180deg, #00d668 0%, #009945 50%, #005224 100%) !important;
  border-color: #33ff99 !important;
  box-shadow: 
    0 0 14px rgba(0, 255, 136, 0.65),
    inset 0 1px 2px rgba(255, 255, 255, 0.4),
    inset 0 -2px 4px rgba(0, 0, 0, 0.6) !important;
}

#zayro-vip-overlay .ingot-top-tag {
  font-size: 6px !important;
  font-weight: 900 !important;
  letter-spacing: 0.1em !important;
  color: #ffd000 !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8) !important;
}
#zayro-vip-overlay .ingot-main-text {
  font-size: 21px !important;
  font-weight: 900 !important;
  letter-spacing: 0.05em !important;
  color: #ffffff !important;
  line-height: 1.1 !important;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.8) !important;
}
#zayro-vip-overlay .ingot-conf-pill {
  display: flex !important;
  align-items: center !important;
  gap: 3px !important;
  font-family: monospace, sans-serif !important;
  font-size: 6.5px !important;
  font-weight: 800 !important;
  color: #ffffff !important;
}
#zayro-vip-overlay .conf-dot {
  width: 4px !important;
  height: 4px !important;
  border-radius: 50% !important;
  background: #ffd000 !important;
  box-shadow: 0 0 4px #ffd000 !important;
}

#zayro-vip-overlay .res-chip-pedestal {
  position: relative !important;
  width: 86px !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
}

#zayro-vip-overlay .res-ball {
  position: relative !important;
  width: 44px !important;
  height: 44px !important;
  border-radius: 50% !important;
  display: grid !important;
  place-items: center !important;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.85) !important;
}

#zayro-vip-overlay .ball-circle-red {
  background: radial-gradient(circle at 35% 30%, #ff4d6d 0%, #c9184a 55%, #590d22 100%) !important;
  border: 1.5px solid #ff758f !important;
  box-shadow: 0 0 10px rgba(255, 0, 60, 0.7) !important;
}
#zayro-vip-overlay .ball-circle-green {
  background: radial-gradient(circle at 35% 30%, #52b788 0%, #2d6a4f 55%, #081c15 100%) !important;
  border: 1.5px solid #74c69d !important;
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.7) !important;
}
#zayro-vip-overlay .ball-circle-violet {
  background: radial-gradient(circle at 35% 30%, #b5179e 0%, #7209b7 55%, #3a0ca3 100%) !important;
  border: 1.5px solid #c77dff !important;
  box-shadow: 0 0 10px rgba(181, 23, 158, 0.7) !important;
}

#zayro-vip-overlay .res-num-text {
  position: relative !important;
  z-index: 2 !important;
  font-size: 20px !important;
  font-weight: 900 !important;
  color: #ffffff !important;
  text-shadow: 0 0 6px rgba(0, 0, 0, 0.85) !important;
}

#zayro-vip-overlay .res-color-pill {
  margin-top: 3px !important;
  font-size: 5.5px !important;
  font-weight: 900 !important;
  letter-spacing: 0.03em !important;
  color: #ffd000 !important;
  background: rgba(255, 208, 0, 0.15) !important;
  border: 1px solid rgba(255, 208, 0, 0.45) !important;
  border-radius: 20px !important;
  padding: 1px 5px !important;
  text-transform: uppercase !important;
  white-space: nowrap !important;
}

#zayro-vip-overlay .api-id-horizon {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 4px !important;
  width: 100% !important;
  font-family: monospace, sans-serif !important;
  font-size: 7px !important;
  font-weight: 800 !important;
  color: #ffffff !important;
  margin-top: 2px !important;
}

#zayro-vip-overlay .horizon-line {
  flex: 1 !important;
  height: 1px !important;
  background: linear-gradient(90deg, transparent, rgba(255, 0, 60, 0.5), transparent) !important;
}
#zayro-vip-overlay .horizon-acc {
  color: #00ff88 !important;
  font-weight: 900 !important;
  text-shadow: 0 0 4px rgba(0, 255, 136, 0.6) !important;
}
"""


class OverlayManager:
    """
    Manages the floating VIP hack overlay injected directly into the live game page during Playwright runs.
    Ensures that when a win occurs, the Congratulations popup has this floating card on top in the screenshot.
    """

    @staticmethod
    def get_ball_info(number: Optional[int], choice: str) -> dict:
        """Returns ball styling, color name, and number"""
        if number is None:
            num = 7 if choice.upper() == "BIG" else 2
        else:
            num = int(number)

        if num in (1, 3, 7, 9):
            color = "GREEN"
            cls = "ball-circle-green"
        elif num in (2, 4, 6, 8):
            color = "RED"
            cls = "ball-circle-red"
        elif num == 0:
            color = "RED+VIOLET"
            cls = "ball-circle-violet"
        else: # 5
            color = "GREEN+VIOLET"
            cls = "ball-circle-violet"

        return {"number": num, "color": color, "class": cls}

    @classmethod
    def generate_html(
        cls,
        issue: str,
        choice: str,
        confidence: float = 98.7,
        level: int = 1,
        number: Optional[int] = None
    ) -> str:
        """
        Generates the standalone HTML markup for the Zayro VIP Hack Card.
        If a custom HTML template is uploaded by the admin, it uses/adapts it.
        """
        # Check if custom template exists in db or filesystem
        custom_tpl = db_manager.get_custom_html_template()
        # If it's a full simulator webpage like zayro.html (contains iframe or doctype),
        # we do NOT inject an iframe/black body into the live game page, we use the pure isolated Zayro card instead.
        if custom_tpl and len(custom_tpl.strip()) > 50:
            if "<iframe" not in custom_tpl and "<!DOCTYPE" not in custom_tpl and "target-game-frame" not in custom_tpl:
                rendered = custom_tpl
                rendered = rendered.replace("{issue}", str(issue))
                rendered = rendered.replace("{choice}", choice.upper())
                rendered = rendered.replace("{confidence}", f"{float(confidence):.1f}")
                rendered = rendered.replace("{level}", str(level))
                rendered = rendered.replace("{number}", str(number if number is not None else (7 if choice.upper() == "BIG" else 2)))
                return rendered

        choice_clean = choice.strip().upper()
        outcome_class = "big" if choice_clean == "BIG" else "small"
        ball = cls.get_ball_info(number, choice_clean)
        short_issue = str(issue)[-5:] if len(str(issue)) > 5 else str(issue)
        conf_str = f"{float(confidence):.1f}%" if float(confidence) > 0 else "98.8%"

        html = f"""
        <div class="card-outer">
          <!-- SINGLE GOLD LASER RUNNING STROKE -->
          <svg class="card-stroke" viewBox="0 0 240 180" preserveAspectRatio="none">
            <rect x="1" y="1" width="238" height="178" pathLength="100" rx="16"/>
          </svg>

          <!-- TOP DOCKED PILL BADGE -->
          <div class="card-title-line1">BdgWin VIP Hack</div>

          <!-- 4 CORNER NOTCH BRACKETS -->
          <div class="card-bracket b-tl"></div>
          <div class="card-bracket b-tr"></div>
          <div class="card-bracket b-bl"></div>
          <div class="card-bracket b-br"></div>

          <div class="card-inner">
            <!-- STATUS STRIP -->
            <div class="mode-strip">
              <div class="strip-item"><span>SYS : </span><span class="strip-val">SECURE PRO</span></div>
              <div class="strip-item"><span>MOD : </span><span class="strip-mode">ACTIVE</span></div>
              <div class="strip-item"><span>PING : </span><span class="strip-ping">21MS</span></div>
            </div>

            <!-- INNER SCREEN VIEWPORT -->
            <div class="card-screen">
              <div class="screen-cyber-matrix">
                <svg class="circuit-svg" viewBox="0 0 240 120" preserveAspectRatio="none">
                  <path d="M 0 20 L 35 20 L 48 35 L 95 35 M 145 35 L 192 35 L 205 20 L 240 20" stroke="#ff003c" stroke-width="0.8" fill="none"/>
                  <path d="M 0 100 L 40 100 L 52 85 L 90 85 M 150 85 L 188 85 L 200 100 L 240 100" stroke="#ff003c" stroke-width="0.8" fill="none"/>
                  <circle cx="48" cy="35" r="1.5" fill="#ffd000"/>
                  <circle cx="192" cy="35" r="1.5" fill="#ffd000"/>
                </svg>
                <div class="telemetry-hud-tag tele-tl">&#9733; 0x9K-AI</div>
                <div class="telemetry-hud-tag tele-tr">SYNC: 99.8% &#9733;</div>
                <div class="telemetry-hud-tag tele-bl">&#9889; MATRIX: ON</div>
                <div class="telemetry-hud-tag tele-br">5.8GHz &#9889;</div>
                <div class="laser-sweep-line"></div>
              </div>

              <!-- PREDICTION RESULT COCKPIT -->
              <div id="sv-result">
                <div class="pred-showcase-row">
                  <!-- Left: 3D Outcome Ingot -->
                  <div class="res-outcome-ingot {outcome_class}" id="resBsBadge">
                    <div class="ingot-top-tag">&#9733; AI VERDICT &#9733;</div>
                    <div class="ingot-main-text" id="resBsText">{choice_clean}</div>
                    <div class="ingot-conf-pill">
                      <span class="conf-dot"></span>
                      <span id="resConfText">CONF: {conf_str}</span>
                    </div>
                  </div>

                  <!-- Right: 3D Casino Chip Pedestal -->
                  <div class="res-chip-pedestal">
                    <div class="res-ball {ball['class']}" id="resBall">
                      <span class="res-num-text" id="resNumText">{ball['number']}</span>
                    </div>
                    <div class="res-color-pill" id="resColorPill">COLOR: {ball['color']}</div>
                  </div>
                </div>

                <!-- Precision Laser Horizon -->
                <div class="api-id-horizon">
                  <span class="horizon-line"></span>
                  <span id="res-period-bottom">API ID : {short_issue}</span>
                  <span class="horizon-acc">SAFE LEVEL {level}</span>
                  <span class="horizon-line"></span>
                </div>
              </div>
            </div>
          </div>
        </div>
        """
        return html


overlay_manager = OverlayManager()

def _label(value: int, labels: list[str]) -> str:
    idx = max(0, min(int(value), len(labels) - 1))
    return labels[idx]


def _tip(en: str, kn: str) -> dict[str, str]:
    return {"en": en, "kn": kn}


def generate_recommendations(
    decision: str,
    waste: int,
    delay: int,
    density: int,
    area: int,
) -> list[dict[str, str]]:
    waste_label = _label(waste, ["low", "medium", "high"])
    density_label = _label(density, ["low", "medium", "high"])
    area_label = "residential" if int(area) == 0 else "commercial"
    delay_days = max(0, int(delay))

    tips: list[dict[str, str]] = []

    if decision == "DISPOSE":
        tips.append(
            _tip(
                "Dispose waste at the nearest listed disposal site as soon as possible.",
                "ಸಾಧ್ಯವಾದಷ್ಟು ಬೇಗ ಸಮೀಪದ ವಿಸರ್ಜನಾ ಕೇಂದ್ರದಲ್ಲಿ ತ್ಯಾಜ್ಯವನ್ನು ವಿಲೇವಾರಿ ಮಾಡಿ.",
            )
        )
        if delay_days >= 3:
            tips.append(
                _tip(
                    "Escalate collection priority because pickup delay is already high.",
                    "ಸಂಗ್ರಹಣೆಯಲ್ಲಿ ಈಗಾಗಲೇ ಹೆಚ್ಚು ವಿಳಂಬವಾಗಿರುವುದರಿಂದ ಪ್ರಾಥಮ್ಯವನ್ನು ಹೆಚ್ಚಿಸಿ.",
                )
            )
        if waste_label == "high":
            tips.append(
                _tip(
                    "Segregate wet, dry, and hazardous waste before transport to reduce contamination.",
                    "ಮಾಲಿನ್ಯ ಕಡಿಮೆ ಮಾಡಲು ಸಾಗಣೆಗೆ ಮೊದಲು ಒದ್ದೆ, ಒಣ ಮತ್ತು ಅಪಾಯಕಾರಿ ತ್ಯಾಜ್ಯವನ್ನು ಪ್ರತ್ಯೇಕಿಸಿ.",
                )
            )
        tips.append(
            _tip(
                "Use sealed containers during transport to prevent spillage and odor spread.",
                "ಚಿಮ್ಮಿಕೆ ಮತ್ತು ದುರ್ವಾಸನೆ ಹರಡುವುದನ್ನು ತಡೆಯಲು ಸಾಗಣೆಯಲ್ಲಿ ಮುಚ್ಚಿದ ಪಾತ್ರೆಗಳನ್ನು ಬಳಸಿ.",
            )
        )
    elif decision == "MONITOR":
        tips.append(
            _tip(
                "Monitor the area for the next 24-48 hours before triggering full collection.",
                "ಪೂರ್ಣ ಸಂಗ್ರಹಣೆಯನ್ನು ಆರಂಭಿಸುವ ಮೊದಲು ಮುಂದಿನ 24-48 ಗಂಟೆಗಳ ಕಾಲ ಪ್ರದೇಶವನ್ನು ನಿಗಾ ವಹಿಸಿ.",
            )
        )
        if waste_label in {"medium", "high"}:
            tips.append(
                _tip(
                    "Increase inspection frequency until waste level drops to low.",
                    "ತ್ಯಾಜ್ಯ ಮಟ್ಟ ಕಡಿಮೆಯಾಗುವವರೆಗೆ ಪರಿಶೀಲನೆಗಳ ಅವಧಿಯನ್ನು ಹೆಚ್ಚಿಸಿ.",
                )
            )
        if delay_days >= 2:
            tips.append(
                _tip(
                    "Prepare a backup pickup slot in case delay increases further.",
                    "ವಿಳಂಬ ಇನ್ನಷ್ಟು ಹೆಚ್ಚಾದರೆ ಬಳಸಲು ಬ್ಯಾಕಪ್ ಸಂಗ್ರಹಣಾ ವೇಳೆಯನ್ನು ಸಿದ್ಧಪಡಿಸಿ.",
                )
            )
        tips.append(
            _tip(
                "Promote source segregation at collection points to keep monitoring data reliable.",
                "ನಿಗಾ ಮಾಹಿತಿಯ ವಿಶ್ವಾಸಾರ್ಹತೆಗೆ ಸಂಗ್ರಹಣಾ ಕೇಂದ್ರಗಳಲ್ಲಿ ಮೂಲದಲ್ಲೇ ತ್ಯಾಜ್ಯ ವಿಂಗಡಣೆಯನ್ನು ಉತ್ತೇಜಿಸಿ.",
            )
        )
    else:
        tips.append(
            _tip(
                "No immediate disposal action is needed; continue routine observation.",
                "ತಕ್ಷಣದ ವಿಸರ್ಜನೆ ಅಗತ್ಯವಿಲ್ಲ; ನಿಯಮಿತ ನಿಗಾವನ್ನು ಮುಂದುವರಿಸಿ.",
            )
        )
        if waste_label == "low" and delay_days == 0:
            tips.append(
                _tip(
                    "Keep current collection schedule and focus on prevention measures.",
                    "ಪ್ರಸ್ತುತ ಸಂಗ್ರಹಣಾ ವೇಳಾಪಟ್ಟಿಯನ್ನು ಮುಂದುವರಿಸಿ ಮತ್ತು ತಡೆ ಕ್ರಮಗಳಿಗೆ ಒತ್ತು ನೀಡಿ.",
                )
            )
        tips.append(
            _tip(
                "Record daily waste trends so early warning thresholds can be detected quickly.",
                "ಮುಂಚಿತ ಎಚ್ಚರಿಕೆ ಮಟ್ಟಗಳನ್ನು ಬೇಗ ಪತ್ತೆಹಚ್ಚಲು ದೈನಂದಿನ ತ್ಯಾಜ್ಯ ಪ್ರವೃತ್ತಿಗಳನ್ನು ದಾಖಲಿಸಿ.",
            )
        )

    if density_label == "high":
        tips.append(
            _tip(
                "Deploy additional covered bins in dense zones to avoid overflow between pickups.",
                "ಸಂಗ್ರಹಣೆಗಳ ಮಧ್ಯೆ ತುಂಬಿ ಹರಿಯದಂತೆ ಹೆಚ್ಚಿನ ಸಾಂದ್ರತೆಯ ಪ್ರದೇಶಗಳಲ್ಲಿ ಹೆಚ್ಚುವರಿ ಮುಚ್ಚಿದ ಕಸದ ಬುಟ್ಟಿಗಳನ್ನು ಇಡಿ.",
            )
        )
    if area_label == "commercial":
        tips.append(
            _tip(
                "Coordinate with nearby businesses for off-peak waste handover windows.",
                "ಅತ್ಯಧಿಕ ಸಮಯದ ಹೊರತಾಗಿ ತ್ಯಾಜ್ಯ ಹಸ್ತಾಂತರ ವೇಳೆಗೆ ಸಮೀಪದ ವ್ಯವಹಾರ ಸಂಸ್ಥೆಗಳೊಂದಿಗೆ ಸಮನ್ವಯಗೊಳಿಸಿ.",
            )
        )
    else:
        tips.append(
            _tip(
                "Run local awareness reminders on household segregation and pickup timing.",
                "ಮನೆಮಟ್ಟದ ತ್ಯಾಜ್ಯ ವಿಂಗಡಣೆ ಮತ್ತು ಸಂಗ್ರಹಣಾ ಸಮಯದ ಬಗ್ಗೆ ಸ್ಥಳೀಯ ಜಾಗೃತಿ ನೆನಪುಗಳನ್ನು ನಡೆಸಿ.",
            )
        )

    # Deduplicate while preserving order in case future rules overlap.
    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for tip in tips:
        key = tip["en"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(tip)
    return deduped

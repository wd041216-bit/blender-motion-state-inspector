import json
from typing import Dict

def format_json(report: Dict) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2)

def format_markdown(report: Dict) -> str:
    lines = []
    lines.append("## Scene Report")
    lines.append("")
    for actor in report.get("actors", []):
        lines.append(f"### {actor['name']}")
        morph = actor.get("morphology", {})
        parts = []
        if morph.get("height"):
            parts.append(f"身高 {morph['height']}m")
        if parts:
            lines.append(f"**形态：** {', '.join(parts)}")
        lines.append(f"**姿态：** {actor.get('pose_state', '未知')}")
        anoms = actor.get("anomalies", [])
        if anoms:
            lines.append(f"**异常：** {', '.join(a.get('message', str(a)) for a in anoms)}")
        else:
            lines.append("**异常：** 无")
        lines.append("")
    spatial = report.get("spatial", {})
    if spatial:
        lines.append("### 空间关系")
        gc = spatial.get("ground_contact", [])
        if gc:
            lines.append(f"- 地面接触: {', '.join(gc)}")
        else:
            lines.append("- 地面接触: 无")
    return "\n".join(lines)

import json
from typing import Dict

def format_json(report: Dict) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2)

def format_markdown(report: Dict) -> str:
    lines = []
    if "frame_reports" in report:
        lines.append("## Animation State Report")
        lines.append("")
        lines.append(f"**摘要：** {report.get('summary', '')}")
        lines.append("")
        events = report.get("event_diagnostics", [])
        lines.append("### 事件诊断")
        if events:
            for event in events:
                lines.append(f"- {event['actor']} {event['type']}: frames {event['start']}-{event['end']} ({event['count']} samples)")
        else:
            lines.append("- 无连续异常事件")
        lines.append("")
        lines.append("### 采样帧")
        for frame in report.get("frame_reports", [])[:12]:
            lines.append(f"- Frame {frame.get('frame_info', {}).get('current')}: {frame.get('summary', '')}")
        return "\n".join(lines)

    lines.append("## Scene Report")
    lines.append("")
    for actor in report.get("actors", []):
        lines.append(f"### {actor['name']}")
        cls = actor.get("classification", {})
        if cls:
            lines.append(f"**类型：** {cls.get('class', 'unknown')} ({cls.get('confidence', 0):.2f})")
        morph = actor.get("morphology", {})
        parts = []
        if morph.get("height"):
            parts.append(f"身高 {morph['height']}m")
        if morph.get("shoulder_width"):
            parts.append(f"宽度 {morph['shoulder_width']}m")
        if parts:
            lines.append(f"**形态：** {', '.join(parts)}")
        lines.append(f"**姿态：** {actor.get('pose_state', '未知')}")
        facing = actor.get("facing", {})
        if facing.get("vector"):
            lines.append(f"**朝向：** {facing['vector']} ({facing.get('source')}, confidence={facing.get('confidence')})")
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

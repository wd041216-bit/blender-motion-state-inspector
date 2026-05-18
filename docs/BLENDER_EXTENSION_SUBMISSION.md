# Blender Extension Submission

This document tracks the review package for submitting Motion State Inspector to the Blender Extensions platform.

## Extension Package

- Package: `motion_state_inspector-0.1.0.zip`
- Release: https://github.com/wd041216-bit/blender-motion-state-inspector/releases/tag/v0.1.0
- Download: https://github.com/wd041216-bit/blender-motion-state-inspector/releases/download/v0.1.0/motion_state_inspector-0.1.0.zip
- SHA256: `04261e8698fa0db317f3d0e075413032727aaf7682508758f44c1c73b61c25ff`

## Local Validation

```bash
blender --command extension validate addon --valid-tags=""
blender --command extension build --source-dir addon --output-dir dist --valid-tags=""
blender --command extension validate dist/motion_state_inspector-0.1.0.zip --valid-tags=""
```

All three commands passed locally with Blender 5.1.1.

## Suggested Listing

Name:

```text
Motion State Inspector
```

Tagline:

```text
Export LLM-readable model, skeleton, and motion state reports
```

Description:

```text
Motion State Inspector converts Blender scenes, avatars, armatures, and animation frames into structured JSON reports for agentic 3D workflows.

It helps tools and reviewers understand character vs scene prop classification, Mixamo-style skeleton semantics, morphology, facing vectors, ground clearance, contacts, and sampled motion diagnostics without relying only on screenshots.

The extension does not generate or modify animation. It collects scene state and exports facts for downstream QA, retargeting, automation, and LLM-based inspection.
```

Category tags:

```text
Animation
Import-Export
```

Website/source:

```text
https://github.com/wd041216-bit/blender-motion-state-inspector
```

License:

```text
MIT
```

Permissions:

```text
files: Write raw scene state JSON reports to disk
network: Expose an optional local TCP inspection server
```

## Review Notes

- The local TCP server binds to `127.0.0.1` only.
- Network access is optional and used for local agent-triggered inspection.
- The add-on can be used entirely offline through the N-panel or headless script.
- The Python analyzer CLI is part of the repository workflow; the Blender extension package focuses on in-Blender state collection.

## Current Submission Status

Blocked on Blender ID / Cloudflare human verification at:

```text
https://extensions.blender.org/submit/
```

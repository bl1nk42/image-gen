# Video Blueprint

Each clip must include:

```yaml
id: clip-01
purpose: establish|develop|climax|resolve|transition
scene: environment
action: subject + trajectory
transition_description: 2-4 sentences including appearance, movement, state change, and what remains present
seconds: 3-10
camera: static|pan|tilt|dolly|zoom|crane|arc|handheld
ratio: 16:9|9:16
first_keyframe: path or generated asset
continuity: continuous|scene_cut
narration_budget: seconds or 0
narration_cue: text|continues|null
bgm_cue: mood, arrangement, density, brightness
job_id: provider job id
```

Dependent clips are sequential. Independent clips can be queued. Keep a manifest beside outputs.

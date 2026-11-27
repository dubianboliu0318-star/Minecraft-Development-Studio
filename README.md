# Minecraft Development Studio (MDS)

Minecraft development workspace.

## Projects
- mods: Minecraft mods
- datapacks: Minecraft datapacks
- resource-packs: Resource packs
- models: 3D models
- textures: Textures
- ui: User interfaces
- animations: Animation assets

## Shared
- templates: Reusable templates
- tools: Development tools

## Documentation
- specifications: Project specifications
- reports: QA and development reports

## Tests
- tests: Automated tests

## Commands

Run all automated checks and show project status:
`python shared/tools/mds.py doctor`

Show the next development stage:
`python shared/tools/mds.py workflow --slug <project-slug>`

Generate a project QA report:
`python shared/tools/mds.py qa --slug <project-slug>`

Framework QA does not mark Minecraft build or in-game verification complete.

Package a validated datapack:
`python shared/tools/package_datapack.py --slug <project-slug>`

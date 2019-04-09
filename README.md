# terraecs

Terraecs is a simple cli tool to run a once-off ECS/Fargate task that relies on a terraformed infrastructure.

## Motivation

* I need to run a task (be it ror-rake, laravel-artisan, etc.) in a Fargate service environment
* I use terraform for IaC, and I do not want to create rogue/unmaintainable resources via 3rd party (like how serverless-framework does it)
* I do not want to change my IaC for every different task, but rather have a single task-definition and just run commands ad-hoc
* These once-off tasks are dirty, I just want to have direct feedback on how it went (logs + exit status)

## Usage

```bash
$ terraform output -module=custom_ecs_task -json > output.json
$ terraecs -f output.json run "command" "arg1" "arg2"
```

# terraecs

[![Build Status](https://travis-ci.org/lifeofguenter/terraecs.svg?branch=master)](https://travis-ci.org/lifeofguenter/terraecs)
[![PyPI](https://img.shields.io/pypi/v/terraecs.svg)](https://pypi.org/project/terraecs/)
[![License](https://img.shields.io/github/license/lifeofguenter/terraecs.svg)](LICENSE)

Terraecs is a simple cli tool to run a once-off [ECS/Fargate](https://aws.amazon.com/fargate/) task that relies on a [terraformed](https://www.terraform.io/) infrastructure.

_Preview release, please do not use for anything important!_

## Motivation

* I want to run a command (be it ror-rake, laravel-artisan, etc.) in a Fargate environment
* I use terraform for IaC, and do not want to deviate from that
* I also do not want to think about infrastructure when running a command, as it should be already setup via terraform
* These once-off tasks are dirty, I want to have direct feedback on how it went (logs + exit status)

## Installation

```bash
$ pip install terraecs
```

## Usage

You will need to create a Fargate task module to create a task-definition and any other supporting resources (networking/cloudwatchlogs). At a minimum the module will have to output the following:

```hcl
output "cluster_id" {
  value = "${var.cluster_id}"
}

output "subnets" {
  value = "${var.subnets}"
}

output "security_group_id" {
  value = "${aws_security_group.main.id}"
}

output "task_definition_arn" {
  value = "${aws_ecs_task_definition.main.arn}"
}
```

Terraform 0.12 and later intentionally track only root module outputs in the state. To expose module outputs for external consumption, you must export them from the root module using an output block, which as of 0.12 can now be done for a single module all in one output:

```hcl
output "custom_ecs_task" {
  value = module.custom_ecs_task
}
```

Once you have applied your terraform config, pull the output into a json:

```bash
$ terraform output -json custom_ecs_task > output.json
```

Now you can use `terraecs` to run any command based off the above task-definition:

```bash
$ terraecs -f output.json run "command" "arg1" "arg2"
```

## Output

The output can look something like this:

```bash
❯ AWS_PROFILE=staging terraecs -f output.json run artisan --help
2019-04-10 08:14:01,884 botocore.credentials [INFO] Found credentials in shared credentials file: ~/.aws/credentials
2019-04-10 08:14:03,893 root [INFO] launched task: arn:aws:ecs:eu-west-1:1111111111111:task/staging-main/4544cfd6f10e4ff0b16458666362cbd9
2019-04-10 08:14:04,069 root [INFO] PROVISIONING
2019-04-10 08:14:25,461 root [INFO] PENDING
2019-04-10 08:15:51,642 root [INFO] DEPROVISIONING
2019-04-10 08:16:13,632 root [INFO] STOPPED
Description:
  Lists commands
Usage:
  list [options] [--] [<namespace>]
Arguments:
  namespace            The namespace name
Options:
      --raw            To output raw command list
      --format=FORMAT  The output format (txt, xml, json, or md) [default: "txt"]
Help:
  The list command lists all commands:

    php artisan list

  You can also display the commands for a specific namespace:

    php artisan list test

  You can also output the information in other formats by using the --format option:

    php artisan list --format=xml

  It's also possible to get raw list of commands (useful for embedding command runner):

    php artisan list --raw
```

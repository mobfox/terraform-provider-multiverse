Terraform Provider Multiverse
==================

This provider is similar to [Custom Resources in AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources.html).
You can write a script that will be used to create, update or destroy external resources that are not supported by Terraform.

You can use this provider instead of writing your own Terraform Custom Provider in golang, just write your logic in any language you prefer (python, node, java) and
use it with this provider.

Maintainers
-----------

This provider plugin is maintained by the MobFox DevOps team at [MobFox](https://www.mobfox.com/).

Requirements
------------

-	[Terraform](https://www.terraform.io/downloads.html) 0.10.x
-	[Go](https://golang.org/doc/install) 1.8 (to build the provider plugin)

Building The Provider
---------------------

Clone repository to: `$GOPATH/src/github.com/mobfox/terraform-provider-multiverse`

```sh
$ mkdir -p $GOPATH/src/github.com/mobfox; cd $GOPATH/src/github.com/mobfox
$ git clone git@github.com:mobfox/terraform-provider-multiverse.git
```

Enter the provider directory and build the provider

```sh
$ cd $GOPATH/src/github.com/mobfox/terraform-provider-multiverse
$ make build
```

Using the provider
----------------------

Check the examples
Here an example of Spotinst Multai Load Balancer TargetSet

```hcl
provider "multiverse" {}

resource "multiverse_custom_resource" "spotinst_targetset_and_rules" {
  executor = "python3"
  script = "spotinst_mlb_targetset.py"
  id_key = "id"
  data = <<JSON
{
  "name": "test-terraform-test",
  "mlb_id": "lb-123",
  "mlb_deployment_id": "dp-123",
  "mlb_listener_ids": ["ls-123", "ls-456"],
  "test_group_callback_fqdn": "test.fqdn.com",
  "control_group_callback_fqdn": "control.fqdn.com"
}
JSON
}
```

- When you run `terraform apply` the resource will be created / updated
- When you run `terraform destroy` the resource will be destroyed

#### Attributes

##### Input

* `executor (string)` could be anything like python, bash, sh, node, java, awscli ... etc
* `script (string)` the path to your script or program to run, the script must exit with code 0 and return a valid json
* `id_key (string)` the key of returned result to be used as id
* `data (string)` must be a valid json payload

##### Output
* `resource (map[string])` the output of your script must be a valid json with all keys of type *string* in the form `{"key":"value"}`


#### Referencing in TF template

This an example how to reference the resource and access its attributes

Let's say your script returned the following result
 
```json
{
  "id": "my-123",
  "name": "my-resource",
  "capacity": "20g"
}
```

then the resource in TF will have these attributes

```hcl
id = "my-123"
resource = {
  name = "my-resource"
  capacity = "20g"
  id = "my-123"
}
```

you can access these attributes using variables

```
${multiverse_custom_resource.my_custom_resource.id} # accessing id
${multiverse_custom_resource.my_custom_resource.resource["name"]}
${multiverse_custom_resource.my_custom_resource.resource["capacity"]}
```

#### Why the attribute *data* is stringified JSON?

This will give you flexibility in passing your arguments with mixed types
We couldn't define a with generic mixed types, 
if we used map then all attributes have to be explicitly defined in the schema or all its attributes have the same type


Writing a script
-------------------

Your script must be able to handle the TF event and the JSON payload *data*

* `event` : will have one of these `create, read, delete, update`
* `data` is passed via `stdin`

and your script should look something like this

```python
import sys
import json
...

def handler(event, data):
   data_as_json = json.loads(data)
   if event == "create":
        ...
        
   elif event == "read":
        ...
        
   elif event == "update":
        ...
        
   elif event == "delete":
        ... 
   
def read_data():
    data = ''
    for line in sys.stdin:
        data += line

    return data
   
if __name__ == '__main__':
    context = read_data()
    print(json.dumps(handler(sys.argv[1], context)))
```

To test your script before using in TF

```bash
echo "{\"key\":\"value\"}" | python3 my_resource.py create
```



Developing the Provider
---------------------------

If you wish to work on the provider, you'll first need [Go](http://www.golang.org) installed on your machine (version 1.8+ is *required*). You'll also need to correctly setup a [GOPATH](http://golang.org/doc/code.html#GOPATH), as well as adding `$GOPATH/bin` to your `$PATH`.

To compile the provider, run `make build`. This will build the provider and put the provider binary in the `$GOPATH/bin` directory.

```sh
$ make bin
...
$ $GOPATH/bin/terraform-provider-multiverse
...
```

In order to test the provider, you can simply run `make test`.

```sh
$ make test
```

Feel free to contribute!

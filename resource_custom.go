package main

import (
    "github.com/hashicorp/terraform/helper/schema"
    "log"
    "os/exec"
    "encoding/json"
)

func resourceCustom() *schema.Resource {
    return &schema.Resource{
        Create: onCreate,
        Read:   onRead,
        Update: onUpdate,
        Delete: onDelete,

        Importer: &schema.ResourceImporter{
            State: schema.ImportStatePassthrough,
        },

        SchemaVersion: 1,

        Schema: map[string]*schema.Schema{
            "executor": &schema.Schema{
                Type: schema.TypeString,
                Required: true,
            },

            "script": &schema.Schema{
                Type: schema.TypeString,
                Required: true,
            },

            "data": &schema.Schema{
                Type: schema.TypeString,
                Required: true,
            },

            "id_key": &schema.Schema{
                Type: schema.TypeString,
                Required: true,
            },

            "resource": &schema.Schema{
                Type: schema.TypeString,
                Computed: true,
            },
        },
    }
}

func onCreate(d *schema.ResourceData, m interface{}) error {
    return do("create", d, m)
}

func onRead(d *schema.ResourceData, m interface{}) error {
    return do("read", d, m)
}

func onUpdate(d *schema.ResourceData, m interface{}) error {
    return do("update", d, m)
}

func onDelete(d *schema.ResourceData, m interface{}) error {
    return do("delete", d, m)
}

func do(action string, d *schema.ResourceData, m interface{}) error {
    log.Printf("Executing: %s %s %s %s", d.Get("executor"), d.Get("script"), action, d.Get("data"))
    result, err := exec.Command(
        d.Get("executor").(string),
        d.Get("script").(string),
        "create",
        d.Get("data").(string)).Output()

    if err == nil {
        var resource map[string]interface{}
        err = json.Unmarshal([]byte(result), &resource)
        if err == nil {
            key := d.Get("id_key").(string)
            d.Set("resource", string(result))
            d.SetId(resource[key].(string))
        }
    }

    return err
}
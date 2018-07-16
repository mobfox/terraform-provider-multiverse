package main

import (
        "github.com/hashicorp/terraform/helper/schema"
)

func resourceCustom() *schema.Resource {
        return &schema.Resource{
                Create: onCreate,
                Read:   onRead,
                Update: onUpdate,
                Delete: onDelete,

                Schema: map[string]*schema.Schema{
                        "data": &schema.Schema{
                                Type:     schema.TypeString,
                                Required: true,
                        },
                },
        }
}

func onCreate(d *schema.ResourceData, m interface{}) error {
        return nil
}

func onRead(d *schema.ResourceData, m interface{}) error {
        return nil
}

func onUpdate(d *schema.ResourceData, m interface{}) error {
        return nil
}

func onDelete(d *schema.ResourceData, m interface{}) error {
        return nil
}

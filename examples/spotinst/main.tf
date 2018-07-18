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

output "resources" {
  value = "${multiverse_custom_resource.spotinst_targetset_and_rules.id}"
}

output "test_targetset_id" {
  value = "${multiverse_custom_resource.spotinst_targetset_and_rules["testTargetSet"]}"
}

output "control_targetset_id" {
  value = "${multiverse_custom_resource.spotinst_targetset_and_rules["controlTargetSet"]}"
}
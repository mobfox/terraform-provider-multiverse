provider "multiverse" {}

resource "multiverse_custom_resource" "spotinst_targetset_and_rules" {
  executor = "python3"
  script = "spotinst_mlb_targetset.py"
  id_key = "id"
  data = {
    name = "test-terraform-test"
    mlb_id = "lb-123"
    mlb_deployment_id = "dp-123"
    mlb_listener_ids = [
      "ls-123",
      "ls-123"]
    test_group_callback_fqdn = "a.FQDN.com"
    control_group_callback_fqdn = "b.FQDN.com"
  }
}

output "resources" {
  value = "${multiverse_custom_resource.spotinst_targetset_and_rules.id}"
}
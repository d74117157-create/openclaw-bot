# OpenClaw Oracle Cloud Infrastructure Terraform
# Usage: terraform init && terraform apply

variable "tenancy_ocid" {}
variable "user_ocid" {}
variable "fingerprint" {}
variable "private_key_path" {}
variable "region" { default = "us-ashburn-1" }
variable "compartment_ocid" {}
variable "ssh_public_key" {}

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# VCN
resource "oci_core_vcn" "openclaw_vcn" {
  cidr_block     = "10.0.0.0/16"
  compartment_id = var.compartment_ocid
  display_name   = "openclaw-vcn"
  dns_label      = "openclaw"
}

# Internet Gateway
resource "oci_core_internet_gateway" "openclaw_igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.openclaw_vcn.id
  display_name   = "openclaw-internet-gateway"
}

# Route Table
resource "oci_core_route_table" "openclaw_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.openclaw_vcn.id
  display_name   = "openclaw-route-table"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.openclaw_igw.id
  }
}

# Security List
resource "oci_core_security_list" "openclaw_sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.openclaw_vcn.id
  display_name   = "openclaw-security-list"

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 22
      max = 22
    }
  }

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 8080
      max = 8080
    }
  }

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 3000
      max = 3000
    }
  }

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

# Subnet
resource "oci_core_subnet" "openclaw_subnet" {
  cidr_block        = "10.0.1.0/24"
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.openclaw_vcn.id
  display_name      = "openclaw-subnet"
  dns_label         = "openclaw"
  route_table_id    = oci_core_route_table.openclaw_rt.id
  security_list_ids = [oci_core_security_list.openclaw_sl.id]
}

# VM Instance
resource "oci_core_instance" "openclaw_vm" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.compartment_ocid
  display_name        = "openclaw-bot-vm"
  shape               = "VM.Standard.A1.Flex"

  shape_config {
    ocpus         = 2
    memory_in_gbs = 12
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.ubuntu.images[0].id
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.openclaw_subnet.id
    display_name     = "openclaw-vnic"
    assign_public_ip = true
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
  }
}

# Data sources
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}

data "oci_core_images" "ubuntu" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = "VM.Standard.A1.Flex"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

# Outputs
output "instance_public_ip" {
  value = oci_core_instance.openclaw_vm.public_ip
}

output "instance_id" {
  value = oci_core_instance.openclaw_vm.id
}
